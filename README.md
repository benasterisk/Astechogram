Astechogram: Real-Time Speech-to-Text and Text-to-Speech for Asterisk

Astechogram (astechogram.py) is a Python script that provides a real-time audio processing solution for Asterisk, implementing speech-to-text and text-to-speech functionality using the Deepgram API. It's designed to capture audio from incoming calls, transcribe the speech, and then synthesize and stream the text back as speech.

This script was initially created to test the Asterisk Audiosocket channel/dialplan (AudioSocket - Asterisk Documentation) as a bidirectional TCP socket to manage real-time/stream Speech To Text and Text to Speech features from DeepGram. In this implementation, we are using a single TCP predefined port 9093, with one TCP Socket per call.

Features:

- Real-time audio capture from Asterisk
- Speech detection with volume threshold and silence detection
- Speech-to-text conversion using Deepgram API
- Text-to-speech synthesis using Deepgram API
- Audio streaming back to Asterisk
- Multithreaded design for efficient processing

Prerequisites:

- Python 3.7+
- Asterisk PBX system
- Deepgram API key

Required Libraries:

Astechogram relies on several Python libraries that are not part of the standard Python installation. The main non-standard libraries used include:

- requests: For making HTTP requests to the Deepgram API
- numpy: For numerical operations on audio data
- python-dotenv: For loading environment variables from a .env file
- audiosocket: A custom library for handling audio sockets, sourced from https://github.com/silentindark/audiosocket_server

Installation:

1. Clone this repository:
   git clone https://github.com/yourusername/astechogram.git
   cd astechogram

2. Install the required Python packages:
   pip install requests numpy python-dotenv

3. For the audiosocket library, follow the installation instructions provided in the GitHub repository:
   https://github.com/silentindark/audiosocket_server

4. Set up your Deepgram API key:
   You can set your Deepgram API key as an environment variable by running the following command in your terminal:
   
   export DEEPGRAM_API_KEY='your_deepgram_api_key_here'
   
   Alternatively, you can create a .env file in the project root and add your Deepgram API key:
   
   DG_API_KEY=your_deepgram_api_key_here

   Astechogram will automatically load the API key from the .env file if present.

Asterisk Dialplan Configuration:

To use Astechogram with Asterisk, you need to configure your dialplan. Add the following lines to your Asterisk dialplan (usually in extensions.conf):

[from-internal]
exten => 1234,1,NoOp(Calling Astechogram)
same => n,Set(UUID=${SHELL(uuidgen -r)})
same => n,Audiosocket(${UUID},localhost:9093)
same => n,Hangup()

Explanation:
- Replace '1234' with your desired extension number.
- The UUID is generated using the 'uuidgen' command. Make sure this command is available on your system.
- 'localhost:9093' assumes Astechogram is running on the same machine as Asterisk. Adjust if needed.

Note: Ensure that the 'uuidgen' command is available on your system. If it's not, you may need to install it or use an alternative method to generate a UUID.

Usage:

1. Configure your Asterisk dialplan as shown above.

2. Ensure your Asterisk system can reach the machine running Astechogram on port 9093.

3. Run the Astechogram script:
   python astechogram.py

4. Dial the configured extension (e.g., 1234) from an Asterisk phone. The call will be connected
   to Astechogram, which will process the audio in real-time, transcribe speech, and send
   synthesized speech back to the caller.

Configuration:

You can adjust various parameters in astechogram.py to fine-tune its behavior:

- SAMPLE_RATE: Audio sample rate (default: 8000 Hz)
- CHANNELS: Number of audio channels (default: 1, mono)
- VOLUME_THRESHOLD: Threshold for detecting speech (default: 30)
- MIN_SPEECH_DURATION: Minimum duration of speech to process (default: 0.5 seconds)
- SILENCE_DURATION: Duration of silence to end capture (default: 1.5 seconds)
- BUFFER_SIZE: Size of audio buffer (default: 320 bytes)

Script Analysis:

Astechogram works by:
1. Establishing a TCP connection with Asterisk using the Audiosocket protocol.
2. Continuously capturing audio data from the call.
3. Detecting speech based on volume threshold and silence duration.
4. Sending detected speech to Deepgram for transcription.
5. Sending the transcribed text back to Deepgram for text-to-speech synthesis.
6. Streaming the synthesized speech back to Asterisk.

The script uses multithreading to handle audio capture and processing concurrently, ensuring real-time performance.

Contributing:

Contributions to Astechogram are welcome! Please feel free to submit a Pull Request.

License:

This project is licensed under the MIT License - see the LICENSE file for details.

The audiosocket library used in this project is sourced from https://github.com/silentindark/audiosocket_server and is subject to its own license terms. Please refer to the audiosocket_server repository for more information on its licensing.

Copyright (c) 2024 Michaël Benarouch (benasterisk@gmail.com)
GitHub Repository: https://github.com/yourusername/astechogram

Acknowledgments:

- Deepgram (https://deepgram.com/) for providing the speech-to-text and text-to-speech APIs
- Asterisk (https://www.asterisk.org/) for the PBX system integration
- The audiosocket library by silentindark (https://github.com/silentindark/audiosocket_server)

Disclaimer:

Astechogram is provided as-is, without any guarantees or warranty. The authors are not responsible for any damage or data loss that may occur from the use of this script.