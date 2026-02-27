import os
import telebot
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        payload = {
            "inputs": "Ответь на русском языке: " + message.text
        }

        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        result = response.json()

        if isinstance(result, list):
            answer = result[0]["generated_text"]
        else:
            answer = str(result)

    except Exception as e:
        answer = f"Ошибка: {e}"

    bot.reply_to(message, answer)

bot.infinity_polling(skip_pending=True)
