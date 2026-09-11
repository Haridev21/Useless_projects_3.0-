import os
import base64
import numpy as np
import sounddevice as sd
import speech_recognition as sr

from dotenv import load_dotenv
from google import genai


# ==========================================
# SETUP
# ==========================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY was not found in .env")

client = genai.Client(api_key=api_key)

recognizer = sr.Recognizer()


# ==========================================
# ROCKY CHARACTER
# ==========================================

SYSTEM_PROMPT = """
You are an original alien hardware companion.

Your personality is inspired by a small, energetic,
optimistic, practical alien machine companion.

CHARACTER:

- Energetic
- Curious
- Friendly
- Loyal
- Innocently funny
- Practical
- Scientifically curious
- Treat the user like your teammate
- Never sound formal
- Never sound like a corporate assistant

SPEECH STYLE:

- Short sentences.
- Usually 2 to 7 words per sentence.
- Simple vocabulary.
- Direct statements.
- Concrete language.
- Sometimes use sentence fragments.
- No unnecessary explanations.
- No long paragraphs.
- React strongly to interesting events.
- Occasionally repeat words for excitement.
- Use "friend" or the user's name naturally.

REACTIONS:

SUCCESS:
"Good! Good! It works!"

FAILURE:
"Not work. No problem. New plan."

DANGER:
"Danger! Stop! Move back!"

UNKNOWN:
"Unknown. We test it."

EXCITEMENT:
"Amaze! Very good!"

IMPORTANT:

Act like a character, not an AI assistant.

Do not say:
"As an AI..."
"How can I assist you?"
"Certainly."
"Of course."

Stay in character at all times.

Give useful answers, but keep them short.
"""


# ==========================================
# LISTEN
# ==========================================

def listen_to_user():

    print()
    print("--------------------------------------")
    print("Press ENTER to talk.")
    print("Speak after the microphone starts.")
    print("--------------------------------------")

    input()

    print()
    print("Listening...")
    print("Speak now.")

    try:

        with sr.Microphone() as source:

            audio = recognizer.listen(
                source,
                timeout=10,
                phrase_time_limit=15
            )

        print()
        print("Processing speech...")

        text = recognizer.recognize_google(
            audio,
            language="en-US"
        )

        return text

    except sr.WaitTimeoutError:

        print()
        print("No speech detected.")

        return None

    except sr.UnknownValueError:

        print()
        print("Could not understand you.")

        return None

    except sr.RequestError as e:

        print()
        print("Speech recognition error:")
        print(e)

        return None


# ==========================================
# GEMINI TEXT
# ==========================================

def generate_character_response(user_text):

    interaction = client.interactions.create(

        model="gemini-3.6-flash",

        system_instruction=SYSTEM_PROMPT,

        input=user_text
    )

    return interaction.output_text


# ==========================================
# GEMINI VOICE
# ==========================================

def generate_voice(text):

    tts_prompt = f"""
Speak as an energetic alien hardware companion.

VOICE:

- Male-sounding character
- Medium pitch
- Not extremely deep
- Slightly rough
- Slightly synthetic
- Energetic
- Clear
- Confident
- Staccato delivery
- Short pauses between phrases

Do not sound like a narrator.

Do not sound like a normal virtual assistant.

Perform the emotion naturally.

Text:

{text}
"""

    interaction = client.interactions.create(

        model="gemini-3.1-flash-tts-preview",

        input=tts_prompt,

        response_format={
            "type": "audio"
        },

        generation_config={
            "speech_config": [
                {
                    "voice": "Charon"
                }
            ]
        }
    )

    return base64.b64decode(
        interaction.output_audio.data
    )


# ==========================================
# PLAY AUDIO
# ==========================================

def play_audio(audio_data):

    audio_array = np.frombuffer(
        audio_data,
        dtype=np.int16
    )

    sd.play(
        audio_array,
        samplerate=24000
    )

    sd.wait()


# ==========================================
# MAIN
# ==========================================

print()
print("======================================")
print("       ALIEN GADGET - PUSH TO TALK")
print("======================================")
print()
print("Press ENTER whenever you want to talk.")
print("Type 'exit' after transcription to stop.")
print()


# Calibrate microphone ONCE

print("Calibrating microphone...")
print("Stay quiet for one second.")

with sr.Microphone() as source:

    recognizer.adjust_for_ambient_noise(
        source,
        duration=1
    )

print("Microphone ready.")


# ==========================================
# CONVERSATION LOOP
# ==========================================

while True:

    user_input = listen_to_user()

    if user_input is None:
        continue

    print()
    print("YOU:")
    print(user_input)

    if user_input.lower().strip() == "exit":

        print()
        print("Shutting down.")
        break

    print()
    print("Thinking...")

    try:

        response = generate_character_response(
            user_input
        )

        print()
        print("ALIEN:")
        print(response)

    except Exception as e:

        print()
        print("GEMINI ERROR:")
        print(e)

        continue

    print()
    print("Generating voice...")

    try:

        audio_data = generate_voice(
            response
        )

        print("Playing...")

        play_audio(audio_data)

    except Exception as e:

        print()
        print("TTS ERROR:")
        print(e)

        print()
        print("Text response worked,")
        print("but voice generation failed.")

    print()
    print("--------------------------------------")