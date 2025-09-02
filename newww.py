import os
import tempfile
import uuid
import speech_recognition as sr
from gtts import gTTS
import pygame
import requests
import datetime
import sys

# ==========================
# CONFIG
# ==========================
gemini_key = "AIzaSyDU7k71ooFAqL6EIAV4k0QZUj2bccJ_zvk"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

current_language = "en"
user_name = "User"

# ==========================
# TEXT TO SPEECH
# ==========================
def say(text, lang=None):
    """Speak text in English/Hindi/Bengali using gTTS + pygame and print it."""
    global current_language
    if lang is None:
        lang = current_language

    print(f"🗣 {text}")  # Print what will be spoken

    try:
        temp_file = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp3")
        tts = gTTS(text=text, lang=lang)
        tts.save(temp_file)

        pygame.mixer.init()
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.quit()
        os.remove(temp_file)
    except Exception as e:
        print("TTS Error:", e)

# ==========================
# SPEECH RECOGNITION
# ==========================
def input_audio():
    """Capture voice input from microphone until user speaks"""
    r = sr.Recognizer()
    while True:
        with sr.Microphone() as source:
            print("🎤 Listening....")
            r.pause_threshold = 1
            try:
                audio = r.listen(source, timeout=None, phrase_time_limit=8)
            except sr.WaitTimeoutError:
                continue
        try:
            query = r.recognize_google(audio, language='en-IN')
            return query
        except Exception:
            continue

# ==========================
# WISH ME FUNCTION
# ==========================
def wishme():
    hour = int(datetime.datetime.now().hour)
    if current_language == "hi":
        if 0 <= hour < 12:
            say("सुप्रभात!")
        elif 12 <= hour < 18:
            say("नमस्कार!")
        else:
            say("शुभ संध्या!")
    elif current_language == "bn":
        if 0 <= hour < 12:
            say("সুপ্রভাত!")
        elif 12 <= hour < 18:
            say("শুভ অপরাহ্ন!")
        else:
            say("শুভ সন্ধ্যা!")
    else:
        if 0 <= hour < 12:
            say("Good Morning!")
        elif 12 <= hour < 18:
            say("Good Afternoon!")
        else:
            say("Good Evening!")

# ==========================
# USER SETUP (LANG + NAME)
# ==========================
def setup_user():
    global current_language, user_name

    # Welcome with company intro
    say("Welcome to Oxland, from Oxbow Intellect Private Limited!", lang="en")

    # Step 1: Select Language
    say("Please select a language: English, Hindi, or Bengali", lang="en")
    language_choice = input_audio().lower()

    while not language_choice:
        language_choice = input_audio().lower()

    if "hindi" in language_choice:
        current_language = "hi"
        say("आपने हिंदी चुना है")
    elif "bengali" in language_choice or "bangla" in language_choice:
        current_language = "bn"
        say("আপনি বাংলা বেছে নিয়েছেন")
    else:
        current_language = "en"
        say("You have selected English")

    # Step 2: Ask for name
    if current_language == "hi":
        ask_name = "आपका नाम क्या है?"
    elif current_language == "bn":
        ask_name = "আপনার নাম কি?"
    else:
        ask_name = "What is your name?"

    say(ask_name)
    name = input_audio()

    if name:
        user_name = name
        if current_language == "hi":
            say(f"नमस्ते {name}, आपसे मिलकर अच्छा लगा! मैं Oxland हूँ, Oxbow Intellect Private Limited से।")
        elif current_language == "bn":
            say(f"হ্যালো {name}, আপনাকে পেয়ে ভালো লাগলো! আমি Oxland, Oxbow Intellect Private Limited থেকে।")
        else:
            say(f"Hello {name}, nice to meet you! I am Oxland from Oxbow Intellect Private Limited.")

    # Step 3: Wish Me
    wishme()

# ==========================
# GEMINI AI CHAT
# ==========================
def ask_gemini(prompt):
    try:
        url = f"{GEMINI_API_URL}?key={gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"You Oxland, a helpful and friendly voice assistant from Oxbow Intellect Private Limited.\nUser: {prompt}"}
                    ]
                }
            ]
        }
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"Error: {e}"

# ==========================
# MAIN PROGRAM
# ==========================
def main():
    setup_user()

    while True:
        say("Please ask your question, or say exit to quit")
        query = input_audio()

        if query:
            query_lower = query.lower()
            print(f"❓ {user_name} asked: {query}")

            # Exit voice command
            if any(word in query_lower for word in ["exit", "quit", "stop", "bye"]):
                if current_language == "hi":
                    say("धन्यवाद, अलविदा! मैं Oxland हूँ, Oxbow Intellect Private Limited से।")
                elif current_language == "bn":
                    say("ধন্যবাদ, বিদায়! আমি Oxland, Oxbow Intellect Private Limited থেকে।")
                else:
                    say("Thank you, goodbye! I am Oxland from Oxbow Intellect Private Limited.")
                sys.exit(0)

            # Otherwise send to Gemini
            answer = ask_gemini(query)
            print(f"💡 Oxland Answer: {answer}")
            say(answer)

# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    main()
