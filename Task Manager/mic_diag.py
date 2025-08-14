# mic_diag.py
import speech_recognition as sr

print("=== INPUT DEVICES ===")
for i, name in enumerate(sr.Microphone.list_microphone_names() or []):
    print(f"[{i}] {name}")

# 👉 edit this to the index that matches your actual mic from the list above
DEVICE_INDEX = None  # e.g., 0, 1, 2 ...

r = sr.Recognizer()
r.dynamic_energy_threshold = False
r.energy_threshold = 500  # bump to 800–1200 if your room is loud

with sr.Microphone(device_index=DEVICE_INDEX) as source:
    print("\nSpeak for up to 5 seconds…")
    r.adjust_for_ambient_noise(source, duration=0.2)
    audio = r.listen(source, timeout=5, phrase_time_limit=5)

print("Recognizing…")
try:
    text = r.recognize_google(audio, language="en-US")
    print("You said:", text)
except sr.UnknownValueError:
    print("Nothing recognized.")
except Exception as e:
    print("Recognition error:", e)

