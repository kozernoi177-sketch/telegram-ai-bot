import os
import telebot
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistralai/mistral-7b-instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты Telegram-бот. Отвечай всегда только на русском языке."
                    },
                    {
                        "role": "user",
                        "content": message.text
                    }
                ]
            },
            timeout=30
        )

        result = response.json()

        if "choices" in result:
            answer = result["choices"][0]["message"]["content"]
        else:
            answer = f"Ошибка API: {result}"

    except Exception as e:
        answer = f"Ошибка бота: {e}"

    bot.reply_to(message, answer)

bot.infinity_polling(skip_pending=True)
