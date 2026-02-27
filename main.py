import telebot
import requests
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": message.text}
            ]
        }
    )

    result = response.json()
    answer = result["choices"][0]["message"]["content"]
    bot.reply_to(message, answer)
bot.infinity_polling()
