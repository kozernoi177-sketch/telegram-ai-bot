import os
import telebot
from telebot import types
import random
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

users = {}
duel_waiting = []
duels = {}

difficulty_settings = {
    "Лёгкий": {"time": 30, "multiplier": 1},
    "Средний": {"time": 20, "multiplier": 1.5},
    "Сложный": {"time": 15, "multiplier": 2}
}

positive_reactions = [
    "🔥 Отлично!",
    "💉 Профессионально!",
    "👏 Молодец!",
    "🏆 Так держать!"
]

# ========================
# БАЗЫ ВОПРОСОВ
# ========================

quiz_questions = [
    ("Сколько камер в сердце?", "4"),
    ("Сколько костей у взрослого человека?", "206"),
    ("Сколько лёгких у человека?", "2"),
    ("Нормальная температура тела?", "36.6"),
]

injection_questions = [
    ("Можно ли использовать нестерильный шприц?", "нет"),
    ("Может ли неправильная техника вызвать осложнение?", "да"),
    ("Является ли соблюдение асептики обязательным?", "да"),
    ("Может ли воздух в шприце вызвать эмболию?", "да"),
]

for i in range(1, 151):
    injection_questions.append(
        (f"Может ли нарушение правил инъекции привести к осложнению ({i})?", "да")
    )

# ========================
# СИСТЕМА
# ========================

def init_user(user_id):
    users[user_id] = {
        "points": 0,
        "total": 0,
        "correct": 0,
        "streak": 0,
        "difficulty": "Лёгкий",
        "mode": None,
        "used_quiz": [],
        "used_injection": [],
        "answer": None,
        "question_time": None
    }

def get_league(points):
    if points < 50:
        return "🥉 Новичок"
    elif points < 150:
        return "🥈 Ассистент"
    elif points < 300:
        return "🥇 Специалист"
    else:
        return "👑 MASTER"

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎮 Викторина", "💉 Инъекции")
    markup.add("🥊 1 на 1")
    markup.add("📊 Профиль", "🎚 Сложность", "⛔ Стоп")
    return markup

def ask_question(chat_id, mode):
    user = users[chat_id]

    if mode == "quiz":
        pool = quiz_questions
        used = user["used_quiz"]
    else:
        pool = injection_questions
        used = user["used_injection"]

    available = [q for q in pool if q not in used]
    if not available:
        used.clear()
        available = pool.copy()

    question = random.choice(available)
    used.append(question)

    user["answer"] = question[1]
    user["mode"] = mode
    user["question_time"] = time.time()

    if mode == "injection":
        bot.send_message(chat_id, question[0] + "\nОтветьте: да или нет")
    else:
        bot.send_message(chat_id, question[0])

# ========================
# КОМАНДЫ
# ========================

@bot.message_handler(commands=['start'])
def start(message):
    init_user(message.from_user.id)
    bot.send_message(message.chat.id, "Выберите режим:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🎮 Викторина")
def quiz(message):
    if message.from_user.id not in users:
        init_user(message.from_user.id)
    ask_question(message.chat.id, "quiz")

@bot.message_handler(func=lambda m: m.text == "💉 Инъекции")
def injection(message):
    if message.from_user.id not in users:
        init_user(message.from_user.id)
    ask_question(message.chat.id, "injection")

@bot.message_handler(func=lambda m: m.text == "⛔ Стоп")
def stop(message):
    users[message.from_user.id]["answer"] = None
    users[message.from_user.id]["mode"] = None
    bot.send_message(message.chat.id, "Режим остановлен.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📊 Профиль")
def profile(message):
    user = users.get(message.from_user.id)
    if not user:
        init_user(message.from_user.id)
        user = users[message.from_user.id]

    accuracy = 0
    if user["total"] > 0:
        accuracy = round(user["correct"] / user["total"] * 100)

    bot.send_message(
        message.chat.id,
        f"Очки: {user['points']}\n"
        f"Лига: {get_league(user['points'])}\n"
        f"Ответов: {user['total']}\n"
        f"Правильных: {user['correct']}\n"
        f"Серия: {user['streak']}\n"
        f"Точность: {accuracy}%"
    )

@bot.message_handler(func=lambda m: m.text == "🎚 Сложность")
def difficulty_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Лёгкий", "Средний", "Сложный")
    bot.send_message(message.chat.id, "Выберите:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in difficulty_settings)
def set_difficulty(message):
    users[message.from_user.id]["difficulty"] = message.text
    bot.send_message(message.chat.id, "Сложность изменена", reply_markup=main_menu())

# ========================
# ОТВЕТЫ
# ========================

@bot.message_handler(func=lambda m: True)
def handle_answer(message):
    user_id = message.from_user.id
    if user_id not in users:
        return

    user = users[user_id]
    if not user["answer"]:
        return

    time_limit = difficulty_settings[user["difficulty"]]["time"]

    if time.time() - user["question_time"] > time_limit:
        bot.send_message(message.chat.id, f"⏳ Время вышло!\nОтвет: {user['answer']}")
        user["streak"] = 0
        user["answer"] = None
        ask_question(message.chat.id, user["mode"])
        return

    user["total"] += 1

    if message.text.lower() == user["answer"]:
        user["correct"] += 1
        user["streak"] += 1
        points = int(10 * difficulty_settings[user["difficulty"]]["multiplier"])
        user["points"] += points
        bot.send_message(message.chat.id, random.choice(positive_reactions) + f" +{points} очков")
    else:
        user["streak"] = 0
        bot.send_message(message.chat.id, f"❌ Неверно.\nОтвет: {user['answer']}")

    user["answer"] = None
    ask_question(message.chat.id, user["mode"])

bot.infinity_polling(skip_pending=True)
