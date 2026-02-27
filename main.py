import os
import telebot
import requests
import time

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
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": message.text}
                ]
            }
        )

        result = response.json()

        if "choices" in result:
            answer = result["choices"][0]["message"]["content"]
        else:
            answer = f"API Error: {result}"

        bot.reply_to(message, answer)

    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

print("Bot started...")

while True:
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Polling error: {e}")
        time.sleep(5)
