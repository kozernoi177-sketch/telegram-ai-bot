import os
import telebot
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

API_URL = "https://router.huggingface.co/hf-inference/models/HuggingFaceH4/zephyr-7b-beta"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        payload = {
            "inputs": f"<|system|>\nОтвечай всегда на русском языке.\n<|user|>\n{message.text}\n<|assistant|>"
        }

        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)

        if response.status_code != 200:
            answer = f"Ошибка API: {response.text}"
        else:
            result = response.json()
            answer = result[0]["generated_text"]

    except Exception as e:
        answer = f"Ошибка: {e}"

    bot.reply_to(message, answer)

bot.infinity_polling(skip_pending=True)
