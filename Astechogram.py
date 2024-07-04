"""
Astechogram - Real-Time Speech-to-Text and Text-to-Speech for Asterisk
Copyright (c) 2024 Michaël Benarouch (benasterisk@gmail.com)
GitHub Repository: https://github.com/yourusername/astechogram

This script is licensed under the MIT License.
See the LICENSE file for full license text.

This script uses the following third-party libraries:
- requests: For making HTTP requests to the Deepgram API (https://pypi.org/project/requests/)
- numpy: For numerical operations on audio data (https://pypi.org/project/numpy/)
- python-dotenv: For loading environment variables from a .env file (https://pypi.org/project/python-dotenv/)
- audiosocket: A custom library for handling audio sockets, sourced from https://github.com/silentindark/audiosocket_server

Ensure you have installed all the required libraries and have the necessary environment variables set.
"""


import os
import time
import threading
import queue
import uuid
import struct
import requests
import numpy as np
from dotenv import load_dotenv
from audiosocket import Audiosocket

# Load environment variables
load_dotenv()

# API Keys and URLs
DEEPGRAM_API_KEY = os.getenv("DG_API_KEY")
SPEECH_TO_TEXT_URL = "https://api.deepgram.com/v1/listen"
TTS_API_URL = "https://api.deepgram.com/v1/speak?model=aura-asteria-en&encoding=linear16&sample_rate=8000&channels=1"

# Audio settings
SAMPLE_RATE = 8000  # Sample rate in Hz
CHANNELS = 1  # Number of audio channels
VOLUME_THRESHOLD = 30  # Volume threshold for detecting speech
MIN_SPEECH_DURATION = 0.5  # Minimum duration of speech in seconds (500ms)
SILENCE_DURATION = 1.5  # Duration of silence to end capture
BUFFER_SIZE = 320  # Buffer size in bytes (20ms of audio at 16-bit 8000Hz mono)

# Create a TCP socket to send and receive audio data
audiosocket = Audiosocket(("0.0.0.0", 9093))

# Queue for audio data
audio_queue = queue.Queue()

def calculate_volume(audio_chunk):
    audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
    volume = np.abs(audio_data).mean()
    return volume

def speech_to_text(audio_data):
    headers = {
        'Authorization': f'Token {DEEPGRAM_API_KEY}',
        'Content-Type': 'application/octet-stream'
    }
    params = {
        'encoding': 'linear16',
        'sample_rate': SAMPLE_RATE,
        'channels': CHANNELS
    }
    response = requests.post(SPEECH_TO_TEXT_URL, headers=headers, params=params, data=audio_data)
    if response.status_code == 200:
        return response.json()['results']['channels'][0]['alternatives'][0]['transcript']
    else:
        print(f"Failed to transcribe audio, status code: {response.status_code}")
        return None

def text_to_speech(text):
    headers = {
        'Authorization': f'Token {DEEPGRAM_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {'text': text}
    print("Sending text data to Deepgram for TTS...")
    response = requests.post(TTS_API_URL, headers=headers, json=payload, stream=True)
    print("Deepgram Text-to-Speech Request Headers:", headers)
    print("Deepgram Text-to-Speech Request Payload:", payload)
    print("Deepgram Text-to-Speech Response Status Code:", response.status_code)
    return response

def stream_audio_to_asterisk(response, connection):
    """Streams audio data to Asterisk via the specified connection."""
    try:
        audio_data = b""
        for chunk in response.iter_content(chunk_size=BUFFER_SIZE):
            if chunk:
                audio_data += chunk

        for i in range(0, len(audio_data), BUFFER_SIZE):
            connection.write(audio_data[i:i+BUFFER_SIZE])
            time.sleep(BUFFER_SIZE / (SAMPLE_RATE * CHANNELS * 2))  # Calculate appropriate delay for smoother playback

    except Exception as e:
        print(f"Error streaming audio: {e}")
    print("Streaming complete.")

def send_uuid(connection):
    """Send the UUID packet after TCP connection is established."""
    uuid_packet = struct.pack('!B H 16s', 0x01, 16, uuid.uuid4().bytes)
    connection.write(uuid_packet)

def capture_audio(connection):
    while True:
        buffer = b""
        speech_detected = False
        capture_start_time = time.time()
        speech_start_time = None
        silence_start_time = None
        
        while True:
            chunk = connection.read()
            if not chunk:
                print("Caller disconnected.")
                return
            
            buffer += chunk
            volume = calculate_volume(chunk)
            
            if volume > VOLUME_THRESHOLD:
                if not speech_detected:
                    speech_start_time = time.time()
                speech_detected = True
                silence_start_time = None
            elif speech_detected and time.time() - speech_start_time >= MIN_SPEECH_DURATION:
                if silence_start_time is None:
                    silence_start_time = time.time()
                elif time.time() - silence_start_time >= SILENCE_DURATION:
                    break

        if speech_detected and len(buffer) >= SAMPLE_RATE * MIN_SPEECH_DURATION * 2:
            audio_queue.put(buffer)
            print(f"Speech detected, buffer length: {len(buffer)}")
        else:
            print("No valid speech detected, restarting capture loop.")

def process_audio(connection):
    while True:
        speech_buffer = audio_queue.get()
        if speech_buffer:
            print("Processing audio chunk...")
            transcription = speech_to_text(speech_buffer)
            if transcription:
                print("Transcription:", transcription)
                tts_response = text_to_speech(transcription)
                if tts_response.status_code == 200:
                    print("Streaming TTS back to Asterisk...")
                    stream_audio_to_asterisk(tts_response, connection)
                else:
                    print(f"Failed to synthesize TTS, status code: {tts_response.status_code}")
                    print("Error details:", tts_response.text)

def main():
    while True:
        print("Waiting for incoming call...")
        connection = audiosocket.listen()
        if connection:
            print("Call connected.")
            send_uuid(connection)
            
            capture_thread = threading.Thread(target=capture_audio, args=(connection,))
            process_thread = threading.Thread(target=process_audio, args=(connection,))
            
            capture_thread.start()
            process_thread.start()

            capture_thread.join()
            connection.close()
            print("Call ended. Waiting for a new call...")

if __name__ == "__main__":
    main()
