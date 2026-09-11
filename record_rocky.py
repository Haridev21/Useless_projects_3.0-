import os
import wave
import pyaudio


# ==========================================
# SETTINGS
# ==========================================

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2
CHUNK = 1024

POSITIVE_COUNT = 10
NEGATIVE_COUNT = 10

BASE_FOLDER = "rocky_samples"
POSITIVE_FOLDER = os.path.join(BASE_FOLDER, "positive")
NEGATIVE_FOLDER = os.path.join(BASE_FOLDER, "negative")


# ==========================================
# CREATE FOLDERS
# ==========================================

os.makedirs(POSITIVE_FOLDER, exist_ok=True)
os.makedirs(NEGATIVE_FOLDER, exist_ok=True)


# ==========================================
# AUDIO SETUP
# ==========================================

audio = pyaudio.PyAudio()


def record_audio(filename, duration=2):

    stream = audio.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    frames = []

    for _ in range(
        int(SAMPLE_RATE / CHUNK * duration)
    ):
        data = stream.read(
            CHUNK,
            exception_on_overflow=False
        )
        frames.append(data)

    stream.stop_stream()
    stream.close()

    with wave.open(filename, "wb") as wf:

        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"".join(frames))


# ==========================================
# POSITIVE RECORDINGS
# ==========================================

print()
print("======================================")
print("       ROCKY WAKE WORD RECORDER")
print("======================================")
print()

print("We will record:")
print()
print('10 recordings of "Hey Rocky"')
print("10 recordings of normal speech")
print()

input("Press ENTER to start...")

print()
print("POSITIVE RECORDINGS")
print('Say "Hey Rocky" each time.')
print()


for i in range(1, POSITIVE_COUNT + 1):

    print("--------------------------------------")
    print(f"Recording {i}/{POSITIVE_COUNT}")
    print('Say: "Hey Rocky"')
    input("Press ENTER when ready...")

    filename = os.path.join(
        POSITIVE_FOLDER,
        f"rocky_{i:02d}.wav"
    )

    print("Recording...")

    record_audio(
        filename,
        duration=2
    )

    print("Saved:", filename)
    print()


# ==========================================
# NEGATIVE RECORDINGS
# ==========================================

print()
print("======================================")
print("       NEGATIVE RECORDINGS")
print("======================================")
print()

print("Now speak normally.")
print()
print("IMPORTANT:")
print("Do NOT say 'Hey Rocky'.")
print()
print("You can say things like:")
print('"Hello, how are you?"')
print('"What are we building today?"')
print('"Turn on the computer."')
print()

input("Press ENTER to start...")

for i in range(1, NEGATIVE_COUNT + 1):

    print("--------------------------------------")
    print(f"Recording {i}/{NEGATIVE_COUNT}")

    input("Press ENTER and speak normally...")

    filename = os.path.join(
        NEGATIVE_FOLDER,
        f"negative_{i:02d}.wav"
    )

    print("Recording...")

    record_audio(
        filename,
        duration=2
    )

    print("Saved:", filename)
    print()


# ==========================================
# CLEANUP
# ==========================================

audio.terminate()

print()
print("======================================")
print("          RECORDING COMPLETE")
print("======================================")
print()

print("Your recordings are in:")
print(BASE_FOLDER)
print()