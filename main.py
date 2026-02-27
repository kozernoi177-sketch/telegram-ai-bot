import os
import telebot
from telebot import types
import random
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

users = {}
username_to_id = {}
pending_invites = {}
active_duels = {}

difficulty_settings = {
    "Лёгкий": {"time": 30, "multiplier": 1},
    "Средний": {"time": 20, "multiplier": 1.5},
    "Сложный": {"time": 15, "multiplier": 2}
}

# =======================
# ВОПРОСЫ
# =======================

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
]

for i in range(1, 151):
    injection_questions.append(
        (f"Может ли нарушение правил инъекции привести к осложнению ({i})?", "да")
    )

# =======================
# ИНИЦИАЛИЗАЦИЯ
# =======================

def init_user(user_id, username):
    users[user_id] = {
        "name": None,
        "username": username,
        "points": 0,
        "total": 0,
        "correct": 0,
        "difficulty": "Лёгкий",
        "mode": None,
        "used_quiz": [],
        "used_injection": [],
        "answer": None,
        "question_time": None,
        "duel_score": 0,
        "duel_round": 0
    }
    if username:
        username_to_id[username] = user_id

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎮 Викторина", "💉 Инъекции")
    markup.add("🥊 1 на 1")
    markup.add("📊 Профиль", "🎚 Сложность", "⛔ Стоп")
    return markup

# =======================
# START
# =======================

@bot.message_handler(commands=['start'])
def start(message):
    init_user(message.from_user.id, message.from_user.username)
    bot.send_message(message.chat.id, "Введите своё имя:")

@bot.message_handler(func=lambda m: m.from_user.id in users and users[m.from_user.id]["name"] is None)
def set_name(message):
    users[message.from_user.id]["name"] = message.text
    bot.send_message(message.chat.id, f"Привет, {message.text}!", reply_markup=main_menu())

# =======================
# ВИКТОРИНА / ИНЪЕКЦИИ
# =======================

def ask_question(chat_id, mode):
    user = users[chat_id]

    pool = quiz_questions if mode == "quiz" else injection_questions
    used = user["used_quiz"] if mode == "quiz" else user["used_injection"]

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

@bot.message_handler(func=lambda m: m.text == "🎮 Викторина")
def quiz(message):
    ask_question(message.chat.id, "quiz")

@bot.message_handler(func=lambda m: m.text == "💉 Инъекции")
def injection(message):
    ask_question(message.chat.id, "injection")

# =======================
# 1 НА 1
# =======================

@bot.message_handler(func=lambda m: m.text == "🥊 1 на 1")
def duel_request(message):
    bot.send_message(message.chat.id, "Введите @username соперника:")

@bot.message_handler(func=lambda m: m.text.startswith("@"))
def send_invite(message):
    inviter_id = message.from_user.id
    username = message.text.replace("@", "")

    if username not in username_to_id:
        bot.send_message(inviter_id, "Пользователь не найден или не запускал бота.")
        return

    opponent_id = username_to_id[username]

    pending_invites[opponent_id] = inviter_id

    bot.send_message(inviter_id, "Приглашение отправлено.")
    bot.send_message(opponent_id, f"{users[inviter_id]['name']} вызывает вас на дуэль!\nНапишите: принять")

@bot.message_handler(func=lambda m: m.text.lower() == "принять")
def accept_duel(message):
    opponent_id = message.from_user.id

    if opponent_id not in pending_invites:
        return

    inviter_id = pending_invites.pop(opponent_id)

    active_duels[inviter_id] = opponent_id
    active_duels[opponent_id] = inviter_id

    users[inviter_id]["duel_score"] = 0
    users[opponent_id]["duel_score"] = 0
    users[inviter_id]["duel_round"] = 0
    users[opponent_id]["duel_round"] = 0

    bot.send_message(inviter_id, "Дуэль началась! 10 раундов.")
    bot.send_message(opponent_id, "Дуэль началась! 10 раундов.")

    start_duel_round(inviter_id)
    start_duel_round(opponent_id)

def start_duel_round(user_id):
    if users[user_id]["duel_round"] >= 10:
        finish_duel(user_id)
        return

    question = random.choice(quiz_questions)

    users[user_id]["answer"] = question[1]
    users[user_id]["mode"] = "duel"
    users[user_id]["question_time"] = time.time()
    users[user_id]["duel_round"] += 1

    bot.send_message(user_id, f"Раунд {users[user_id]['duel_round']}/10\n{question[0]}")

def finish_duel(user_id):
    opponent_id = active_duels.get(user_id)
    if not opponent_id:
        return

    score1 = users[user_id]["duel_score"]
    score2 = users[opponent_id]["duel_score"]

    if score1 > score2:
        bot.send_message(user_id, "🏆 Вы победили!")
        bot.send_message(opponent_id, "❌ Вы проиграли.")
    elif score2 > score1:
        bot.send_message(opponent_id, "🏆 Вы победили!")
        bot.send_message(user_id, "❌ Вы проиграли.")
    else:
        bot.send_message(user_id, "🤝 Ничья!")
        bot.send_message(opponent_id, "🤝 Ничья!")

    active_duels.pop(user_id, None)
    active_duels.pop(opponent_id, None)

# =======================
# СТОП
# =======================

@bot.message_handler(func=lambda m: m.text == "⛔ Стоп")
def stop(message):
    users[message.from_user.id]["mode"] = None
    users[message.from_user.id]["answer"] = None
    bot.send_message(message.chat.id, "Режим остановлен.")

# =======================
# ОТВЕТЫ
# =======================

@bot.message_handler(func=lambda m: True)
def handle_answer(message):
    user_id = message.from_user.id
    if user_id not in users:
        return

    user = users[user_id]
    if not user["answer"]:
        return

    if time.time() - user["question_time"] > difficulty_settings[user["difficulty"]]["time"]:
        bot.send_message(message.chat.id, f"⏳ Время вышло!\nОтвет: {user['answer']}")
        user["answer"] = None
        return

    if message.text.lower() == user["answer"]:
        bot.send_message(message.chat.id, "🔥 Верно!")
        if user["mode"] == "duel":
            user["duel_score"] += 1
    else:
        bot.send_message(message.chat.id, f"❌ Неверно.\nОтвет: {user['answer']}")

    user["answer"] = None

    if user["mode"] == "duel":
        start_duel_round(user_id)
    elif user["mode"] == "quiz":
        ask_question(message.chat.id, "quiz")
    elif user["mode"] == "injection":
        ask_question(message.chat.id, "injection")

bot.infinity_polling(skip_pending=True)
