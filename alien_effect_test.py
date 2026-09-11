import wave
import numpy as np
import sounddevice as sd
from scipy import signal


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "gadget_response.wav"
OUTPUT_FILE = "alien_effect.wav"

SAMPLE_RATE = 24000


# ============================================================
# LOAD WAV
# ============================================================

def load_wav(filename):

    with wave.open(filename, "rb") as wf:

        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sample_rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())

    if channels != 1:
        raise ValueError("Audio must be mono.")

    if sample_width != 2:
        raise ValueError("Audio must be 16-bit.")

    audio = np.frombuffer(
        frames,
        dtype=np.int16
    ).astype(np.float32)

    audio /= 32768.0

    return audio, sample_rate


# ============================================================
# METALLIC DISTORTION
# ============================================================

def distortion(audio):

    drive = 1.6

    distorted = np.tanh(
        audio * drive
    )

    mix = 0.15

    return (
        audio * (1.0 - mix)
        + distorted * mix
    )


# ============================================================
# RING MODULATION
# ============================================================

def ring_modulation(audio, sample_rate):

    carrier_frequency = 45.0

    t = np.arange(
        len(audio)
    ) / sample_rate

    carrier = np.sin(
        2 * np.pi * carrier_frequency * t
    )

    modulated = audio * carrier

    mix = 0.12

    return (
        audio * (1.0 - mix)
        + modulated * mix
    )


# ============================================================
# METALLIC HIGH FREQUENCY
# ============================================================

def high_frequency_presence(audio, sample_rate):

    sos = signal.butter(
        2,
        4500,
        btype="highpass",
        fs=sample_rate,
        output="sos"
    )

    high = signal.sosfilt(
        sos,
        audio
    )

    mix = 0.08

    return (
        audio
        + high * mix
    )


# ============================================================
# NORMALIZE
# ============================================================

def normalize(audio):

    peak = np.max(
        np.abs(audio)
    )

    if peak == 0:
        return audio

    audio = audio / peak

    audio = audio * 0.85

    return audio


# ============================================================
# SAVE WAV
# ============================================================

def save_wav(filename, audio, sample_rate):

    audio_int16 = (
        np.clip(audio, -1, 1)
        * 32767
    ).astype(np.int16)

    with wave.open(filename, "wb") as wf:

        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        wf.writeframes(
            audio_int16.tobytes()
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("Loading audio...")

    audio, sample_rate = load_wav(
        INPUT_FILE
    )

    print("Applying metallic distortion...")

    audio = distortion(audio)

    print("Applying alien modulation...")

    audio = ring_modulation(
        audio,
        sample_rate
    )

    print("Adding high-frequency texture...")

    audio = high_frequency_presence(
        audio,
        sample_rate
    )

    print("Normalizing...")

    audio = normalize(audio)

    save_wav(
        OUTPUT_FILE,
        audio,
        sample_rate
    )

    print()
    print("Saved:")
    print(OUTPUT_FILE)
    print()
    print("Playing alien effect...")

    sd.play(
        audio,
        samplerate=sample_rate
    )

    sd.wait()

    print()
    print("Done.")


if __name__ == "__main__":
    main()