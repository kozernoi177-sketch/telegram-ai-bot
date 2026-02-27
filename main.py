import os
import telebot
from telebot import types
import random
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

users = {}

# ========================= БАЗА ЗНАНИЙ =========================

knowledge_base = {
    "сколько костей": "У взрослого человека 206 костей.",
    "сколько органов": "В организме человека около 78 органов.",
    "что такое инсульт": "Инсульт — нарушение кровоснабжения мозга.",
    "что такое инфаркт": "Инфаркт — отмирание ткани из-за нехватки крови.",
    "нормальная температура": "Нормальная температура тела — около 36.6°C.",
}

# ========================= СИМПТОМЫ =========================

symptom_rules = {
    "головная боль": {"risk": 1, "causes": ["стресс", "мигрень"]},
    "температура": {"risk": 2, "causes": ["инфекция", "грипп"]},
    "кашель": {"risk": 2, "causes": ["простуда", "бронхит"]},
    "боль в груди": {"risk": 3, "causes": ["сердечные проблемы"]},
    "одышка": {"risk": 3, "causes": ["астма", "сердечная недостаточность"]},
}

# ========================= ОБЩАЯ ВИКТОРИНА =========================

quiz_base = [
    ("Сколько камер в сердце?", "4"),
    ("Сколько лёгких у человека?", "2"),
    ("Какой орган фильтрует кровь?", "Почки"),
    ("Главный орган нервной системы?", "Мозг"),
]

def generate_quiz():
    questions = []
    for i in range(20):
        for q in quiz_base:
            questions.append(q)
    return random.sample(questions, len(questions))

# ========================= ИНЪЕКЦИИ (для М) =========================

injection_base = [
    ("Может ли нарушение стерильности привести к инфекции?", "да"),
    ("Является ли аллергическая реакция возможным осложнением инъекции?", "да"),
    ("Важно ли соблюдать асептику при инъекциях?", "да"),
    ("Может ли неправильная техника вызвать гематому?", "да"),
    ("Нужно ли проверять срок годности препарата перед использованием?", "да"),
    ("Может ли появиться отёк после инъекции?", "да"),
    ("Может ли покраснение быть признаком воспаления?", "да"),
    ("Является ли стерильность обязательной при медицинских процедурах?", "да"),
]

def generate_injection_questions():
    questions = []
    for i in range(10):  # 8 × 10 = 80
        for q in injection_base:
            questions.append(q)
    return random.sample(questions, len(questions))

# ========================= МЕНЮ =========================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🧠 Вопрос")
    markup.add("🩺 Симптомы")
    markup.add("🎮 Викторина")
    markup.add("📊 Профиль")
    markup.add("🆘 Первая помощь")
    markup.add("💉 Инъекции (для М)")
    return markup

# ========================= START =========================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {
        "points": 0,
        "quiz": generate_quiz(),
        "history": []
    }

    bot.send_message(
        message.chat.id,
        "Медицинский бот.\nВыберите раздел:",
        reply_markup=main_menu()
    )

# ========================= ПРОФИЛЬ =========================

@bot.message_handler(func=lambda m: m.text == "📊 Профиль")
def profile(message):
    user_id = message.from_user.id
    points = users.get(user_id, {}).get("points", 0)

    level = "Студент"
    if points >= 50:
        level = "Интерн"
    if points >= 150:
        level = "Доктор"

    bot.send_message(
        message.chat.id,
        f"Очки: {points}\nУровень: {level}"
    )

# ========================= ВИКТОРИНА =========================

def send_quiz(chat_id, user_id):
    if not users[user_id]["quiz"]:
        users[user_id]["quiz"] = generate_quiz()

    q, a = users[user_id]["quiz"].pop()
    users[user_id]["current_answer"] = a
    bot.send_message(chat_id, q)

@bot.message_handler(func=lambda m: m.text == "🎮 Викторина")
def quiz(message):
    send_quiz(message.chat.id, message.from_user.id)

# ========================= ПЕРВАЯ ПОМОЩЬ =========================

@bot.message_handler(func=lambda m: m.text == "🆘 Первая помощь")
def first_aid(message):
    bot.send_message(
        message.chat.id,
        "Первая помощь:\n"
        "Ожог — охладить водой 10–15 минут.\n"
        "Обморок — уложить и приподнять ноги.\n"
        "Кровотечение — наложить давление."
    )

# ========================= ИНЪЕКЦИИ =========================

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
    bot.send_message(chat_id, f"💉 Вопрос:\n{q}\n\nОтветьте: да или нет")

def handle_injection_answer(message):
    user_id = message.from_user.id
    text = message.text.lower()

    if user_id in users and "current_injection_answer" in users[user_id]:
        correct = users[user_id]["current_injection_answer"]

        if text == correct:
            bot.send_message(message.chat.id, "Умница.")
        else:
            bot.send_message(
                message.chat.id,
                f"Неправильно.\nПравильный ответ: {correct}"
            )

        del users[user_id]["current_injection_answer"]
        send_injection_question(message.chat.id, user_id)
        return True

    return False

# ========================= ОБЩИЙ ОБРАБОТЧИК =========================

@bot.message_handler(func=lambda message: True)
def handle(message):

    # ---- Сначала проверяем инъекции ----
    if handle_injection_answer(message):
        return

    user_id = message.from_user.id
    text = message.text.lower()

    # ---- Проверка викторины ----
    if user_id in users and "current_answer" in users[user_id]:
        correct = users[user_id]["current_answer"].lower()

        if text == correct:
            users[user_id]["points"] += 10
            bot.send_message(message.chat.id, "Правильно! +10 очков")
        else:
            bot.send_message(
                message.chat.id,
                f"Неправильно.\nПравильный ответ: {users[user_id]['current_answer']}"
            )

        del users[user_id]["current_answer"]
        send_quiz(message.chat.id, user_id)
        return

    # ---- Симптомы ----
    found = []
    total_risk = 0

    for s in symptom_rules:
        if s in text:
            found.append(s)
            total_risk += symptom_rules[s]["risk"]

    if found:
        risk = "НИЗКИЙ"
        if total_risk >= 4:
            risk = "СРЕДНИЙ"
        if total_risk >= 6:
            risk = "ВЫСОКИЙ"

        causes = []
        for f in found:
            causes.extend(symptom_rules[f]["causes"])

        bot.send_message(
            message.chat.id,
            f"Обнаружены симптомы: {', '.join(found)}\n"
            f"Возможные причины: {', '.join(set(causes))}\n"
            f"Уровень риска: {risk}"
        )

        users[user_id]["history"].append({
            "date": datetime.now().strftime("%d.%m.%Y"),
            "risk": risk,
            "symptoms": found
        })

        return

    # ---- База знаний ----
    for key in knowledge_base:
        if key in text:
            bot.send_message(message.chat.id, knowledge_base[key])
            return

    bot.send_message(
        message.chat.id,
        "Я не нашёл точный ответ. Попробуйте переформулировать вопрос."
    )

bot.infinity_polling(skip_pending=True)
