import json
import webbrowser
import os
import sys
import time
import datetime
import pygame
import difflib
from gtts import gTTS
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
from vosk import Model as VoskModel, KaldiRecognizer
import json as js
import tempfile

ASSISTANT_NAME = "Oxland"
COMPANY_NAME = "Oxbow Intellect Private Limited"
MODULES_FILE = "modules_routes.json"

# ------------------ Models ------------------
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"
vosk_model = VoskModel(VOSK_MODEL_PATH)
vosk_rec = KaldiRecognizer(vosk_model, 16000)

# ------------------ Audio Preprocess ------------------
def preprocess_audio(audio, target_db=-20.0):
    rms = np.sqrt(np.mean(audio**2))
    scalar = 10 ** (target_db / 20) / (rms + 1e-6)
    return np.clip(audio * scalar, -32768, 32767).astype(np.int16)

# ------------------ TTS ------------------
def speak_and_print(text: str, tts_lang: str = "en"):
    print(f"Assistant: {text}")
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        tts = gTTS(text=text, lang=tts_lang)
        tts.save(path)

        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.stop()
        pygame.mixer.quit()  
        time.sleep(0.05)    
    except Exception as e:
        print(f"[TTS error: {e}]")
    finally:
        if os.path.exists(path):
            os.remove(path)

# ------------------ Recording ------------------
def record_audio(seconds=3, samplerate=16000):
    print(f"(Listening for {seconds} seconds... speak now)")
    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()
    audio = preprocess_audio(audio)
    return audio

# ------------------ Whisper Recognition (low-latency) ------------------
def listen_once(language="en", seconds=3):
    audio_np = record_audio(seconds=seconds)
    print(f"(Processing... recognizing speech with Whisper)")
    try:
        audio_float = audio_np.astype(np.float32) / 32768.0
        segments, info = whisper_model.transcribe(audio_float, beam_size=5, language=language)
        text = " ".join([seg.text for seg in segments]).strip()
        if text:
            print(f"User: {text}")
            speak_and_print(f"You said: {text}", "hi" if language == "hi" else "en")
            return text
        else:
            print("No speech recognized.")
            return None
    except Exception as e:
        print(f"[Whisper error: {e}]")
        return None

def listen_name_with_vosk():
    print("(Listening for your name with Vosk...)")
    audio = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype="int16")
    sd.wait()
    if vosk_rec.AcceptWaveform(audio.tobytes()):
        result = js.loads(vosk_rec.Result())
        text = result.get("text", "").strip().title()
        return text if text else None
    return None

# ------------------ Language ------------------
def detect_language_choice(text: str):
    if not text:
        return None
    t = text.lower().strip()
    english_keywords = ["english", "eng", "इंग्लिश", "अंग्रेजी"]
    hindi_keywords = ["hindi", "हिंदी", "हिन्दी"]

    for word in english_keywords:
        if word in t:
            return "en"
    for word in hindi_keywords:
        if word in t:
            return "hi"

    all_keywords = english_keywords + hindi_keywords
    matches = difflib.get_close_matches(t, all_keywords, n=1, cutoff=0.5)
    if matches:
        if matches[0] in english_keywords:
            return "en"
        else:
            return "hi"
    return None

# ------------------ Helpers ------------------
def get_time_based_greeting(lang="en"):
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
    if not text:
        return None
    t = text.lower()
    identity_phrases = {
        "name": ["your name", "assistant name", "who are you"],
        "company": ["company", "which company", "where do you work"]
    }
    for key, phrases in identity_phrases.items():
        matches = difflib.get_close_matches(t, phrases, n=1, cutoff=0.5)
        if matches:
            if key == "name":
                return f"My name is {ASSISTANT_NAME}"
            elif key == "company":
                return f"I work at {COMPANY_NAME}"
    return None

def match_tab(user_text, tab_names):
    if not user_text:
        return None
    user_text = user_text.lower()
    for name in tab_names:
        if name.lower() in user_text or user_text in name.lower():
            return name
    matches = difflib.get_close_matches(user_text, [t.lower() for t in tab_names], n=1, cutoff=0.5)
    if matches:
        for name in tab_names:
            if name.lower() == matches[0]:
                return name
    return None

def ask_yes_no(text):
    if not text:
        return None
    t = text.lower()
    if "yes" in t or "yeah" in t or "yep" in t:
        return "yes"
    if "no" in t or "nah" in t or "nope" in t:
        return "no"
    matches = difflib.get_close_matches(t, ["yes", "no", "yeah", "nah", "nope", "yep"], n=1, cutoff=0.5)
    if matches:
        if matches[0] in ["yes", "yeah", "yep"]:
            return "yes"
        else:
            return "no"
    return None

# ------------------ Prompts ------------------
PROMPTS = {
    "welcome": {"en": "Welcome to Oxland"},
    "choose_lang": {"en": "Please choose your language: English or Hindi."},
    "ask_name": {"en": "What is your name?", "hi": "कृपया अपना नाम बताइए।"},
    "ask_address_option": {"en": "Do you want to provide an address? Yes or No?", "hi": "क्या आप पता देना चाहते हैं? हाँ या नहीं?"},
    "ask_address": {"en": "Please say the address you want to search on Google Maps.", "hi": "कृपया वह पता बताएं जिसे आप Google Maps पर देखना चाहते हैं।"},
    "now_select_tab": {"en": "Now you can select the tab.", "hi": "अब आप टैब चुन सकते हैं।"},
    "goodbye": {"en": "Opening the tab. Exiting. Goodbye!", "hi": "टैब खोल रहा हूँ। बाहर निकल रहा हूँ। अलविदा!"},
    "not_found": {"en": "Sorry, I couldn't find that tab. Exiting.", "hi": "क्षमा करें, वह टैब नहीं मिला। बाहर निकल रहा हूँ।"}
}

# ------------------ Steps ------------------
def choose_language():
    speak_and_print(PROMPTS["choose_lang"]["en"], "en")
    chosen = None
    while not chosen:
        text = listen_once("en", seconds=3)
        chosen = detect_language_choice(text)
        if not chosen:
            text = listen_once("hi", seconds=3)
            chosen = detect_language_choice(text)
        if not chosen:
            speak_and_print("Please say English or Hindi.", "en")
    return chosen

def capture_name(chosen):
    name_text = None
    while not name_text:
        speak_and_print(PROMPTS["ask_name"][chosen], "hi" if chosen == "hi" else "en")
        name_text = listen_name_with_vosk()
        if not name_text:
            speak_and_print("Sorry, I didn't catch that. Please say your name again.", "hi" if chosen == "hi" else "en")
    return name_text

def ask_address(chosen):
    speak_and_print(PROMPTS["ask_address_option"][chosen], "hi" if chosen == "hi" else "en")
    while True:
        response = listen_once("hi" if chosen == "hi" else "en", seconds=3)
        choice = ask_yes_no(response)
        if choice == "yes":
            speak_and_print(PROMPTS["ask_address"][chosen], "hi" if chosen == "hi" else "en")
            address = listen_once("hi" if chosen == "hi" else "en", seconds=3)
            if address:
                url = f"https://www.google.com/maps/place/{address.replace(' ', '+')}"
                speak_and_print(f"Opening Google Maps for {address}. Exiting now.", "hi" if chosen == "hi" else "en")
                webbrowser.open(url)
                sys.exit(0)
            else:
                speak_and_print("Sorry, I didn't catch the address. Exiting.", "hi" if chosen == "hi" else "en")
                sys.exit(0)
        elif choice == "no":
            return
        else:
            speak_and_print("Please say Yes or No.", "hi" if chosen == "hi" else "en")

def select_tab(chosen, modules, name_text):
    tab_names = list(modules.keys())
    print("Available Tabs:", ", ".join(tab_names))
    selected_tab = None
    while not selected_tab:
        response = listen_once("hi" if chosen == "hi" else "en", seconds=3)
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
    return selected_tab

# ------------------ Main ------------------
def main():
    try:
        with open(MODULES_FILE, "r", encoding="utf-8") as f:
            modules = json.load(f)
    except Exception as e:
        print(f"Error loading modules file: {e}")
        return

    speak_and_print(PROMPTS["welcome"]["en"], "en")
    chosen = choose_language()
    name_text = capture_name(chosen)
    greet = get_time_based_greeting(chosen)
    speak_and_print(f"{greet}, {name_text}", "hi" if chosen == "hi" else "en")
    ask_address(chosen)
    speak_and_print(PROMPTS["now_select_tab"][chosen], "hi" if chosen == "hi" else "en")
    selected_tab = select_tab(chosen, modules, name_text)
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
