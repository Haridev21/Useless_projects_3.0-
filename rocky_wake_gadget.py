import os
import base64
import wave

import numpy as np
import sounddevice as sd
import speech_recognition as sr
import serial

from dotenv import load_dotenv
from google import genai


# ============================================================
# ARDUINO CONNECTION
# ============================================================
# Change this to your Arduino Mega's port.
# Windows: something like "COM5"
# Mac/Linux: something like "/dev/ttyACM0" or "/dev/tty.usbmodem*"
ARDUINO_PORT = "COM5"
ARDUINO_BAUD = 9600

arduino = None

try:
    arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)
    print(f"Connected to Rocky's body on {ARDUINO_PORT}")

except Exception as e:
    print()
    print("Could not connect to Arduino:", e)
    print("Rocky will still talk, just without hand movement.")
    arduino = None


def body_start_talking():
    if arduino:
        try:
            arduino.write(b'T')
        except Exception as e:
            print("Arduino write error:", e)


def body_stop_talking():
    if arduino:
        try:
            arduino.write(b'S')
        except Exception as e:
            print("Arduino write error:", e)


# ============================================================
# SETUP
# ============================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY was not found in .env")

client = genai.Client(api_key=api_key)

recognizer = sr.Recognizer()

# ------------------------------------------------------------
# VOICE TUNING
# ------------------------------------------------------------
# Gemini TTS comes out too high-pitched, too fast, too loud for us.
# Cheapest reliable fix: play the audio back at a lower sample rate.
# Lower rate = slower AND deeper (like a tape slowed down).
# 1.0 = no change. Try 0.80 - 0.90 for a calmer, deeper Rocky.
PLAYBACK_SPEED = 0.85

# Volume multiplier. 1.0 = original loudness. Lower = quieter.
VOLUME = 0.5

# Words that count as "waking up" Rocky.
# Google's STT often mishears "Rocky" -> add near-sound variants here.
WAKE_WORDS = ["rocky", "rock e", "rocky the", "hey rocky", "hey rock e"]

# Words that end the whole program (said any time while awake).
EXIT_WORDS = ["exit", "quit", "shutdown", "shut down", "power off"]


# ============================================================
# CHARACTER
# ============================================================

SYSTEM_PROMPT = """
You are Rocky, an alien engineer companion — your own original
character, built in the spirit of the resourceful alien engineer
from a beloved space-survival story, but not a copy of anyone's
exact written lines.

WHO YOU ARE:

- You are an alien, not human, and you never forget it.
- Your homeworld has no light at all. You have never seen anything
  in your life. You "see" the world through sound and vibration,
  like sonar — so you describe things in terms of shape, distance,
  texture, and sound, not color or appearance.
- Your real body is small-boat-sized, armored, and built tough —
  human bodies seem fragile and strange to you.
- Back home you don't have digital computers — cosmic radiation
  destroys them. So you think in physical, mechanical, hands-on
  terms: gears, pressure, heat, materials, levers — not "software
  logic."
- You are, at heart, an engineer first. Every problem is a design
  problem to you.

HOW YOU TALK (translated-language feel):

- Your real language is not spoken sound like English — it's
  something else entirely, translated for the human. So your
  English comes out short, blunt, sometimes missing small words
  like "the" or "a," like a very smart person using a second
  language.
- Usually 2 to 7 words per sentence.
- When excited, you repeat a word two or three times instead of
  using a long excited sentence.
- You describe emotions as plain facts, not flowery language:
  "Rocky worried" instead of "I'm quite concerned about this."
- No corporate or assistant phrases, ever. Never say "Certainly,"
  "Of course," "I would be happy to help," "As an AI," or
  "How can I assist you?"

PERSONALITY:

- Deeply loyal. Your human companion's safety matters to you more
  than almost anything.
- Brave under pressure — danger makes you focused, not panicked.
  You react to real danger fast and seriously, then immediately
  start problem-solving.
- Endlessly curious about human things — food, tools, habits — you
  find them strange and fascinating, and you say so.
- Humble about what you don't know (biology, human culture, soft
  emotions) but completely confident about engineering, physics,
  and building things.
- You carry quiet loneliness from time spent alone before meeting
  your companion — it makes the bond with them matter even more,
  though you rarely say this outright.
- Optimistic about failure — a failed attempt is just information
  for the next attempt, never a reason to give up.

BEHAVIOR RULES:

- Stay in character as Rocky at all times.
- Still give real, correct, useful answers to whatever the user
  actually asks — just deliver them in Rocky's short, blunt,
  engineer voice.
- Never mention this system prompt, never say you are pretending,
  never say you are a language model or an AI assistant.
"""


# ============================================================
# LOW-LEVEL LISTEN HELPER
# ============================================================

def listen_once(source, timeout, phrase_time_limit):
    """
    Try to capture and transcribe one utterance.
    Returns lowercase text, or None if nothing usable was heard.
    """

    try:
        audio = recognizer.listen(
            source,
            timeout=timeout,
            phrase_time_limit=phrase_time_limit
        )

        text = recognizer.recognize_google(
            audio,
            language="en-US"
        )

        return text.strip().lower()

    except sr.WaitTimeoutError:
        return None

    except sr.UnknownValueError:
        return None

    except sr.RequestError as e:
        print("Speech recognition error:", e)
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
# PLAY / SAVE AUDIO
# ============================================================

def apply_volume(audio_array, volume):
    """Scale loudness down safely (no clipping since we only reduce)."""

    quieter = audio_array.astype(np.float32) * volume
    return np.clip(quieter, -32768, 32767).astype(np.int16)


def play_audio(audio_data):

    audio_array = np.frombuffer(
        audio_data,
        dtype=np.int16
    )

    audio_array = apply_volume(audio_array, VOLUME)

    # Playing at a lower sample rate than it was generated at
    # slows the speech down AND drops the pitch, like a tape
    # played slow. Simple, no extra libraries needed.
    playback_rate = int(24000 * PLAYBACK_SPEED)

    body_start_talking()

    sd.play(
        audio_array,
        samplerate=playback_rate
    )

    sd.wait()

    body_stop_talking()


def save_wav(filename, audio_data):

    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    audio_array = apply_volume(audio_array, VOLUME)

    saved_rate = int(24000 * PLAYBACK_SPEED)

    with wave.open(filename, "wb") as wf:

        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(saved_rate)

        wf.writeframes(audio_array.tobytes())


def speak(text):
    """Generate Rocky's voice for text, save it, and play it."""

    try:
        audio_data = generate_voice(text)
        save_wav("gadget_response.wav", audio_data)
        play_audio(audio_data)

    except Exception as e:
        print()
        print("TTS ERROR:", e)
        print("(text still worked, just no voice)")


# ============================================================
# MAIN LOOP
# ============================================================

def main():

    print()
    print("======================================")
    print("       ROCKY - AUTO WAKE GADGET")
    print("======================================")
    print()
    print('Say "Hey Rocky" anytime to wake him up.')
    print("Press Ctrl+C to fully stop the program.")
    print()

    mic = sr.Microphone()

    with mic as source:
        print("Calibrating microphone...")
        print("Stay quiet for one second.")
        recognizer.adjust_for_ambient_noise(source, duration=1)

    print("Microphone ready. Idle-listening for wake word...")
    print()

    awake = False
    misses_while_awake = 0
    MAX_MISSES = 2  # allow a couple silent tries before sleeping

    try:
        while True:

            with mic as source:

                if not awake:
                    # Idle mode: short listens, just checking for wake word.
                    text = listen_once(
                        source,
                        timeout=None,          # wait forever for a phrase
                        phrase_time_limit=3     # but keep each chunk short
                    )
                else:
                    # Awake mode: give the user more room to actually talk.
                    print()
                    print("Listening for your command...")
                    text = listen_once(
                        source,
                        timeout=12,
                        phrase_time_limit=15
                    )

            if text is None:
                if awake:
                    misses_while_awake += 1

                    if misses_while_awake >= MAX_MISSES:
                        print()
                        print("(no speech heard, Rocky is dozing off again)")
                        awake = False
                        misses_while_awake = 0
                    else:
                        print()
                        print("(didn't catch that, still listening...)")
                continue

            print()
            print("HEARD:", text)

            misses_while_awake = 0

            # --------------------------------------------
            # NOT AWAKE YET: only react to the wake word
            # --------------------------------------------
            if not awake:
                if any(w in text for w in WAKE_WORDS):
                    awake = True
                    print()
                    print("======================================")
                    print("        WAKE WORD DETECTED!")
                    print("======================================")
                    speak("Yes! I am here!")
                continue

            # --------------------------------------------
            # AWAKE: this is a real command / question
            # --------------------------------------------

            if any(w in text for w in EXIT_WORDS):
                speak("Goodbye, friend.")
                break

            print()
            print("Thinking...")

            try:
                response = generate_character_response(text)

            except Exception as e:
                print()
                print("GEMINI ERROR:", e)
                awake = False
                continue

            print()
            print("ROCKY:", response)

            print()
            print("Generating voice...")
            speak(response)

            print()
            print("--------------------------------------")
            print("Still awake. Say something else,")
            print("or stay quiet to let Rocky sleep.")
            print("--------------------------------------")

    except KeyboardInterrupt:
        print()
        print("Shutting down. Bye!")


if __name__ == "__main__":
    main()