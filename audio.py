"""
 Author :- Aman Altaf Multani Awan
 Description:- Detecting and retrieving the audio during the video stream
             - The speech recording and saving into a wav format to analyze the data.
             - In this, we are using PyAudio source and build it for your system. Be sure to install the portaudio library development package (portaudio19-dev) and the python development package (python-all-dev) beforehand.
             - Also Using the wave module which provides a convenient interface to the WAV sound format.
"""

#import the necessary packages
# !/usr/bin/env python
import pyaudio
import wave
from array import array
#initialize for the variable

FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100 #“RATE” is the sampling rate as a number of the frames per second.
CHUNK = 1024 #“CHUNK” is the number of frames in the buffer which are splits into small signals
RECORD_SECONDS = 15
FILE_NAME = "RECORDING.wav"
#instantiate the pyaudio
audio=pyaudio.PyAudio()

#recording prerequisites
stream = audio.open(format=FORMAT, channels=CHANNELS,
                  rate=RATE,
                  input=True,
                  frames_per_buffer=CHUNK)

#starting recording
frames = []

for i in range(0, int(RATE/CHUNK*RECORD_SECONDS)):
    data = stream.read(CHUNK)
    data_chunk = array('h', data)
    vol = max(data_chunk)
    if(vol >= 500):
        print("something said")
        frames.append(data)
    else:
        print("nothing")
    print("\n")

#end of recording
stream.stop_stream()
stream.close()
audio.terminate()

#writing to file
wavfile = wave.open(FILE_NAME, 'wb')
wavfile.setnchannels(CHANNELS)
wavfile.setsampwidth(audio.get_sample_size(FORMAT))
wavfile.setframerate(RATE)

#append frames recorded to file
wavfile.writeframes(b''.join(frames))
wavfile.close()

