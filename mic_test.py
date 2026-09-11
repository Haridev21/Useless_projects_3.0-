import speech_recognition as sr


recognizer = sr.Recognizer()


print()
print("==============================")
print("     MICROPHONE TEST")
print("==============================")
print()
print("Calibrating microphone...")
print("Stay quiet for a moment.")
print()


with sr.Microphone() as source:

    recognizer.adjust_for_ambient_noise(
        source,
        duration=1
    )

    print("Listening...")
    print("Speak now.")

    audio = recognizer.listen(
        source
    )


print()
print("Processing speech...")


try:

    text = recognizer.recognize_google(
        audio
    )

    print()
    print("YOU SAID:")
    print(text)
    print()

except sr.UnknownValueError:

    print()
    print("Could not understand the speech.")
    print()

except sr.RequestError as e:

    print()
    print("Speech recognition service error:")
    print(e)
    print()