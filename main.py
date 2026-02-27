import os
import telebot
from telebot import types
import random

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

medical_data = {
    "Головная боль": "🧠 Возможные причины: стресс, мигрень, усталость.",
    "Температура": "🌡 Чаще всего признак инфекции.",
    "Кашель": "😷 Может быть при простуде или аллергии."
}

quiz_questions = [
    {"q": "Сколько костей в теле человека?", "a": "206"},
    {"q": "Нормальная температура тела?", "a": "36.6"},
]

users = {}

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Симптомы")
    markup.add("Викторина")
    markup.add("Профиль")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {"points": 0, "level": 1}

    bot.send_message(
        message.chat.id,
        "🩺 Медицинский бот\nВыберите раздел:",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda message: message.text == "Симптомы")
def symptoms(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for key in medical_data.keys():
        markup.add(key)
    markup.add("Назад")
    bot.send_message(message.chat.id, "Выберите симптом:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in medical_data)
def symptom_answer(message):
    bot.send_message(message.chat.id, medical_data[message.text])

@bot.message_handler(func=lambda message: message.text == "Викторина")
def quiz(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {"points": 0, "level": 1}

    question = random.choice(quiz_questions)
    users[user_id]["current_answer"] = question["a"]
    bot.send_message(message.chat.id, question["q"])

@bot.message_handler(func=lambda message: message.text == "Профиль")
def profile(message):
    user_id = message.from_user.id
    data = users.get(user_id, {"points": 0, "level": 1})
    bot.send_message(
        message.chat.id,
        f"🏆 Уровень: {data['level']}\n💰 Очки: {data['points']}"
    )

@bot.message_handler(func=lambda message: True)
def handle_answer(message):
    user_id = message.from_user.id

    if user_id in users and "current_answer" in users[user_id]:
        correct = users[user_id]["current_answer"]

        if message.text.lower() == correct.lower():
            users[user_id]["points"] += 10
            bot.send_message(message.chat.id, "Правильно! +10 очков 🔥")
        else:
            bot.send_message(message.chat.id, "Неправильно 😅")

        del users[user_id]["current_answer"]

    elif message.text == "Назад":
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=main_menu())

bot.infinity_polling(skip_pending=True)
