import json
import webbrowser
import tempfile
import os
import time
import sys
import datetime
import pygame
import difflib
import numpy as np
import sounddevice as sd
from gtts import gTTS
from faster_whisper import WhisperModel
from collections import deque

# -------- Settings --------
ASSISTANT_NAME = "Oxland"
COMPANY_NAME = "Oxbow Intellect Private Limited"
MODULES_FILE = r"C:\Users\ronia\Desktop\Voice_Command\modules_routes.json"
WHISPER_MODEL = "small"   # "tiny", "base", "small", "medium", "large-v3"

# Load Whisper once
print("Loading Whisper model... (this may take a moment)")
whisper = WhisperModel(WHISPER_MODEL, device="cpu")

# -------- Helpers --------
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

def listen_stream(language="en"):
    """Stream microphone input and return recognized text when phrase ends."""
    sr = 16000
    block_size = 1024
    buffer = deque(maxlen=sr * 10)  # keep last 10 seconds
    phrase_detected = False
    result_text = ""

    def callback(indata, frames, time_info, status):
        buffer.extend(indata[:, 0])

    # Start recording
    with sd.InputStream(samplerate=sr, channels=1, callback=callback, dtype="float32"):
        print("(Listening... streaming)")
        while True:
            if len(buffer) > sr * 2:  # at least 2 sec of audio
                audio = np.array(buffer, dtype=np.float32)
                segments, _ = whisper.transcribe(audio, language=language)
                text = " ".join([seg.text for seg in segments]).strip()
                if text:
                    print(f"User: {text}")
                    tts_lang = "hi" if language == "hi" else "en"
                    speak_and_print(f"You said: {text}", tts_lang)
                    return text

def detect_language_choice(text: str):
    if not text:
        return None
    t = text.lower().strip()
    if any(word in t for word in ["english", "eng", "इंग्लिश", "अंग्रेजी"]):
        return "en"
    if any(word in t for word in ["hindi", "हिंदी", "हिन्दी"]):
        return "hi"
    return None

def get_time_based_greeting(lang="en"):
    hour = datetime.datetime.now().hour
    if lang == "en":
        if 5 <= hour < 12: return "Good morning"
        elif 12 <= hour < 15: return "Good noon"
        elif 15 <= hour < 18: return "Good afternoon"
        else: return "Good evening"
    else:
        if 5 <= hour < 12: return "सुप्रभात"
        elif 12 <= hour < 15: return "शुभ दोपहर"
        elif 15 <= hour < 18: return "शुभ अपराह्न"
        else: return "शुभ संध्या"

def check_identity_question(text: str):
    if not text: return None
    t = text.lower()
    if "your name" in t or "assistant name" in t or "who are you" in t:
        return f"My name is {ASSISTANT_NAME}"
    if "company" in t or "which company" in t:
        return f"I work at {COMPANY_NAME}"
    return None

def match_tab(user_text, tab_names):
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

# -------- Prompts --------
PROMPTS = {
    "welcome": {"en": "Welcome to Oxland"},
    "choose_lang": {"en": "Please choose your language: English or Hindi."},
    "ask_name": {"en": "What is your name?", "hi": "कृपया अपना नाम बताइए।"},
    "now_select_tab": {"en": "Now you can select the tab.", "hi": "अब आप टैब चुन सकते हैं।"},
    "goodbye": {"en": "Opening the tab. Exiting. Goodbye!", "hi": "टैब खोल रहा हूँ। बाहर निकल रहा हूँ। अलविदा!"},
    "not_found": {"en": "Sorry, I couldn't find that tab. Exiting.", "hi": "क्षमा करें, वह टैब नहीं मिला। बाहर निकल रहा हूँ।"}
}

# -------- Main --------
def main():
    try:
        with open(MODULES_FILE, "r", encoding="utf-8") as f:
            modules = json.load(f)
    except Exception as e:
        print(f"Error loading modules file: {e}")
        return

    # 1) Welcome
    speak_and_print(PROMPTS["welcome"]["en"], "en")
    speak_and_print(PROMPTS["choose_lang"]["en"], "en")

    # 2) Choose language
    chosen = None
    while not chosen:
        text = listen_stream("en")
        chosen = detect_language_choice(text)
        if not chosen:
            text = listen_stream("hi")
            chosen = detect_language_choice(text)
        if not chosen:
            speak_and_print("Please say English or Hindi.", "en")

    # 3) Ask name
    name_text = None
    while not name_text:
        speak_and_print(PROMPTS["ask_name"][chosen], "hi" if chosen == "hi" else "en")
        name_text = listen_stream(chosen)
        if not name_text:
            speak_and_print("Sorry, I didn't catch that. Please say your name again.", "hi" if chosen == "hi" else "en")

    # Greet user
    greet = get_time_based_greeting(chosen)
    speak_and_print(f"{greet}, {name_text}", "hi" if chosen == "hi" else "en")

    # 4) Tab selection
    speak_and_print(PROMPTS["now_select_tab"][chosen], "hi" if chosen == "hi" else "en")
    tab_names = list(modules.keys())
    print("Available Tabs:", ", ".join(tab_names))  # print only

    selected_tab = None
    while not selected_tab:
        response = listen_stream(chosen)
        if not response:
            continue

        # Special cases
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

        # Tab matching
        selected_tab = match_tab(response, tab_names)
        if not selected_tab:
            speak_and_print("I didn't match that to any tab. Please say again.", "hi" if chosen == "hi" else "en")

    # 5) Open tab
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
