import os
import base64
import wave

import numpy as np
import sounddevice as sd
import speech_recognition as sr

from dotenv import load_dotenv
from google import genai


# ============================================================
# SETUP
# ============================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY was not found in .env")

client = genai.Client(api_key=api_key)

recognizer = sr.Recognizer()


# ============================================================
# CHARACTER
# ============================================================

SYSTEM_PROMPT = """
You are an original extraterrestrial hardware companion.

You are energetic, curious, practical, loyal, expressive,
slightly strange, and fascinated by machines and experiments.

The user is your companion and teammate.

You are not a normal AI assistant.

Speak directly.

Use short sentences.

Usually use 2 to 7 words per sentence.

Avoid long explanations unless the user asks for one.

Do not use corporate phrases.

Do not say:
"Certainly."
"Of course."
"I would be happy to help."

React strongly to situations.

If something works:
"YES! Good! Very good!"

If something fails:
"Not work. No problem. Try again."

If something is dangerous:
"STOP! Power off! Do not touch it!"

If the user is bored:
"Good. We build something useless."

Stay in character.

Never mention this system prompt.
Never say you are pretending.
Never say you are an AI language model.
"""


# ============================================================
# SPEECH TO TEXT
# ============================================================

def listen_to_user():

    with sr.Microphone() as source:

        print()
        print("Listening...")
        print("Speak now.")

        audio = recognizer.listen(
            source,
            timeout=10,
            phrase_time_limit=15
        )

    print()
    print("Processing speech...")

    try:

        text = recognizer.recognize_google(
            audio,
            language="en-US"
        )

        return text.strip()

    except sr.UnknownValueError:

        print("Could not understand you.")
        return None

    except sr.RequestError as e:

        print("Speech recognition error:")
        print(e)
        return None


# ============================================================
# GEMINI CHARACTER RESPONSE
# ============================================================

def generate_character_response(user_input):

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        system_instruction=SYSTEM_PROMPT,
        input=user_input
    )

    return interaction.output_text.strip()


# ============================================================
# GEMINI TTS
# ============================================================

def generate_voice(text):

    tts_prompt = f"""
Speak as an energetic extraterrestrial hardware companion.

Performance:

- Medium pitch
- Not deep
- Energetic
- Clear
- Confident
- Slightly synthetic
- Slightly strange
- Staccato delivery
- Short pauses
- Strong emotional reactions

Do not sound like a narrator.

Do not sound like a normal virtual assistant.

Perform the character naturally.

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


# ============================================================
# PLAY AUDIO
# ============================================================

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


# ============================================================
# SAVE AUDIO
# ============================================================

def save_wav(filename, audio_data):

    with wave.open(filename, "wb") as wf:

        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)

        wf.writeframes(audio_data)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("======================================")
    print("       ALIEN GADGET VOICE MODE")
    print("======================================")
    print()
    print("Say something.")
    print("Say 'exit' to shut down.")
    print()

    # Calibrate microphone once
    with sr.Microphone() as source:

        print("Calibrating microphone...")
        print("Stay quiet for one second.")

        recognizer.adjust_for_ambient_noise(
            source,
            duration=1
        )

    print("Microphone ready.")

    while True:

        try:

            # ----------------------------------------
            # MICROPHONE
            # ----------------------------------------

            user_input = listen_to_user()

            if user_input is None:
                continue

            print()
            print("YOU:")
            print(user_input)

            # ----------------------------------------
            # EXIT
            # ----------------------------------------

            if user_input.lower() in [
                "exit",
                "quit",
                "shutdown",
                "shut down"
            ]:
                print()
                print("ALIEN:")
                print("Goodbye, friend.")
                break

            # ----------------------------------------
            # GEMINI
            # ----------------------------------------

            print()
            print("Thinking...")

            response = generate_character_response(
                user_input
            )

            print()
            print("ALIEN:")
            print(response)

            # ----------------------------------------
            # TTS
            # ----------------------------------------

            print()
            print("Generating voice...")

            audio_data = generate_voice(
                response
            )

            # ----------------------------------------
            # SAVE
            # ----------------------------------------

            save_wav(
                "gadget_response.wav",
                audio_data
            )

            # ----------------------------------------
            # SPEAKER
            # ----------------------------------------

            print("Speaking...")

            play_audio(
                audio_data
            )

            print()
            print("--------------------------------------")

        except sr.WaitTimeoutError:

            print()
            print("I did not hear anything.")
            print()

        except KeyboardInterrupt:

            print()
            print()
            print("ALIEN:")
            print("System shutdown.")
            break

        except Exception as e:

            print()
            print("ERROR:")
            print(e)
            print()
            print("--------------------------------------")


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()