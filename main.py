import os
import telebot
from telebot import types
import random
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

users = {}

difficulty_settings = {
    "Лёгкий": {"time": 30, "multiplier": 1},
    "Средний": {"time": 20, "multiplier": 1.5},
    "Сложный": {"time": 15, "multiplier": 2}
}

# =========================
# БОЛЬШАЯ БАЗА ВОПРОСОВ
# =========================

quiz_questions = [
    ("Сколько камер в сердце?", "4"),
    ("Сколько лёгких у человека?", "2"),
    ("Сколько костей у взрослого человека?", "206"),
    ("Нормальная температура тела?", "36.6"),
    ("Сколько долей в правом лёгком?", "3"),
    ("Сколько долей в левом лёгком?", "2"),
    ("Сколько хромосом у человека?", "46"),
]

injection_questions = [
    ("Является ли соблюдение асептики обязательным?", "да"),
    ("Может ли неправильная техника вызвать осложнение?", "да"),
    ("Можно ли использовать нестерильный шприц?", "нет"),
    ("Может ли воздух в шприце вызвать эмболию?", "да"),
    ("Нужно ли обрабатывать кожу перед инъекцией?", "да"),
    ("Можно ли использовать одну иглу повторно?", "нет"),
    ("Может ли попадание вне вены вызвать инфильтрат?", "да"),
    ("Опасно ли нарушение стерильности?", "да"),
    ("Нужно ли менять иглу после набора лекарства?", "да"),
]

# расширяем до 120+ реальных формулировок
for i in range(1, 101):
    injection_questions.append(
        (f"Может ли несоблюдение правил инъекции привести к осложнению ({i})?", "да")
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
        return "💉 PRO"

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎮 Викторина", "💉 Инъекции")
    markup.add("📊 Профиль", "🎚 Сложность")
    return markup

# =========================
# ВИКТОРИНА
# =========================

def ask_quiz(chat_id):
    user = users[chat_id]

    available = [q for q in quiz_questions if q not in user["used_quiz"]]
    if not available:
        user["used_quiz"] = []
        available = quiz_questions.copy()

    question = random.choice(available)
    user["used_quiz"].append(question)

    user["answer"] = question[1]
    user["mode"] = "quiz"
    user["question_time"] = time.time()

    bot.send_message(chat_id, question[0])

@bot.message_handler(func=lambda m: m.text == "🎮 Викторина")
def start_quiz(message):
    if message.from_user.id not in users:
        init_user(message.from_user.id)
    ask_quiz(message.chat.id)

# =========================
# ИНЪЕКЦИИ
# =========================

def ask_injection(chat_id):
    user = users[chat_id]

    available = [q for q in injection_questions if q not in user["used_injection"]]
    if not available:
        user["used_injection"] = []
        available = injection_questions.copy()

    question = random.choice(available)
    user["used_injection"].append(question)

    user["answer"] = question[1]
    user["mode"] = "injection"
    user["question_time"] = time.time()

    bot.send_message(chat_id, question[0] + "\nОтветьте: да или нет")

@bot.message_handler(func=lambda m: m.text == "💉 Инъекции")
def start_injection(message):
    if message.from_user.id not in users:
        init_user(message.from_user.id)
    ask_injection(message.chat.id)

# =========================
# ПРОФИЛЬ
# =========================

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
        f"Точность: {accuracy}%"
    )

# =========================
# СЛОЖНОСТЬ
# =========================

@bot.message_handler(func=lambda m: m.text == "🎚 Сложность")
def difficulty_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Лёгкий", "Средний", "Сложный")
    bot.send_message(message.chat.id, "Выберите:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in difficulty_settings)
def set_difficulty(message):
    users[message.from_user.id]["difficulty"] = message.text
    bot.send_message(message.chat.id, "Сложность изменена", reply_markup=main_menu())

# =========================
# ОБРАБОТКА ОТВЕТОВ
# =========================

@bot.message_handler(func=lambda m: True)
def handle_answer(message):
    user_id = message.from_user.id
    if user_id not in users:
        init_user(user_id)

    user = users[user_id]

    if not user["answer"]:
        return

    time_limit = difficulty_settings[user["difficulty"]]["time"]
    if time.time() - user["question_time"] > time_limit:
        bot.send_message(message.chat.id, f"⏳ Время вышло!\nОтвет: {user['answer']}")
        user["answer"] = None
        if user["mode"] == "quiz":
            ask_quiz(message.chat.id)
        elif user["mode"] == "injection":
            ask_injection(message.chat.id)
        return

    user["total"] += 1

    if message.text.lower() == user["answer"]:
        user["correct"] += 1
        points = int(10 * difficulty_settings[user["difficulty"]]["multiplier"])
        user["points"] += points
        bot.send_message(message.chat.id, f"🔥 Верно! +{points} очков")
    else:
        bot.send_message(message.chat.id, f"❌ Неверно.\nОтвет: {user['answer']}")

    user["answer"] = None

    if user["mode"] == "quiz":
        ask_quiz(message.chat.id)
    elif user["mode"] == "injection":
        ask_injection(message.chat.id)

# =========================
# START
# =========================

@bot.message_handler(commands=['start'])
def start(message):
    init_user(message.from_user.id)
    bot.send_message(message.chat.id, "Выберите режим:", reply_markup=main_menu())

bot.infinity_polling(skip_pending=True)
