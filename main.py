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
    "Лёгкий": 30,
    "Средний": 20,
    "Сложный": 15
}

# =====================
# БАЗА ВОПРОСОВ
# =====================

quiz_questions = [
    ("Сколько камер в сердце?", "4"),
    ("Сколько костей у взрослого человека?", "206"),
    ("Сколько лёгких у человека?", "2"),
    ("Нормальная температура тела?", "36.6"),
    ("Сколько почек у человека?", "2"),
    ("Сколько желудков у человека?", "1"),
]

# расширяем до 100+
for i in range(1, 101):
    quiz_questions.append((f"Сколько рёбер у человека? (вопрос {i})", "24"))

injection_questions = [
    ("Можно ли использовать нестерильный шприц?", "нет"),
    ("Обязательно ли соблюдать асептику?", "да"),
    ("Может ли неправильная техника вызвать осложнение?", "да"),
]

for i in range(1, 101):
    injection_questions.append(
        (f"Может ли нарушение правил инъекции привести к осложнению №{i}?", random.choice(["да", "нет"]))
    )

# =====================
# ИНИЦИАЛИЗАЦИЯ
# =====================

def init_user(user_id, username):
    users[user_id] = {
        "name": None,
        "username": username,
        "points": 0,
        "correct": 0,
        "total": 0,
        "difficulty": "Лёгкий",
        "mode": None,
        "answer": None,
        "question_time": None,
        "duel_pool": [],
        "duel_round": 0,
        "duel_score": 0
    }
    if username:
        username_to_id[username] = user_id

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎮 Викторина", "💉 Инъекции")
    markup.add("🥊 1 на 1")
    markup.add("📊 Профиль", "🎚 Сложность", "⛔ Стоп")
    return markup

# =====================
# START
# =====================

@bot.message_handler(commands=['start'])
def start(message):
    init_user(message.from_user.id, message.from_user.username)
    bot.send_message(message.chat.id, "Введите своё имя:")

@bot.message_handler(func=lambda m: m.from_user.id in users and users[m.from_user.id]["name"] is None)
def set_name(message):
    users[message.from_user.id]["name"] = message.text
    bot.send_message(message.chat.id, f"Привет, {message.text}!", reply_markup=main_menu())

# =====================
# ВОПРОСЫ
# =====================

def ask_question(user_id, pool):
    user = users[user_id]
    question = random.choice(pool)

    user["answer"] = question[1]
    user["question_time"] = time.time()

    bot.send_message(user_id, question[0])

@bot.message_handler(func=lambda m: m.text == "🎮 Викторина")
def quiz(message):
    users[message.chat.id]["mode"] = "quiz"
    ask_question(message.chat.id, quiz_questions)

@bot.message_handler(func=lambda m: m.text == "💉 Инъекции")
def injection(message):
    users[message.chat.id]["mode"] = "injection"
    ask_question(message.chat.id, injection_questions)

# =====================
# ДУЭЛЬ
# =====================

@bot.message_handler(func=lambda m: m.text == "🥊 1 на 1")
def duel_request(message):
    bot.send_message(message.chat.id, "Введите @username соперника:")

@bot.message_handler(func=lambda m: m.text.startswith("@"))
def invite(message):
    inviter = message.from_user.id
    username = message.text.replace("@", "")

    if username not in username_to_id:
        bot.send_message(inviter, "Пользователь не найден.")
        return

    opponent = username_to_id[username]
    pending_invites[opponent] = inviter

    bot.send_message(inviter, "Приглашение отправлено.")
    bot.send_message(opponent, "Вас вызвали на дуэль.\nНапишите: принять")

@bot.message_handler(func=lambda m: m.text.lower() == "принять")
def accept(message):
    opponent = message.from_user.id

    if opponent not in pending_invites:
        return

    inviter = pending_invites.pop(opponent)

    active_duels[inviter] = opponent
    active_duels[opponent] = inviter

    duel_pool = quiz_questions + injection_questions
    random.shuffle(duel_pool)

    users[inviter]["duel_pool"] = duel_pool[:10]
    users[opponent]["duel_pool"] = duel_pool[:10]

    users[inviter]["duel_round"] = 0
    users[opponent]["duel_round"] = 0
    users[inviter]["duel_score"] = 0
    users[opponent]["duel_score"] = 0

    bot.send_message(inviter, "🔥 Дуэль началась!")
    bot.send_message(opponent, "🔥 Дуэль началась!")

    next_duel_question(inviter)
    next_duel_question(opponent)

def next_duel_question(user_id):
    user = users[user_id]

    if user["duel_round"] >= 10:
        finish_duel(user_id)
        return

    question = user["duel_pool"][user["duel_round"]]
    user["duel_round"] += 1
    user["answer"] = question[1]
    user["question_time"] = time.time()

    bot.send_message(user_id, f"Раунд {user['duel_round']}/10\n{question[0]}")

def finish_duel(user_id):
    opponent = active_duels.get(user_id)
    if not opponent:
        return

    score1 = users[user_id]["duel_score"]
    score2 = users[opponent]["duel_score"]

    if score1 > score2:
        bot.send_message(user_id, "🏆 Победа!")
        bot.send_message(opponent, "❌ Поражение.")
    elif score2 > score1:
        bot.send_message(opponent, "🏆 Победа!")
        bot.send_message(user_id, "❌ Поражение.")
    else:
        bot.send_message(user_id, "🤝 Ничья.")
        bot.send_message(opponent, "🤝 Ничья.")

    active_duels.pop(user_id, None)
    active_duels.pop(opponent, None)

# =====================
# ПРОФИЛЬ
# =====================

@bot.message_handler(func=lambda m: m.text == "📊 Профиль")
def profile(message):
    user = users[message.chat.id]
    bot.send_message(message.chat.id,
                     f"Имя: {user['name']}\nОчки: {user['points']}\nВерных: {user['correct']}/{user['total']}")

# =====================
# СЛОЖНОСТЬ
# =====================

@bot.message_handler(func=lambda m: m.text == "🎚 Сложность")
def difficulty(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Лёгкий", "Средний", "Сложный")
    bot.send_message(message.chat.id, "Выберите уровень:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in difficulty_settings)
def set_difficulty(message):
    users[message.chat.id]["difficulty"] = message.text
    bot.send_message(message.chat.id, "Сложность изменена.", reply_markup=main_menu())

# =====================
# СТОП
# =====================

@bot.message_handler(func=lambda m: m.text == "⛔ Стоп")
def stop(message):
    users[message.chat.id]["mode"] = None
    users[message.chat.id]["answer"] = None
    bot.send_message(message.chat.id, "Режим остановлен.")

# =====================
# ОБРАБОТКА ОТВЕТОВ
# =====================

@bot.message_handler(func=lambda m: True)
def answer_handler(message):
    user_id = message.from_user.id

    if user_id not in users:
        return

    user = users[user_id]

    if not user["answer"]:
        return

    if time.time() - user["question_time"] > difficulty_settings[user["difficulty"]]:
        bot.send_message(user_id, f"⏳ Время вышло!\nОтвет: {user['answer']}")
        user["answer"] = None
        return

    user["total"] += 1

    if message.text.lower() == user["answer"]:
        bot.send_message(user_id, "🔥 Верно!")
        user["correct"] += 1
        user["points"] += 10

        if user_id in active_duels:
            user["duel_score"] += 1
    else:
        bot.send_message(user_id, f"❌ Неверно.\nОтвет: {user['answer']}")

    user["answer"] = None

    if user_id in active_duels:
        next_duel_question(user_id)
    elif user["mode"] == "quiz":
        ask_question(user_id, quiz_questions)
    elif user["mode"] == "injection":
        ask_question(user_id, injection_questions)

bot.infinity_polling(skip_pending=True)
