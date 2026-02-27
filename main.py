import os
import telebot
from telebot import types
import random

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# ===================== ПОЛЬЗОВАТЕЛИ =====================

users = {}

# ===================== БАЗА ЗНАНИЙ =====================

knowledge_base = {
    "сколько органов": "В организме человека примерно 78 органов.",
    "сколько костей": "У взрослого человека 206 костей.",
    "нормальная температура": "Нормальная температура тела — около 36.6°C.",
    "что такое инсульт": "Инсульт — это нарушение кровоснабжения мозга.",
    "что такое инфаркт": "Инфаркт — это отмирание ткани из-за нехватки кровоснабжения.",
    "сколько зубов": "У взрослого человека 32 зуба.",
    "самый большой орган": "Самый большой орган человека — кожа.",
    "что такое давление": "Артериальное давление — это давление крови на стенки сосудов.",
}

# ===================== АНАЛИЗ СИМПТОМОВ =====================

symptom_rules = {
    "головная боль": {"causes": ["стресс", "мигрень"], "risk": 1},
    "температура": {"causes": ["инфекция", "грипп"], "risk": 2},
    "кашель": {"causes": ["простуда", "бронхит"], "risk": 2},
    "боль в груди": {"causes": ["сердечные проблемы"], "risk": 3},
    "одышка": {"causes": ["астма", "сердечная недостаточность"], "risk": 3},
    "тошнота": {"causes": ["отравление", "гастрит"], "risk": 1},
    "слабость": {"causes": ["анемия", "инфекция"], "risk": 1},
}

# ===================== ВИКТОРИНА =====================

quiz_base = [
    ("Сколько камер в сердце?", "4"),
    ("Сколько лёгких у человека?", "2"),
    ("Какой орган фильтрует кровь?", "Почки"),
    ("Сколько литров крови у человека?", "5"),
    ("Главный орган нервной системы?", "Мозг"),
]

def generate_quiz():
    questions = []
    for i in range(20):
        for q in quiz_base:
            questions.append(q)
    return random.sample(questions, len(questions))

# ===================== МЕНЮ =====================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🧠 Задать вопрос")
    markup.add("🩺 Анализ симптомов")
    markup.add("🎮 Викторина")
    markup.add("📊 Профиль")
    return markup

# ===================== START =====================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {
        "points": 0,
        "quiz": generate_quiz()
    }

    bot.send_message(
        message.chat.id,
        "🩺 Медицинский PRO Бот\n\n"
        "⚠️ Не заменяет врача.\n"
        "Выберите раздел:",
        reply_markup=main_menu()
    )

# ===================== ПРОФИЛЬ =====================

@bot.message_handler(func=lambda message: message.text == "📊 Профиль")
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
        f"🏆 Очки: {points}\n🎓 Уровень: {level}"
    )

# ===================== ВИКТОРИНА =====================

def send_quiz(chat_id, user_id):
    if not users[user_id]["quiz"]:
        users[user_id]["quiz"] = generate_quiz()

    question, answer = users[user_id]["quiz"].pop()
    users[user_id]["current_answer"] = answer
    bot.send_message(chat_id, question)

@bot.message_handler(func=lambda message: message.text == "🎮 Викторина")
def quiz(message):
    user_id = message.from_user.id
    send_quiz(message.chat.id, user_id)

# ===================== ОБРАБОТЧИК =====================

@bot.message_handler(func=lambda message: True)
def handle(message):
    user_id = message.from_user.id
    text = message.text.lower()

    # ---- Проверка викторины ----
    if user_id in users and "current_answer" in users[user_id]:
        correct = users[user_id]["current_answer"].lower()

        if text == correct:
            users[user_id]["points"] += 10
            bot.send_message(message.chat.id, "✅ Правильно! +10 очков")
        else:
            bot.send_message(
                message.chat.id,
                f"❌ Неправильно\nПравильный ответ: {users[user_id]['current_answer']}"
            )

        del users[user_id]["current_answer"]
        send_quiz(message.chat.id, user_id)
        return

    # ---- Анализ симптомов ----
    found = []
    total_risk = 0

    for symptom in symptom_rules:
        if symptom in text:
            found.append(symptom)
            total_risk += symptom_rules[symptom]["risk"]

    if found:
        risk_level = "НИЗКИЙ"
        if total_risk >= 4:
            risk_level = "СРЕДНИЙ"
        if total_risk >= 6:
            risk_level = "ВЫСОКИЙ 🚨"

        causes = []
        for s in found:
            causes.extend(symptom_rules[s]["causes"])

        bot.send_message(
            message.chat.id,
            f"🩺 Обнаружены симптомы: {', '.join(found)}\n\n"
            f"Возможные причины: {', '.join(set(causes))}\n\n"
            f"Уровень риска: {risk_level}"
        )
        return

    # ---- Поиск ответа в базе ----
    for key in knowledge_base:
        if key in text:
            bot.send_message(message.chat.id, knowledge_base[key])
            return

    bot.send_message(
        message.chat.id,
        "🤖 Я не нашёл точный ответ.\nПопробуйте переформулировать вопрос."
    )

bot.infinity_polling(skip_pending=True)
