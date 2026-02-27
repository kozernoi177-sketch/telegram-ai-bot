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

# ===========================
# НАСТРОЙКИ
# ===========================

difficulty_settings = {
    "Лёгкий": {"time": 30, "multiplier": 1},
    "Средний": {"time": 25, "multiplier": 1.5},
    "Сложный": {"time": 15, "multiplier": 2}
}

positive_reactions = [
    "🔥 Отлично!",
    "💉 Профессионально!",
    "🧠 Гений!",
    "👏 Молодец!",
    "🏆 Так держать!"
]

medical_images = [
    "https://upload.wikimedia.org/wikipedia/commons/8/8c/Hand_washing.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/3/3f/Medical_syringe.jpg"
]

def send_image(chat_id):
    try:
        bot.send_photo(chat_id, random.choice(medical_images))
    except:
        pass

# ===========================
# ВОПРОСЫ
# ===========================

quiz_base = [
    ("Сколько камер в сердце?", "4"),
    ("Сколько лёгких у человека?", "2"),
    ("Можно ли использовать нестерильные инструменты?", "нет")
]

injection_base = [
    "Может ли нарушение стерильности привести к инфекции?",
    "Является ли соблюдение асептики обязательным?",
    "Может ли неправильная техника вызвать осложнение?"
]

duel_base = []
for i in range(50):
    duel_base.extend(quiz_base)

# ===========================
# ВСПОМОГАТЕЛЬНЫЕ
# ===========================

def get_league(points):
    if points < 50:
        return "🥉 Новичок"
    elif points < 150:
        return "🥈 Ассистент"
    elif points < 300:
        return "🥇 Специалист"
    elif points < 500:
        return "💉 PRO"
    else:
        return "👑 MASTER"

def start_timer(user_id):
    users[user_id]["start_time"] = time.time()

def is_timeout(user_id):
    diff = difficulty_settings[users[user_id]["difficulty"]]["time"]
    return time.time() - users[user_id]["start_time"] > diff

# ===========================
# МЕНЮ
# ===========================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎮 Викторина")
    markup.add("💉 Инъекции")
    markup.add("🥊 1 на 1")
    markup.add("📊 Профиль")
    markup.add("🎚 Сложность")
    return markup

# ===========================
# START
# ===========================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {
        "points": 0,
        "total": 0,
        "correct": 0,
        "difficulty": "Лёгкий",
        "mode": None
    }
    bot.send_message(message.chat.id, "Выберите режим:", reply_markup=main_menu())

# ===========================
# ПРОФИЛЬ
# ===========================

@bot.message_handler(func=lambda m: m.text == "📊 Профиль")
def profile(message):
    user = users[message.from_user.id]
    accuracy = 0
    if user["total"] > 0:
        accuracy = round((user["correct"] / user["total"]) * 100)

    bot.send_message(
        message.chat.id,
        f"Очки: {user['points']}\n"
        f"Лига: {get_league(user['points'])}\n"
        f"Всего ответов: {user['total']}\n"
        f"Правильных: {user['correct']}\n"
        f"Точность: {accuracy}%\n"
        f"Сложность: {user['difficulty']}"
    )

# ===========================
# СЛОЖНОСТЬ
# ===========================

@bot.message_handler(func=lambda m: m.text == "🎚 Сложность")
def difficulty_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Лёгкий", "Средний", "Сложный")
    bot.send_message(message.chat.id, "Выберите сложность:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in difficulty_settings)
def set_difficulty(message):
    users[message.from_user.id]["difficulty"] = message.text
    bot.send_message(message.chat.id, f"Сложность установлена: {message.text}", reply_markup=main_menu())

# ===========================
# ВИКТОРИНА
# ===========================

@bot.message_handler(func=lambda m: m.text == "🎮 Викторина")
def quiz(message):
    user_id = message.from_user.id
    users[user_id]["mode"] = "quiz"
    q, a = random.choice(quiz_base)
    users[user_id]["answer"] = a
    start_timer(user_id)

    time_limit = difficulty_settings[users[user_id]["difficulty"]]["time"]
    bot.send_message(message.chat.id, f"⏳ {time_limit} секунд\n{q}")

# ===========================
# ИНЪЕКЦИИ
# ===========================

@bot.message_handler(func=lambda m: m.text == "💉 Инъекции")
def injection(message):
    user_id = message.from_user.id
    users[user_id]["mode"] = "injection"
    q = random.choice(injection_base)
    a = random.choice(["да", "нет"])
    users[user_id]["answer"] = a
    start_timer(user_id)

    time_limit = difficulty_settings[users[user_id]["difficulty"]]["time"]
    bot.send_message(message.chat.id, f"💉 ⏳ {time_limit} секунд\n{q}\nОтветьте: да или нет")

# ===========================
# ДУЭЛЬ
# ===========================

@bot.message_handler(func=lambda m: m.text == "🥊 1 на 1")
def duel(message):
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

        send_duel_question(user_id)
        send_duel_question(opponent)
    else:
        duel_waiting.append(user_id)
        bot.send_message(user_id, "Ожидание соперника...")

def send_duel_question(user_id):
    duel = duels[user_id]

    if duel["round"] >= 10:
        bot.send_message(user_id, f"Дуэль завершена. Ваш счёт: {duel['score']}")
        return

    q, a = duel["questions"][duel["round"]]
    users[user_id]["answer"] = a
    users[user_id]["mode"] = "duel"
    duel["round"] += 1
    start_timer(user_id)

    bot.send_message(user_id, f"🥊 Раунд {duel['round']}/10\n{q}")

# ===========================
# ОБРАБОТКА ОТВЕТОВ
# ===========================

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
    users[user_id]["total"] += 1

    if is_timeout(user_id):
        bot.send_message(message.chat.id, f"⏳ Время вышло.\nОтвет: {correct}")
        send_image(message.chat.id)
        return

    if text == correct:
        users[user_id]["correct"] += 1
        multiplier = difficulty_settings[users[user_id]["difficulty"]]["multiplier"]
        points = int(10 * multiplier)
        users[user_id]["points"] += points
        bot.send_message(message.chat.id, random.choice(positive_reactions) + f" +{points} очков")
    else:
        bot.send_message(message.chat.id, f"Неправильно.\nОтвет: {correct}")

    send_image(message.chat.id)

    if users[user_id]["mode"] == "duel":
        duels[user_id]["score"] += 1 if text == correct else 0
        send_duel_question(user_id)

bot.infinity_polling(skip_pending=True)
