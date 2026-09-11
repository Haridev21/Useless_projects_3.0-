import pyaudio
import numpy as np

from openwakeword.model import Model


# ==========================================
# SETUP
# ==========================================

print()
print("======================================")
print("        WAKE WORD TEST")
print("======================================")
print()

print("Loading wake-word model...")


model = Model(
    wakeword_models=["hey_jarvis"],
    inference_framework="onnx"
)


print("Model loaded.")
print()
print('Say "Hey Jarvis"')
print("Press Ctrl+C to stop.")
print()


# ==========================================
# MICROPHONE
# ==========================================

audio = pyaudio.PyAudio()

stream = audio.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    frames_per_buffer=1280
)


# ==========================================
# WAKE WORD DETECTION
# ==========================================

try:

    while True:

        data = stream.read(
            1280,
            exception_on_overflow=False
        )

        audio_frame = np.frombuffer(
            data,
            dtype=np.int16
        )

        prediction = model.predict(
            audio_frame
        )

        score = prediction.get(
            "hey_jarvis",
            0
        )

        if score > 0.5:

            print()
            print("======================================")
            print("       WAKE WORD DETECTED!")
            print("======================================")
            print()

            # Prevent immediate repeated detections
            model.reset()


except KeyboardInterrupt:

    print()
    print("Stopping...")


finally:

    stream.stop_stream()
    stream.close()
    audio.terminate()

    print("Microphone closed.")