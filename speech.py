"""
 Author :- Aman Altaf Multani Awan
 Description:- Recognize speech using Google Speech Recognition
             - Listen for the first phrase and extract it into audio data
             - Using the library for performing the speech recognition with the support of several engines and API’s online and as well as offline.
    """

import speech_recognition as sr

r = sr.Recognizer()

with sr.Microphone as source:
    print("Speak Anything: ")
    audio = r.listen(source)
    try:
        text = r.recognize_google(audio)
        print("You said : {}".format(text))
    except LookupError: #Shows error if speech is unintelligible
print("Sorry could not recognize what you said")