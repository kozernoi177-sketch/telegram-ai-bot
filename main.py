import os
import telebot
from telebot import types
import random
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

users = {}
duel_queue = []
active_duels = {}

# ==========================================================
#                 МЕДИЦИНСКИЕ КАРТИНКИ
# ==========================================================

medical_images = [
    "https://upload.wikimedia.org/wikipedia/commons/8/8c/Hand_washing.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/3/3f/Medical_syringe.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/2/2e/Heart_diagram-en.svg",
    "https://upload.wikimedia.org/wikipedia/commons/1/19/Human_brain.jpg",
]

def send_random_image(chat_id):
    bot.send_photo(chat_id, random.choice(medical_images))

# ==========================================================
#                     ВИКТОРИНА
# ==========================================================

quiz_base = [
    ("Сколько камер в сердце?", "4"),
    ("Можно ли использовать нестерильные инструменты?", "Нет"),
    ("Сколько лёгких у человека?", "2"),
]

def generate_quiz():
    return random.sample(quiz_base, len(quiz_base))

# ==========================================================
#                   ИНЪЕКЦИИ
# ==========================================================

injection_templates = [
    "Может ли нарушение стерильности привести к инфекции?",
    "Является ли контроль состояния пациента важным?",
    "Может ли появиться отёк после процедуры?",
]

def generate_injection_questions():
    questions = []
    for i in range(50):
        for q in injection_templates:
            questions.append((q, random.choice(["да", "нет"])))
    return random.sample(questions, len(questions))

# ==========================================================
#                       МЕНЮ
# ==========================================================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎮 Викторина")
    markup.add("💉 Инъекции (для М)")
    markup.add("🥊 1 на 1")
    return markup

# ==========================================================
#                       START
# ==========================================================

@bot.message_handler(commands=['start'])
def start(message):
    users[message.from_user.id] = {
        "quiz": generate_quiz(),
        "injection_quiz": [],
        "points": 0
    }
    bot.send_message(message.chat.id, "Выберите режим:", reply_markup=main_menu())

# ==========================================================
#                 ТАЙМЕР ЛОГИКА
# ==========================================================

def start_timer(user_id):
    users[user_id]["question_time"] = time.time()

def check_timeout(user_id):
    if "question_time" in users[user_id]:
        if time.time() - users[user_id]["question_time"] > 30:
            return True
    return False

# ==========================================================
#                   ВИКТОРИНА
# ==========================================================

@bot.message_handler(func=lambda m: m.text == "🎮 Викторина")
def start_quiz(message):
    user_id = message.from_user.id
    if not users[user_id]["quiz"]:
        users[user_id]["quiz"] = generate_quiz()

    q, a = users[user_id]["quiz"].pop()
    users[user_id]["current_answer"] = a
    start_timer(user_id)

    bot.send_message(message.chat.id, f"⏳ 30 секунд\n{q}")

# ==========================================================
#                   ИНЪЕКЦИИ
# ==========================================================

@bot.message_handler(func=lambda m: m.text == "💉 Инъекции (для М)")
def start_injection(message):
    user_id = message.from_user.id
    users[user_id]["injection_quiz"] = generate_injection_questions()
    send_injection_question(message.chat.id, user_id)

def send_injection_question(chat_id, user_id):
    if not users[user_id]["injection_quiz"]:
        users[user_id]["injection_quiz"] = generate_injection_questions()

    q, a = users[user_id]["injection_quiz"].pop()
    users[user_id]["current_injection_answer"] = a
    start_timer(user_id)

    bot.send_message(chat_id, f"💉 ⏳ 30 секунд\n{q}\nОтветьте: да или нет")

# ==========================================================
#                   РЕЖИМ 1 НА 1
# ==========================================================

@bot.message_handler(func=lambda m: m.text == "🥊 1 на 1")
def duel_request(message):
    user_id = message.from_user.id

    if duel_queue:
        opponent = duel_queue.pop()
        active_duels[user_id] = opponent
        active_duels[opponent] = user_id

        bot.send_message(message.chat.id, "Соперник найден! Начинаем дуэль.")
        bot.send_message(opponent, "Соперник найден! Начинаем дуэль.")

        start_duel_round(user_id)
        start_duel_round(opponent)

    else:
        duel_queue.append(user_id)
        bot.send_message(message.chat.id, "Ожидание соперника...")

def start_duel_round(user_id):
    q, a = random.choice(quiz_base)
    users[user_id]["duel_answer"] = a
    start_timer(user_id)
    bot.send_message(user_id, f"
