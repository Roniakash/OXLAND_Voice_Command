import os
import tempfile
import uuid
from gtts import gTTS
import pygame
import datetime
import sys
import webbrowser
import speech_recognition as sr

# ==========================
# CONFIG (Languages + Tabs)
# ==========================
LANGUAGES = {
    "en": {
        "name": "English",
        "texts": {
            "welcome": "Welcome to Oxland.",
            "select_lang": "Please select your language: English, Hindi, or Bengali.",
            "ask_name": "What is your name?",
            "morning": "Good morning {name}, welcome to Oxland.",
            "afternoon": "Good afternoon {name}, welcome to Oxland.",
            "evening": "Good evening {name}, welcome to Oxland.",
            "again": "Do you want to open another page?",
            "quit": "Goodbye {name}, have a great day!",
            "company": "Our company name is Oxbow Intellect Private Limited.",
            "assistant": "I am Oxland, your assistant."
        },
        "tabs": {
            "dashboard": "http://209.209.40.144:3031/",
            "locations": "http://209.209.40.144:3031/locations",
            "projects": "http://209.209.40.144:3031/projects",
            "analytics": "http://209.209.40.144:3031/analytics",
            "land acquisition": "http://209.209.40.144:3031/land-acquisition",
            "plot management": "http://209.209.40.144:3031/plot-management",
            "document search": "http://209.209.40.144:3031/document-search",
            "r & r": "http://209.209.40.144:3031/r-r",
            "litigation & court cases": "http://209.209.40.144:3031/litigation-court-cases",
            "land aggregator": "http://209.209.40.144:3031/land-aggregator",
            "agriculture": "http://209.209.40.144:3031/agriculture",
            "land use & land cover": "http://209.209.40.144:3031/land-use-cover",
            "forest land": "http://209.209.40.144:3031/forest-land",
            "faqs": "http://209.209.40.144:3031/faq",
            "master data": "http://209.209.40.144:3031/master-data",
            "imports": "http://209.209.40.144:3031/imports",
            "settings": "http://209.209.40.144:3031/settings"
        }
    },
    "hi": {
        "name": "Hindi",
        "texts": {
            "welcome": "ऑक्सलैंड में आपका स्वागत है।",
            "select_lang": "कृपया अपनी भाषा चुनें: अंग्रेज़ी, हिंदी, या बंगाली।",
            "ask_name": "आपका नाम क्या है?",
            "morning": "शुभ प्रभात {name}, ऑक्सलैंड में आपका स्वागत है।",
            "afternoon": "शुभ दोपहर {name}, ऑक्सलैंड में आपका स्वागत है।",
            "evening": "शुभ संध्या {name}, ऑक्सलैंड में आपका स्वागत है।",
            "again": "क्या आप एक और पेज खोलना चाहते हैं?",
            "quit": "अलविदा {name}, आपका दिन शुभ हो!",
            "company": "हमारी कंपनी का नाम ऑक्सबो इंटेलेक्ट प्राइवेट लिमिटेड है।",
            "assistant": "मैं ऑक्सलैंड हूँ, आपका सहायक।"
        },
        "tabs": {
            "डैशबोर्ड": "http://209.209.40.144:3031/",
            "स्थान": "http://209.209.40.144:3031/locations",
            "परियोजनाएं": "http://209.209.40.144:3031/projects",
            "विश्लेषण": "http://209.209.40.144:3031/analytics",
            "भूमि अधिग्रहण": "http://209.209.40.144:3031/land-acquisition",
            "प्लॉट प्रबंधन": "http://209.209.40.144:3031/plot-management",
            "दस्तावेज़ खोज": "http://209.209.40.144:3031/document-search",
            "आर एंड आर": "http://209.209.40.144:3031/r-r",
            "विवाद और अदालत के मामले": "http://209.209.40.144:3031/litigation-court-cases",
            "भूमि एग्रीगेटर": "http://209.209.40.144:3031/land-aggregator",
            "कृषि": "http://209.209.40.144:3031/agriculture",
            "भूमि उपयोग और भूमि आवरण": "http://209.209.40.144:3031/land-use-cover",
            "वन भूमि": "http://209.209.40.144:3031/forest-land",
            "सामान्य प्रश्न": "http://209.209.40.144:3031/faq",
            "मास्टर डेटा": "http://209.209.40.144:3031/master-data",
            "आयात": "http://209.209.40.144:3031/imports",
            "सेटिंग्स": "http://209.209.40.144:3031/settings"
        }
    },
    "bn": {
        "name": "Bengali",
        "texts": {
            "welcome": "অক্সল্যান্ডে আপনাকে স্বাগতম।",
            "select_lang": "দয়া করে আপনার ভাষা নির্বাচন করুন: ইংরেজি, হিন্দি, বা বাংলা।",
            "ask_name": "আপনার নাম কি?",
            "morning": "শুভ সকাল {name}, অক্সল্যান্ডে আপনাকে স্বাগতম।",
            "afternoon": "শুভ অপরাহ্ন {name}, অক্সল্যান্ডে আপনাকে স্বাগতম।",
            "evening": "শুভ সন্ধ্যা {name}, অক্সল্যান্ডে আপনাকে স্বাগতম।",
            "again": "আপনি কি আরেকটি পেজ খুলতে চান?",
            "quit": "বিদায় {name}, আপনার দিনটি শুভ হোক!",
            "company": "আমাদের কোম্পানির নাম অক্সবো ইন্টেলেক্ট প্রাইভেট লিমিটেড।",
            "assistant": "আমি অক্সল্যান্ড, আপনার সহকারী।"
        },
        "tabs": {
            "ড্যাশবোর্ড": "http://209.209.40.144:3031/",
            "অবস্থান": "http://209.209.40.144:3031/locations",
            "প্রকল্পসমূহ": "http://209.209.40.144:3031/projects",
            "বিশ্লেষণ": "http://209.209.40.144:3031/analytics",
            "জমি অধিগ্রহণ": "http://209.209.40.144:3031/land-acquisition",
            "প্লট ব্যবস্থাপনা": "http://209.209.40.144:3031/plot-management",
            "ডকুমেন্ট অনুসন্ধান": "http://209.209.40.144:3031/document-search",
            "আর অ্যান্ড আর": "http://209.209.40.144:3031/r-r",
            "মামলা ও আদালতের বিষয়": "http://209.209.40.144:3031/litigation-court-cases",
            "জমি সংযোজক": "http://209.209.40.144:3031/land-aggregator",
            "কৃষি": "http://209.209.40.144:3031/agriculture",
            "ভূমি ব্যবহার ও ভূমি আচ্ছাদন": "http://209.209.40.144:3031/land-use-cover",
            "বনের জমি": "http://209.209.40.144:3031/forest-land",
            "প্রশ্নোত্তর": "http://209.209.40.144:3031/faq",
            "মাস্টার ডেটা": "http://209.209.40.144:3031/master-data",
            "আমদানি": "http://209.209.40.144:3031/imports",
            "সেটিংস": "http://209.209.40.144:3031/settings"
        }
    }
}

# ==========================
# GLOBAL STATE
# ==========================
current_language = "en"
user_name = "User"

# ==========================
# TEXT TO SPEECH
# ==========================
def say(text, lang=None):
    global current_language
    if lang is None:
        lang = current_language
    print(f"🗣 {text}")
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
    r = sr.Recognizer()
    lang_map = {"en": "en-IN", "hi": "hi-IN", "bn": "bn-IN"}
    language_code = lang_map.get(current_language, "en-IN")
    while True:
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=1)
                r.pause_threshold = 0.8
                r.energy_threshold = 300
                print("🎤 Listening...")
                audio = r.listen(source, timeout=None, phrase_time_limit=8)
            try:
                query = r.recognize_google(audio, language=language_code)
                print(f"📝 Recognized: {query}")
                return query.lower()
            except sr.UnknownValueError:
                say("Sorry, I didn't catch that. Please speak again.", current_language)
            except sr.RequestError as e:
                print("Google Speech Recognition service error:", e)
                say("There is a problem with the speech service.", current_language)
                return ""
        except Exception as e:
            print("Microphone error:", e)

# ==========================
# WISH FUNCTION
# ==========================
def wish_user():
    hour = datetime.datetime.now().hour
    texts = LANGUAGES[current_language]["texts"]
    if hour < 12:
        say(texts["morning"].format(name=user_name))
    elif hour < 17:
        say(texts["afternoon"].format(name=user_name))
    else:
        say(texts["evening"].format(name=user_name))

# ==========================
# FLOW FUNCTIONS
# ==========================
def welcome_message():
    say(LANGUAGES["en"]["texts"]["welcome"], "en")

def select_language():
    global current_language
    say(LANGUAGES["en"]["texts"]["select_lang"], "en")
    response = input_audio()
    if "hindi" in response or "हिंदी" in response:
        current_language = "hi"
    elif "bengali" in response or "bangla" in response or "বাংলা" in response:
        current_language = "bn"
    else:
        current_language = "en"
    say(f"Language set to {LANGUAGES[current_language]['name']}", current_language)

def ask_name():
    global user_name
    say(LANGUAGES[current_language]["texts"]["ask_name"], current_language)
    response = input_audio()
    if response:
        user_name = response.split()[0].capitalize()
    else:
        user_name = "Friend"
    say(f"{user_name}, nice to meet you!", current_language)

def open_tabs_loop():
    # Speak tab selection prompt once in selected language
    tab_prompt_text = {
        "en": "Now you can select the tab.",
        "hi": "अब आप टैब चुन सकते हैं।",
        "bn": "এখন আপনি ট্যাব নির্বাচন করতে পারেন।"
    }
    say(tab_prompt_text[current_language], current_language)

    while True:
        response = input_audio()
        if not response:
            continue

        # Special cases for company or assistant
        if "company" in response or "कंपनी" in response or "কোম্পানি" in response:
            say(LANGUAGES[current_language]["texts"]["company"], current_language)
            continue
        if "oxland" in response or "ऑक्सलैंड" in response or "অক্সল্যান্ড" in response:
            say(LANGUAGES[current_language]["texts"]["assistant"], current_language)
            continue

        # Exit command
        if any(word in response for word in ["quit", "exit", "stop", "bye", "बंद", "निकास", "বন্ধ", "প্রস্থান"]):
            break

        # Open the requested tab
        matched = False
        for keyword, url in LANGUAGES[current_language]["tabs"].items():
            if keyword.lower() in response:
                webbrowser.open(url)
                say(f"Opening {keyword}", current_language)
                matched = True
                break
        if not matched:
            say("Sorry, I could not understand the page.", current_language)

        # Ask if user wants to open another page
        say(LANGUAGES[current_language]["texts"]["again"], current_language)
        again = input_audio()
        if any(word in again for word in ["no", "quit", "exit", "stop", "बंद", "निकास", "বন্ধ", "প্রস্থান"]):
            break

def quit_message():
    say(LANGUAGES[current_language]["texts"]["quit"].format(name=user_name), current_language)
    sys.exit(0)

# ==========================
# MAIN
# ==========================
def main():
    welcome_message()
    select_language()
    ask_name()
    wish_user()
    open_tabs_loop()
    quit_message()

if __name__ == "__main__":
    main()
