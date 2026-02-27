import os
import telebot
from telebot import types
import random
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise Exception("Добавь BOT_TOKEN в Secrets")

bot = telebot.TeleBot(BOT_TOKEN)

users = {}
duel_waiting = []
duels = {}

# =====================================================
# МЕДИЦИНСКИЕ КАРТИНКИ (СТАБИЛЬНЫЕ JPG)
# =====================================================

medical_images = {
    "quiz": [
        "https://upload.wikimedia.org/wikipedia/commons/8/8c/Hand_washing.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/3/3f/Medical_syringe.jpg",
    ],
    "injection": [
        "https://upload.wikimedia.org/wikipedia/commons/3/3f/Medical_syringe.jpg",
    ]
}

def send_image(chat_id, category):
    try:
        bot.send_photo(chat_id, random.choice(medical_images[category]))
    except:
        pass

# =====================================================
# ВОПРОСЫ
# =====================================================

quiz_base = [
    ("Сколько камер в сердце?", "4"),
    ("Сколько лёгких у человека?", "2"),
    ("Можно ли использовать нестерильные инструменты?", "нет"),
]

injection_base = [
    "Может ли нарушение стерильности привести к инфекции?",
    "Является ли соблюдение асептики обязательным?",
    "Может ли неправильная техника вызвать осложнение?"
]

duel_base = []
for i in range(50):
    duel_base.extend([
        ("Сколько камер в сердце?", "4"),
        ("Сколько лёгких у человека?", "2"),
        ("Можно ли использовать нестерильные инструменты?", "нет"),
    ])

# =====================================================
# МЕНЮ
# =====================================================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎮 Викторина")
    markup.add("💉 Инъекции (для М)")
    markup.add("🥊 1 на 1")
    return markup

# =====================================================
# START
# =====================================================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {
        "points": 0,
        "mode": None
    }
    bot.send_message(message.chat.id, "Выберите режим:", reply_markup=main_menu())

# =====================================================
# ТАЙМЕР
# =====================================================

def start_timer(user_id):
    users[user_id]["start_time"] = time.time()

def timeout(user_id):
    if "start_time" in users[user_id]:
        return time.time() - users[user_id]["start_time"] > 30
    return False

# =====================================================
# ВИКТОРИНА
# =====================================================

@bot.message_handler(func=lambda m: m.text == "🎮 Викторина")
def quiz_start(message):
    user_id = message.from_user.id
    users[user_id]["mode"] = "quiz"

    q, a = random.choice(quiz_base)
    users[user_id]["answer"] = a
    start_timer(user_id)

    bot.send_message(message.chat.id, f"⏳ 30 секунд\n{q}")

# =====================================================
# ИНЪЕКЦИИ
# =====================================================

@bot.message_handler(func=lambda m: m.text == "💉 Инъекции (для М)")
def injection_start(message):
    user_id = message.from_user.id
    users[user_id]["mode"] = "injection"

    q = random.choice(injection_base)
    a = random.choice(["да", "нет"])

    users[user_id]["answer"] = a
    start_timer(user_id)

    bot.send_message(message.chat.id, f"💉 ⏳ 30 секунд\n{q}\nОтветьте: да или нет")

# =====================================================
# ДУЭЛЬ 1 НА 1
# =====================================================

@bot.message_handler(func=lambda m: m.text == "🥊 1 на 1")
def duel_start(message):
    user_id = message.from_user.id

    if duel_waiting:
        opponent = duel_waiting.pop()

        duels[user_id] = {
            "opponent": opponent,
            "score": 0,
            "round": 0,
            "questions": random.sample(duel_base, 10)
        }

        duels[opponent] = {
            "opponent": user_id,
            "score": 0,
            "round": 0,
            "questions": duels[user_id]["questions"]
        }

        bot.send_message(user_id, "Соперник найден!")
        bot.send_message(opponent, "Соперник найден!")

        send_duel_question(user_id)
        send_duel_question(opponent)

    else:
        duel_waiting.append(user_id)
        bot.send_message(user_id, "Ожидание соперника...")

def send_duel_question(user_id):
    duel = duels[user_id]

    if duel["round"] >= 10:
        end_duel(user_id)
        return

    q, a = duel["questions"][duel["round"]]
    users[user_id]["answer"] = a
    users[user_id]["mode"] = "duel"

    duel["round"] += 1
    start_timer(user_id)

    bot.send_message(user_id, f"🥊 Раунд {duel['round']}/10\n⏳ 30 секунд\n{q}")

def end_duel(user_id):
    duel = duels[user_id]
    opponent = duel["opponent"]

    score1 = duel["score"]
    score2 = duels[opponent]["score"]

    bot.send_message(user_id, f"Дуэль завершена.\nВаш счёт: {score1}")
    bot.send_message(opponent, f"Дуэль завершена.\nВаш счёт: {score2}")

    del duels[user_id]
    del duels[opponent]

# =====================================================
# ОБЩИЙ ОБРАБОТЧИК
# =====================================================

@bot.message_handler(func=lambda m: True)
def handle(message):
    user_id = message.from_user.id
    text = message.text.lower()

    if user_id not in users:
        start(message)
        return

    if "answer" not in users[user_id]:
        return

    correct = users[user_id]["answer"]

    if timeout(user_id):
        bot.send_message(message.chat.id, f"⏳ Время вышло.\nОтвет: {correct}")
        send_image(message.chat.id, "quiz")
        return

    if text == correct:
        bot.send_message(message.chat.id, "Правильно!")
        if users[user_id]["mode"] == "duel":
            duels[user_id]["score"] += 1
    else:
        bot.send_message(message.chat.id, f"Неправильно.\nОтвет: {correct}")

    if users[user_id]["mode"] == "quiz":
        send_image(message.chat.id, "quiz")

    if users[user_id]["mode"] == "injection":
        send_image(message.chat.id, "injection")

    if users[user_id]["mode"] == "duel":
        send_duel_question(user_id)

bot.infinity_polling(skip_pending=True)
