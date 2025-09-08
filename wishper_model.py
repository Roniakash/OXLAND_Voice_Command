import json
import webbrowser
import tempfile
import os
import time
import sys
import datetime
import pygame
import difflib
from gtts import gTTS
import speech_recognition as sr

try:
    import sounddevice as sd
    import numpy as np
    from vosk import Model as VoskModel, KaldiRecognizer
    HAS_VOSK = True
except ImportError:
    HAS_VOSK = False


ASSISTANT_NAME = "Oxland"
COMPANY_NAME = "Oxbow Intellect Private Limited"
MODULES_FILE = r"C:\Users\ronia\Desktop\Voice_Command\modules_routes.json"


def speak_and_print(text: str, tts_lang: str = "en"):
    """Speak out loud and print to console safely."""
    print(f"Assistant: {text}")
    try:
        tts = gTTS(text=text, lang=tts_lang)
        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        tts.save(path)

        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        pygame.mixer.music.stop()
        pygame.mixer.quit()
        os.remove(path)

    except Exception as e:
        print(f"[TTS error: {e}]")


def listen_once(recognizer: sr.Recognizer, mic: sr.Microphone, language_code="en-US"):
    """Capture voice and return recognized text (Google STT)."""
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        print("🎙️ Listening...")
        audio = recognizer.listen(source)
    print("🔎 Processing...")
    try:
        text = recognizer.recognize_google(audio, language=language_code)
        print(f"User: {text}")
        return text
    except sr.UnknownValueError:
        print("Speech not understood.")
        return None
    except sr.RequestError as e:
        print(f"Google STT error: {e}")
        return None


def listen_once_vosk(timeout=5):
    """Capture audio and return recognized text using Vosk (offline)."""
    if not HAS_VOSK:
        return None

    try:
        model = VoskModel("vosk-model-small-en-us-0.15")
        rec = KaldiRecognizer(model, 16000)

        print("🎙️ Listening (Vosk)...")
        audio = sd.rec(int(timeout * 16000), samplerate=16000, channels=1, dtype="int16")
        sd.wait()

        rec.AcceptWaveform(audio.tobytes())
        result = json.loads(rec.Result())
        text = result.get("text", "").strip()
        if text:
            print(f"User (Vosk): {text}")
            return text
    except Exception as e:
        print(f"[Vosk error: {e}]")
    return None


def detect_language_choice(text: str):
    """Detect if user said English or Hindi."""
    if not text:
        return None
    t = text.lower().strip()

    if any(word in t for word in ["english", "eng", "इंग्लिश", "अंग्रेजी"]):
        return "en"
    if any(word in t for word in ["hindi", "हिंदी", "हिन्दी"]):
        return "hi"

    return None


def get_time_based_greeting(lang="en"):
    """Return time-based greeting in English or Hindi."""
    hour = datetime.datetime.now().hour
    if lang == "en":
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 15:
            return "Good noon"
        elif 15 <= hour < 18:
            return "Good afternoon"
        else:
            return "Good evening"
    else:
        if 5 <= hour < 12:
            return "सुप्रभात"
        elif 12 <= hour < 15:
            return "शुभ दोपहर"
        elif 15 <= hour < 18:
            return "शुभ अपराह्न"
        else:
            return "शुभ संध्या"


def check_identity_question(text: str):
    """Check if user asked about assistant or company."""
    if not text:
        return None
    t = text.lower()
    if "your name" in t or "assistant name" in t or "who are you" in t:
        return f"My name is {ASSISTANT_NAME}"
    if "company" in t or "which company" in t:
        return f"I work at {COMPANY_NAME}"
    return None


def match_tab(user_text, tab_names):
    """Fuzzy match user speech to a tab name."""
    if not user_text:
        return None
    user_text = user_text.lower()

    for name in tab_names:
        if name.lower() in user_text or user_text in name.lower():
            return name

    matches = difflib.get_close_matches(user_text, [t.lower() for t in tab_names], n=1, cutoff=0.6)
    if matches:
        for name in tab_names:
            if name.lower() == matches[0]:
                return name
    return None


PROMPTS = {
    "welcome": {"en": "Welcome to Oxland"},
    "choose_lang": {"en": "Please choose your language: English or Hindi."},
    "ask_name": {"en": "What is your name?", "hi": "कृपया अपना नाम बताइए।"},
    "now_select_tab": {"en": "Now you can select the tab.", "hi": "अब आप टैब चुन सकते हैं।"},
    "goodbye": {"en": "Opening the tab. Exiting. Goodbye!", "hi": "टैब खोल रहा हूँ। बाहर निकल रहा हूँ। अलविदा!"},
    "not_found": {"en": "Sorry, I couldn't find that tab. Exiting.", "hi": "क्षमा करें, वह टैब नहीं मिला। बाहर निकल रहा हूँ।"}
}


def main():
    try:
        with open(MODULES_FILE, "r", encoding="utf-8") as f:
            modules = json.load(f)
    except Exception as e:
        print(f"Error loading modules file: {e}")
        return

    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    speak_and_print(PROMPTS["welcome"]["en"], "en")
    speak_and_print(PROMPTS["choose_lang"]["en"], "en")

    chosen = None
    while not chosen:
        text = listen_once(recognizer, mic, "en-US")
        chosen = detect_language_choice(text)
        if not chosen:
            text = listen_once(recognizer, mic, "hi-IN")
            chosen = detect_language_choice(text)
        if not chosen:
            speak_and_print("Please say English or Hindi.", "en")

    # --- Ask name ---
    name_text = None
    while not name_text:
        speak_and_print(PROMPTS["ask_name"][chosen], "hi" if chosen == "hi" else "en")
        name_text = listen_once(recognizer, mic, "hi-IN" if chosen == "hi" else "en-US")

        # Try Vosk if Google STT fails
        if not name_text and HAS_VOSK:
            name_text = listen_once_vosk(timeout=4)

        if not name_text:
            speak_and_print("Sorry, I didn't catch that. Please say your name again.", "hi" if chosen == "hi" else "en")

    greet = get_time_based_greeting(chosen)
    speak_and_print(f"{greet}, {name_text}", "hi" if chosen == "hi" else "en")

    # --- Tab selection ---
    speak_and_print(PROMPTS["now_select_tab"][chosen], "hi" if chosen == "hi" else "en")

    tab_names = list(modules.keys())
    print("Available Tabs:", ", ".join(tab_names))

    selected_tab = None
    while not selected_tab:
        response = listen_once(recognizer, mic, "hi-IN" if chosen == "hi" else "en-US")
        if not response and HAS_VOSK:
            response = listen_once_vosk(timeout=5)
        if not response:
            continue

        if "exit" in response.lower() or "quit" in response.lower():
            speak_and_print("Okay, exiting now. Goodbye!", "hi" if chosen == "hi" else "en")
            sys.exit(0)

        if "my name" in response.lower():
            speak_and_print(f"Your name is {name_text}", "hi" if chosen == "hi" else "en")
            continue

        identity_answer = check_identity_question(response)
        if identity_answer:
            speak_and_print(identity_answer, "hi" if chosen == "hi" else "en")
            continue

        selected_tab = match_tab(response, tab_names)
        if not selected_tab:
            speak_and_print("I didn't match that to any tab. Please say again.", "hi" if chosen == "hi" else "en")

    url = modules.get(selected_tab)
    if url:
        speak_and_print(PROMPTS["goodbye"][chosen], "hi" if chosen == "hi" else "en")
        print(f"Opening tab '{selected_tab}' -> {url}")
        webbrowser.open(url)
    else:
        speak_and_print(PROMPTS["not_found"][chosen], "hi" if chosen == "hi" else "en")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting on user interrupt.")
        sys.exit(0)
