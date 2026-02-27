import os
import telebot
from telebot import types
import random

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

users = {}

quiz_questions = [
    {
        "q": "Сколько костей в теле взрослого человека?",
        "options": ["206", "230", "180", "250"],
        "answer": "206",
        "explanation": "У взрослого человека 206 костей."
    },
    {
        "q": "Нормальная температура тела?",
        "options": ["35.0", "36.6", "38.5", "34.5"],
        "answer": "36.6",
        "explanation": "Средняя норма — 36.6°C."
    },
    {
        "q": "Какой орган отвечает за перекачку крови?",
        "options": ["Печень", "Лёгкие", "Сердце", "Почки"],
        "answer": "Сердце",
        "explanation": "Сердце перекачивает кровь по организму."
    }
]

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Викторина")
    markup.add("Профиль")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {"points": 0}

    bot.send_message(
        message.chat.id,
        "🩺 Медицинский PRO бот\nВыберите раздел:",
        reply_markup=main_menu()
    )

def send_question(chat_id, user_id):
    question = random.choice(quiz_questions)
    users[user_id]["current"] = question

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for option in question["options"]:
        markup.add(option)
    markup.add("Следующий вопрос")
    markup.add("Назад")

    bot.send_message(chat_id, question["q"], reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Викторина")
def quiz(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {"points": 0}
    send_question(message.chat.id, user_id)

@bot.message_handler(func=lambda message: message.text == "Профиль")
def profile(message):
    user_id = message.from_user.id
    points = users.get(user_id, {}).get("points", 0)
    bot.send_message(message.chat.id, f"🏆 Очки: {points}")

@bot.message_handler(func=lambda message: True)
def handle_answer(message):
    user_id = message.from_user.id

    if message.text == "Назад":
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=main_menu())
        return

    if message.text == "Следующий вопрос":
        send_question(message.chat.id, user_id)
        return

    if user_id in users and "current" in users[user_id]:
        question = users[user_id]["current"]
        correct = question["answer"]

        if message.text == correct:
            users[user_id]["points"] += 10
            bot.send_message(
                message.chat.id,
                f"✅ Правильно!\n\n+10 очков\n\n📖 {question['explanation']}"
            )
        else:
            bot.send_message(
                message.chat.id,
                f"❌ Неправильно\n\nПравильный ответ: {correct}\n\n📖 {question['explanation']}"
            )

        send_question(message.chat.id, user_id)

bot.infinity_polling(skip_pending=True)
