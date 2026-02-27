import os
import telebot
from telebot import types
import random
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN не найден в Environment Variables")

bot = telebot.TeleBot(BOT_TOKEN)

users = {}
duel_queue = []
active_duels = {}

# ======================================================
# КАРТИНКИ (СТАБИЛЬНЫЕ)
# ======================================================

medical_images = [
    "https://picsum.photos/400/300",
    "https://picsum.photos/401/300",
    "https://picsum.photos/402/300",
]

def send_random_image(chat_id):
    try:
        bot.send_photo(chat_id, random.choice(medical_images))
    except:
        pass

# ======================================================
# БАЗЫ ВОПРОСОВ
# ======================================================

quiz_base = [
    ("Сколько камер в сердце?", "4"),
    ("Сколько лёгких у человека?", "2"),
    ("Можно ли использовать нестерильные инструменты?", "нет"),
]

injection_templates = [
    "Может ли нарушение стерильности привести к инфекции?",
    "Может ли неправильная техника вызвать осложнение?",
    "Является ли соблюдение асептики обязательным?",
]

# ======================================================
# ГЕНЕРАЦИЯ
# ======================================================

def generate_quiz():
    return random.sample(quiz_base, len(quiz_base))

def generate_injection():
    questions = []
    for i in range(40):
        for q in injection_templates:
            questions.append((q, random.choice(["да", "нет"])))
    return random.sample(questions, len(questions))

# ======================================================
# МЕНЮ
# ======================================================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎮 Викторина")
    markup.add("💉 Инъекции (для М)")
    markup.add("🥊 1 на 1")
    return markup

# ======================================================
# START
# ======================================================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    users[user_id] = {
        "quiz": generate_quiz(),
        "injection": [],
        "points": 0
    }

    bot.send_message(message.chat.id, "Выберите режим:", reply_markup=main_menu())

# ======================================================
# ТАЙМЕР
# ======================================================

def start_timer(user_id):
    users[user_id]["question_time"] = time.time()

def is_timeout(user_id):
    if "question_time" in users[user_id]:
        return time.time() - users[user_id]["question_time"] > 30
    return False

# ======================================================
# ВИКТОРИНА
# ======================================================

@bot.message_handler(func=lambda m: m.text == "🎮 Викторина")
def quiz_start(message):
    user_id = message.from_user.id

    if user_id not in users:
        start(message)
        return

    if not users[user_id]["quiz"]:
        users[user_id]["quiz"] = generate_quiz()

    q, a = users[user_id]["quiz"].pop()
    users[user_id]["current_answer"] = a
    start_timer(user_id)

    bot.send_message(message.chat.id, f"⏳ 30 секунд\n{q}")

# ======================================================
# ИНЪЕКЦИИ
# ======================================================

@bot.message_handler(func=lambda m: m.text == "💉 Инъекции (для М)")
def injection_start(message):
    user_id = message.from_user.id

    if user_id not in users:
        start(message)
        return

    users[user_id]["injection"] = generate_injection()

    send_injection(message.chat.id, user_id)

def send_injection(chat_id, user_id):
    if not users[user_id]["injection"]:
        users[user_id]["injection"] = generate_injection()

    q, a = users[user_id]["injection"].pop()
    users[user_id]["current_injection"] = a
    start_timer(user_id)

    bot.send_message(chat_id, f"💉 ⏳ 30 секунд\n{q}\nОтветьте: да или нет")

# ======================================================
# ДУЭЛЬ 1 НА 1
# ======================================================

@bot.message_handler(func=lambda m: m.text == "🥊 1 на 1")
def duel_start(message):
    user_id = message.from_user.id

    if user_id not in users:
        start(message)
        return

    if duel_queue:
        opponent = duel_queue.pop()
        active_duels[user_id] = opponent
        active_duels[opponent] = user_id

        bot.send_message(user_id, "Соперник найден!")
        bot.send_message(opponent, "Соперник найден!")

        send_duel_question(user_id)
        send_duel_question(opponent)
    else:
        duel_queue.append(user_id)
        bot.send_message(user_id, "Ожидание соперника...")

def send_duel_question(user_id):
    q, a = random.choice(quiz_base)
    users[user_id]["duel_answer"] = a
    start_timer(user_id)

    bot.send_message(user_id, f"🥊 ⏳ 30 секунд\n{q}")

# ======================================================
# ОБЩИЙ ОБРАБОТЧИК
# ======================================================

@bot.message_handler(func=lambda message: True)
def handle(message):
    user_id = message.from_user.id
    text = message.text.lower()

    if user_id not in users:
        start(message)
        return

    # === ТАЙМАУТ ===
    if is_timeout(user_id):

        if "current_answer" in users[user_id]:
            correct = users[user_id]["current_answer"]
            bot.send_message(message.chat.id, f"⏳ Время вышло.\nОтвет: {correct}")
            send_random_image(message.chat.id)
            del users[user_id]["current_answer"]
            return

        if "current_injection" in users[user_id]:
            correct = users[user_id]["current_injection"]
            bot.send_message(message.chat.id, f"⏳ Время вышло.\nОтвет: {correct}")
            send_random_image(message.chat.id)
            del users[user_id]["current_injection"]
            return

        if "duel_answer" in users[user_id]:
            correct = users[user_id]["duel_answer"]
            bot.send_message(message.chat.id, f"⏳ Время вышло.\nОтвет: {correct}")
            send_random_image(message.chat.id)
            del users[user_id]["duel_answer"]
            return

    # === ИНЪЕКЦИИ ===
    if "current_injection" in users[user_id]:
        correct = users[user_id]["current_injection"]

        if text == correct:
            bot.send_message(message.chat.id, "Умница.")
        else:
            bot.send_message(message.chat.id, f"Неправильно.\nОтвет: {correct}")

        send_random_image(message.chat.id)
        del users[user_id]["current_injection"]
        send_injection(message.chat.id, user_id)
        return

    # === ВИКТОРИНА ===
    if "current_answer" in users[user_id]:
        correct = users[user_id]["current_answer"]

        if text == correct:
            bot.send_message(message.chat.id, "Правильно!")
        else:
            bot.send_message(message.chat.id, f"Неправильно.\nОтвет: {correct}")

        send_random_image(message.chat.id)
        del users[user_id]["current_answer"]
        return

    # === ДУЭЛЬ ===
    if "duel_answer" in users[user_id]:
        correct = users[user_id]["duel_answer"]

        if text == correct:
            bot.send_message(message.chat.id, "Очко засчитано!")
        else:
            bot.send_message(message.chat.id, f"Неправильно.\nОтвет: {correct}")

        send_random_image(message.chat.id)
        del users[user_id]["duel_answer"]
        return

    bot.send_message(message.chat.id, "Выберите режим:", reply_markup=main_menu())

bot.infinity_polling(skip_pending=True)
