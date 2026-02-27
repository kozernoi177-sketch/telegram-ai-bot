import os
import telebot
from telebot import types
import random

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

users = {}

# ========================= БАЗА ЗНАНИЙ =========================

knowledge_base = {
    "сколько органов": "В организме человека примерно 78 органов.",
    "сколько костей": "У взрослого человека 206 костей.",
    "нормальная температура": "Нормальная температура тела — около 36.6°C.",
    "что такое инсульт": "Инсульт — это нарушение кровоснабжения мозга.",
    "что такое инфаркт": "Инфаркт — это отмирание ткани из-за нехватки кровоснабжения.",
    "самый большой орган": "Самый большой орган человека — кожа.",
}

# ========================= СИМПТОМЫ =========================

symptom_rules = {
    "головная боль": {"risk": 1, "causes": ["стресс", "мигрень"]},
    "температура": {"risk": 2, "causes": ["инфекция", "грипп"]},
    "кашель": {"risk": 2, "causes": ["простуда", "бронхит"]},
    "боль в груди": {"risk": 3, "causes": ["сердечные проблемы"]},
    "одышка": {"risk": 3, "causes": ["астма", "сердечная недостаточность"]},
}

# ========================= ВИКТОРИНА =========================

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

# ========================= МЕНЮ =========================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🧠 Вопрос")
    markup.add("🩺 Симптомы")
    markup.add("🎮 Викторина")
    markup.add("📊 Профиль")
    markup.add("🆘 Первая помощь")
    markup.add("💉 Инъекции")
    markup.add("⚖ ИМТ")
    markup.add("🚨 Срочно к врачу")
    return markup

# ========================= START =========================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {
        "points": 0,
        "quiz": generate_quiz(),
        "bmi_step": None,
        "height": None
    }

    bot.send_message(
        message.chat.id,
        "🩺 Медицинский PRO+ Бот\n\n"
        "⚠️ Бот не заменяет врача.\n"
        "Выберите раздел:",
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

    bot.send_message(message.chat.id, f"🏆 Очки: {points}\n🎓 Уровень: {level}")

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
        "🆘 Первая помощь:\n\n"
        "Ожог — охладить водой 10–15 минут.\n"
        "Обморок — уложить и приподнять ноги.\n"
        "Кровотечение — наложить давление.\n"
        "Удушье — вызвать скорую помощь."
    )

# ========================= ИНЪЕКЦИИ =========================

@bot.message_handler(func=lambda m: m.text == "💉 Инъекции")
def injections(message):
    bot.send_message(
        message.chat.id,
        "💉 Инъекции:\n\n"
        "Внутривенные инъекции выполняются медицинским персоналом.\n"
        "Риски: инфекция, повреждение вены, аллергия.\n"
        "При осложнениях — обратиться к врачу."
    )

# ========================= СРОЧНО К ВРАЧУ =========================

@bot.message_handler(func=lambda m: m.text == "🚨 Срочно к врачу")
def urgent(message):
    bot.send_message(
        message.chat.id,
        "🚨 Срочно к врачу при:\n"
        "- боли в груди\n"
        "- одышке\n"
        "- потере сознания\n"
        "- температуре выше 39°C"
    )

# ========================= ИМТ =========================

@bot.message_handler(func=lambda m: m.text == "⚖ ИМТ")
def bmi_start(message):
    users[message.from_user.id]["bmi_step"] = "height"
    bot.send_message(message.chat.id, "Введите рост в сантиметрах:")

# ========================= ОБРАБОТЧИК =========================

@bot.message_handler(func=lambda message: True)
def handle(message):
    user_id = message.from_user.id
    text = message.text.lower()

    # ---- ИМТ логика ----
    if user_id in users and users[user_id].get("bmi_step"):
        if users[user_id]["bmi_step"] == "height":
            users[user_id]["height"] = float(text) / 100
            users[user_id]["bmi_step"] = "weight"
            bot.send_message(message.chat.id, "Введите вес в кг:")
            return

        elif users[user_id]["bmi_step"] == "weight":
            weight = float(text)
            height = users[user_id]["height"]
            bmi = round(weight / (height * height), 1)
            users[user_id]["bmi_step"] = None
            bot.send_message(message.chat.id, f"Ваш ИМТ: {bmi}")
            return

    # ---- Викторина ----
    if user_id in users and "current_answer" in users[user_id]:
        correct = users[user_id]["current_answer"].lower()
        if text == correct:
            users[user_id]["points"] += 10
            bot.send_message(message.chat.id, "✅ Правильно! +10 очков")
        else:
            bot.send_message(message.chat.id, f"❌ Неправильно\nПравильный ответ: {users[user_id]['current_answer']}")
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
            risk = "ВЫСОКИЙ 🚨"

        causes = []
        for f in found:
            causes.extend(symptom_rules[f]["causes"])

        bot.send_message(
            message.chat.id,
            f"🩺 Симптомы: {', '.join(found)}\n"
            f"Причины: {', '.join(set(causes))}\n"
            f"Риск: {risk}"
        )
        return

    # ---- База знаний ----
    for key in knowledge_base:
        if key in text:
            bot.send_message(message.chat.id, knowledge_base[key])
            return

    bot.send_message(message.chat.id, "🤖 Я не нашёл точный ответ. Попробуйте иначе сформулировать.")

bot.infinity_polling(skip_pending=True)
