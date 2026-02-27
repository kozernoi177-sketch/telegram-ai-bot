import os
import telebot
import random

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище игроков (в памяти)
users = {}

questions = [
    {"q": "Сколько будет 7 × 8?", "a": "56"},
    {"q": "Столица Франции?", "a": "Париж"},
    {"q": "Сколько дней в неделе?", "a": "7"},
]

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {"points": 0, "level": 1}
    bot.reply_to(message,
        "Добро пожаловать в игру 🎮\n\n"
        "/quiz — вопрос\n"
        "/profile — твой профиль"
    )

@bot.message_handler(commands=['profile'])
def profile(message):
    user_id = message.from_user.id
    if user_id in users:
        data = users[user_id]
        bot.reply_to(message,
            f"🏆 Уровень: {data['level']}\n"
            f"💰 Очки: {data['points']}"
        )
    else:
        bot.reply_to(message, "Нажми /start")

@bot.message_handler(commands=['quiz'])
def quiz(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.reply_to(message, "Нажми /start")
        return

    question = random.choice(questions)
    users[user_id]["current_answer"] = question["a"]
    bot.reply_to(message, question["q"])

@bot.message_handler(func=lambda message: True)
def handle_answer(message):
    user_id = message.from_user.id

    if user_id in users and "current_answer" in users[user_id]:
        correct = users[user_id]["current_answer"]

        if message.text.lower() == correct.lower():
            users[user_id]["points"] += 10
            bot.reply_to(message, "Правильно 🔥 +10 очков")

            # Повышение уровня
            if users[user_id]["points"] >= 50:
                users[user_id]["level"] += 1
                users[user_id]["points"] = 0
                bot.reply_to(message, "🎉 Новый уровень!")

        else:
            bot.reply_to(message, "Неправильно 😅")

        del users[user_id]["current_answer"]

bot.infinity_polling(skip_pending=True)
