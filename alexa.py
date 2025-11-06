# -------------------------------
# 🧠 Imports
# -------------------------------
import whisper
import openai
import requests
import re
import os
import time
import speech_recognition as sr
from gtts import gTTS
from pygame import mixer

# -------------------------------
# 🔑 API Keys
# -------------------------------
openai.api_key = ""
OWM_API_KEY = ""

# -------------------------------
# ⚙️ Load Whisper model
# -------------------------------
print("⏳ Loading Whisper model...")
whisper_model = whisper.load_model("base")
print("✅ Whisper loaded.")

# -------------------------------
# 🧩 Helper functions
# -------------------------------
def detect_question_type(question):
    question = question.lower()
    if any(word in question for word in ["weather", "temperature", "rain", "forecast"]):
        return "weather"
    return "general"

def extract_city(question):
    city_match = re.search(
        r"in ([A-Za-z ]+?)(?: right now| currently| today|\?|$)", 
        question, 
        re.IGNORECASE
    )
    if city_match:
        return city_match.group(1).strip()
    return None

def get_current_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OWM_API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200 and "main" in data:
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        return f"The current temperature in {city.title()} is {temp}°C with {desc}."
    else:
        return f"Error: {data.get('message', 'Unknown error')}"

def ask_gpt(question):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content.strip()

# -------------------------------
# 🎤 Main Alexa function
# -------------------------------
def alexa_listen():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("\n🎙️ Listening... (say 'Alexa' first)")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    with open("user_input.wav", "wb") as f:
        f.write(audio.get_wav_data())

    print("🧠 Transcribing...")
    result = whisper_model.transcribe("user_input.wav")
    user_text = result["text"].strip()
    print(f"🗣️ You said: {user_text}")

    # Normalize input
    normalized = user_text.lower()
    normalized_clean = re.sub(r"[^\w\s]", "", normalized)

    # Wake word required
    if "alexa" not in normalized_clean.split():
        print("👂 Wake word not detected. Ignoring.")
        return

    # Remove wake word so GPT doesn’t see it
    cleaned_question = normalized_clean.replace("alexa", "").strip()

    # Stop command
    if cleaned_question in ["stop", "exit", "quit"]:
        print("🛑 Stop command detected.")
        return "stop"

    # 🌦 Weather or general
    q_type = detect_question_type(cleaned_question)

    if q_type == "weather":
        city = extract_city(cleaned_question)
        if not city:
            reply = "Sorry, I could not detect the city."
        else:
            reply = get_current_weather(city)
    else:
        print("🤖 Asking GPT...")
        reply = ask_gpt(cleaned_question)

    # Speak reply
    print(f"💬 Alexa: {reply}")
    tts = gTTS(reply)
    tts.save("alexa_reply.mp3")

    mixer.init()
    mixer.music.load("alexa_reply.mp3")
    mixer.music.play()
    while mixer.music.get_busy():
        time.sleep(0.2)

    return reply

# -------------------------------
# 🚀 Alexa Loop
# -------------------------------
print("🟢 Alexa is ready! Say: 'Alexa ...'")

while True:
    result = alexa_listen()
    if result == "stop":
        print("👋 Goodbye!")
        break
