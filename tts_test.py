import os
import base64
import wave
import numpy as np
import sounddevice as sd

from dotenv import load_dotenv
from google import genai


# --------------------------------
# Load API key
# --------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY was not found in .env")


# --------------------------------
# Create Gemini client
# --------------------------------

client = genai.Client(api_key=api_key)


# --------------------------------
# Generate Gemini TTS
# --------------------------------

print("Generating Gemini voice...")

interaction = client.interactions.create(
    model="gemini-3.1-flash-tts-preview",

    input="""
    Speak as a mysterious extraterrestrial artificial intelligence.

    The voice should be:
    - calm
    - deep
    - slightly strange
    - mysterious
    - unsettling
    - slow and deliberate

    Say:

    Hello human. I am awake.
    Your world is... interesting.
    """,

    response_format={
        "type": "audio"
    },

    generation_config={
        "speech_config": [
            {
                "voice": "Kore"
            }
        ]
    }
)


# --------------------------------
# Get audio data
# --------------------------------

audio_data = base64.b64decode(
    interaction.output_audio.data
)


# --------------------------------
# Save PCM as WAV
# --------------------------------

filename = "alien_test.wav"

with wave.open(filename, "wb") as wf:

    # Mono
    wf.setnchannels(1)

    # 16-bit audio
    wf.setsampwidth(2)

    # Gemini TTS sample rate
    wf.setframerate(24000)

    wf.writeframes(audio_data)


print("Audio generated successfully!")
print("Saved as:", filename)


# --------------------------------
# Convert PCM bytes to NumPy
# --------------------------------

audio_array = np.frombuffer(
    audio_data,
    dtype=np.int16
)


# --------------------------------
# Play through PC speaker
# --------------------------------

print("Playing audio...")

sd.play(
    audio_array,
    samplerate=24000
)

sd.wait()

print("Finished!")