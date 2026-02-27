import os
import telebot
from telebot import types
import random

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

users = {}

# 🔥 100+ медицинских вопросов
quiz_questions = []

base_questions = [
("Сколько костей у взрослого человека?", "206", "У взрослого человека 206 костей."),
("Нормальная температура тела?", "36.6", "Средняя норма — 36.6°C."),
("Сколько камер в сердце?", "4", "В сердце 4 камеры."),
("Сколько лёгких у человека?", "2", "У человека два лёгких."),
("Сколько зубов у взрослого человека?", "32", "У взрослого человека 32 зуба."),
("Самый большой орган человека?", "Кожа", "Кожа — самый большой орган."),
("Какой орган фильтрует кровь?", "Почки", "Почки очищают кровь."),
("Где вырабатывается инсулин?", "Поджелудочная железа", "Инсулин вырабатывается в поджелудочной железе."),
("Главный орган нервной системы?", "Мозг", "Мозг управляет всем организмом."),
("Сколько литров крови в среднем у человека?", "5", "В среднем около 5 литров крови."),
]

# создаём 100 вопросов автоматически
for i in range(10):
    for q in base_questions:
        quiz_questions.append({
            "q": q[0],
            "a": q[1],
            "e": q[2]
        })

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Викторина")
    markup.add("Профиль")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {
        "points": 0,
        "remaining": random.sample(quiz_questions, len(quiz_questions))
    }

    bot.send_message(
        message.chat.id,
        "🩺 Мега Медицинский Бот\n\nВыберите раздел:",
        reply_markup=main_menu()
    )

def send_question(chat_id, user_id):
    if not users[user_id]["remaining"]:
        users[user_id]["remaining"] = random.sample(quiz_questions, len(quiz_questions))

    question = users[user_id]["remaining"].pop()
    users[user_id]["current"] = question

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Следующий вопрос")
    markup.add("Назад")

    bot.send_message(chat_id, question["q"], reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Викторина")
def quiz(message):
    user_id = message.from_user.id
    if user_id not in users:
        start(message)
    send_question(message.chat.id, user_id)

@bot.message_handler(func=lambda message: message.text == "Профиль")
def profile(message):
    user_id = message.from_user.id
    points = users.get(user_id, {}).get("points", 0)
    bot.send_message(message.chat.id, f"🏆 Очки: {points}")

@bot.message_handler(func=lambda message: True)
def handle(message):
    user_id = message.from_user.id
    text = message.text.lower()

    if text == "назад":
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=main_menu())
        return

    if text == "следующий вопрос":
        send_question(message.chat.id, user_id)
        return

    # Проверка викторины
    if user_id in users and "current" in users[user_id]:
        question = users[user_id]["current"]
        correct = question["a"].lower()

        if text == correct:
            users[user_id]["points"] += 10
            bot.send_message(
                message.chat.id,
                f"✅ Правильно!\n\n+10 очков\n\n📖 {question['e']}"
            )
        else:
            bot.send_message(
                message.chat.id,
                f"❌ Неправильно\n\nПравильный ответ: {question['a']}\n\n📖 {question['e']}"
            )

        send_question(message.chat.id, user_id)
        return

    # 🧠 Ответы на свободные медицинские вопросы
    medical_knowledge = {
        "сколько органов у человека": "В организме человека около 78 органов.",
        "что такое инсульт": "Инсульт — это нарушение кровообращения мозга.",
        "что такое инфаркт": "Инфаркт — это некроз ткани из-за недостатка кровоснабжения.",
        "что такое давление": "Артериальное давление — это давление крови на стенки сосудов.",
        "симптомы гриппа": "Температура, кашель, слабость, боль в мышцах."
    }

    for key in medical_knowledge:
        if key in text:
            bot.send_message(message.chat.id, medical_knowledge[key])
            return

    bot.send_message(message.chat.id, "🤖 Я могу отвечать на медицинские вопросы или проводить викторину.")

bot.infinity_polling(skip_pending=True)
