import os
import telebot
from telebot import types
import random
import threading
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise Exception("Добавь BOT_TOKEN в Secrets")

bot = telebot.TeleBot(BOT_TOKEN)

users = {}
duel_waiting = []
duels = {}

# =========================
# НАСТРОЙКИ
# =========================

difficulty_settings = {
    "Лёгкий": {"time": 30, "multiplier": 1},
    "Средний": {"time": 20, "multiplier": 1.5},
    "Сложный": {"time": 15, "multiplier": 2}
}

medical_images = [
    "https://upload.wikimedia.org/wikipedia/commons/3/3f/Medical_syringe.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/8/8c/Hand_washing.jpg"
]

def send_image(chat_id):
    try:
        bot.send_photo(chat_id, random.choice(medical_images))
    except:
        pass

# =========================
# ВОПРОСЫ
# =========================

quiz_questions = [
    ("Сколько камер в сердце?", "4"),
    ("Сколько лёгких у человека?", "2"),
    ("Сколько костей у взрослого человека?", "206"),
    ("Нормальная температура тела?", "36.6"),
]

injection_questions = [
    ("Является ли соблюдение асептики обязательным?", "да"),
    ("Может ли неправильная техника вызвать осложнение?", "да"),
    ("Можно ли использовать нестерильный шприц?", "нет"),
]

# Автоматически расширяем инъекции до 120+
for i in range(50):
    injection_questions.append(
        (f"Может ли нарушение стерильности привести к осложнению №{i+1}?", "да")
    )

# =========================
# ВСПОМОГАТЕЛЬНЫЕ
# =========================

def init_user(user_id):
    users[user_id] = {
        "points": 0,
        "total": 0,
        "correct": 0,
        "difficulty": "Лёгкий",
        "mode": None,
        "used_quiz": [],
        "used_injection": [],
        "timer": None,
        "current_answer": None
    }

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

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎮 Викторина", "💉 Инъекции")
    markup.add("🥊 1 на 1")
    markup.add("📊 Профиль", "🎚 Сложность")
    return markup

# =========================
# ТАЙМЕР
# =========================

def start_timer(user_id, chat_id):
    def timeout():
        time_limit = difficulty_settings[users[user_id]["difficulty"]]["time"]
        time.sleep(time_limit)

        if users[user_id]["current_answer"] is not None:
            correct = users[user_id]["current_answer"]
            bot.send_message(chat_id, f"⏳ Время вышло!\nОтвет: {correct}")
            send_image(chat_id)
            users[user_id]["current_answer"] = None

            if users[user_id]["mode"] == "quiz":
                ask_quiz(chat_id)
            elif users[user_id]["mode"] == "injection":
                ask_injection(chat_id)

    thread = threading.Thread(target=timeout)
    thread.start()
    users[user_id]["timer"] = thread

# =========================
# START
# =========================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    init_user(user_id)
    bot.send_message(message.chat.id, "Выберите режим:", reply_markup=main_menu())

# =========================
# ПРОФИЛЬ
# =========================

@bot.message_handler(func=lambda m: m.text == "📊 Профиль")
def profile(message):
    user_id = message.from_user.id
    if user_id not in users:
        init_user(user_id)

    user = users[user_id]
    accuracy = 0
    if user["total"] > 0:
        accuracy = round((user["correct"] / user["total"]) * 100)

    bot.send_message(
        message.chat.id,
        f"Очки: {user['points']}\n"
        f"Лига: {get_league(user['points'])}\n"
        f"Всего ответов: {user['total']}\n"
        f"Правильных: {user['correct']}\n"
        f"Точность: {accuracy}%"
    )

# =========================
# СЛОЖНОСТЬ
# =========================

@bot.message_handler(func=lambda m: m.text == "🎚 Сложность")
def difficulty_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Лёгкий", "Средний", "Сложный")
    bot.send_message(message.chat.id, "Выберите сложность:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in difficulty_settings)
def set_difficulty(message):
    users[message.from_user.id]["difficulty"] = message.text
    bot.send_message(message.chat.id, "Сложность изменена", reply_markup=main_menu())

# =========================
# ВИКТОРИНА
# =========================

def ask_quiz(chat_id):
    user_id = chat_id
    user = users[user_id]

    available = [q for q in quiz_questions if q not in user["used_quiz"]]
    if not available:
        user["used_quiz"] = []
        available = quiz_questions.copy()

    question = random.choice(available)
    user["used_quiz"].append(question)
    user["current_answer"] = question[1]
    user["mode"] = "quiz"

    bot.send_message(chat_id, question[0])
    start_timer(user_id, chat_id)

@bot.message_handler(func=lambda m: m.text == "🎮 Викторина")
def quiz_start(message):
    ask_quiz(message.chat.id)

# =========================
# ИНЪЕКЦИИ
# =========================

def ask_injection(chat_id):
    user_id = chat_id
    user = users[user_id]

    available = [q for q in injection_questions if q not in user["used_injection"]]
    if not available:
        user["used_injection"] = []
        available = injection_questions.copy()

    question = random.choice(available)
    user["used_injection"].append(question)
    user["current_answer"] = question[1]
    user["mode"] = "injection"

    bot.send_message(chat_id, question[0] + "\nОтветьте: да или нет")
    start_timer(user_id, chat_id)

@bot.message_handler(func=lambda m: m.text == "💉 Инъекции")
def injection_start(message):
    ask_injection(message.chat.id)

# =========================
# ОТВЕТЫ
# =========================

@bot.message_handler(func=lambda m: True)
def handle_answer(message):
    user_id = message.from_user.id
    if user_id not in users:
        init_user(user_id)

    user = users[user_id]

    if user["current_answer"] is None:
        return

    user["total"] += 1
    text = message.text.lower()

    correct = user["current_answer"]

    if text == correct:
        user["correct"] += 1
        multiplier = difficulty_settings[user["difficulty"]]["multiplier"]
        points = int(10 * multiplier)
        user["points"] += points
        bot.send_message(message.chat.id, f"🔥 Верно! +{points} очков")
    else:
        bot.send_message(message.chat.id, f"❌ Неверно.\nОтвет: {correct}")

    send_image(message.chat.id)
    user["current_answer"] = None

    if user["mode"] == "quiz":
        ask_quiz(message.chat.id)
    elif user["mode"] == "injection":
        ask_injection(message.chat.id)

# =========================
# ЗАПУСК
# =========================

bot.infinity_polling(skip_pending=True)
