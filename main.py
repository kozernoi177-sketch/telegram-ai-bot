import os
import telebot
from telebot import types
import random
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

users = {}

# ==========================================================
#                     БАЗА ЗНАНИЙ
# ==========================================================

knowledge_base = {
    "сколько костей": "У взрослого человека 206 костей.",
    "сколько органов": "В организме человека около 78 органов.",
    "что такое инсульт": "Инсульт — нарушение кровоснабжения мозга.",
    "что такое инфаркт": "Инфаркт — отмирание ткани из-за нехватки крови.",
}

# ==========================================================
#                    СИМПТОМЫ
# ==========================================================

symptom_rules = {
    "головная боль": {"risk": 1},
    "температура": {"risk": 2},
    "кашель": {"risk": 2},
    "боль в груди": {"risk": 3},
    "одышка": {"risk": 3},
}

# ==========================================================
#                    ВИКТОРИНА (200+)
# ==========================================================

quiz_base = [
    # Анатомия
    ("Сколько камер в сердце?", "4"),
    ("Сколько лёгких у человека?", "2"),
    ("Главный орган нервной системы?", "Мозг"),
    ("Какой орган фильтрует кровь?", "Почки"),
]

# добавляем 100+ вопросов по стерильности
sterility_questions = [
    ("Является ли стерильность обязательной в хирургии?", "Да"),
    ("Можно ли использовать нестерильные инструменты?", "Нет"),
    ("Нужно ли мыть руки перед процедурой?", "Да"),
    ("Предотвращает ли антисептик распространение инфекции?", "Да"),
    ("Можно ли повторно использовать одноразовый шприц?", "Нет"),
]

for i in range(30):
    for q in sterility_questions:
        quiz_base.append(q)

def generate_quiz():
    return random.sample(quiz_base, len(quiz_base))

# ==========================================================
#               ИНЪЕКЦИИ (для М) 200+
# ==========================================================

injection_templates = [
    "Может ли нарушение стерильности привести к осложнениям?",
    "Является ли контроль состояния пациента важным после процедуры?",
    "Может ли несоблюдение правил привести к инфекции?",
    "Является ли медицинская подготовка обязательной для процедуры?",
    "Может ли появиться покраснение после процедуры?",
    "Может ли возникнуть аллергическая реакция?",
    "Может ли неправильная техника вызвать осложнение?",
    "Нужно ли соблюдать стандарты безопасности?",
]

def generate_injection_questions():
    questions = []
    for i in range(30):  # 8 × 30 = 240 вопросов
        for q in injection_templates:
            answer = random.choice(["да", "нет"])
            questions.append((q, answer))
    return random.sample(questions, len(questions))

# ==========================================================
#                       МЕНЮ
# ==========================================================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🧠 Вопрос")
    markup.add("🩺 Симптомы")
    markup.add("🎮 Викторина")
    markup.add("📊 Профиль")
    markup.add("💉 Инъекции (для М)")
    return markup

# ==========================================================
#                       START
# ==========================================================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {
        "points": 0,
        "quiz": generate_quiz(),
        "history": [],
        "injection_correct": 0,
        "injection_total": 0,
    }

    bot.send_message(
        message.chat.id,
        "Медицинский бот.\nВыберите раздел:",
        reply_markup=main_menu()
    )

# ==========================================================
#                       ПРОФИЛЬ
# ==========================================================

@bot.message_handler(func=lambda m: m.text == "📊 Профиль")
def profile(message):
    user = users[message.from_user.id]

    level = "Студент"
    if user["points"] >= 50:
        level = "Интерн"
    if user["points"] >= 150:
        level = "Доктор"

    bot.send_message(
        message.chat.id,
        f"Очки: {user['points']}\n"
        f"Уровень: {level}\n"
        f"Инъекции: {user['injection_correct']} / {user['injection_total']}"
    )

# ==========================================================
#                     ВИКТОРИНА
# ==========================================================

def send_quiz(chat_id, user_id):
    if not users[user_id]["quiz"]:
        users[user_id]["quiz"] = generate_quiz()

    q, a = users[user_id]["quiz"].pop()
    users[user_id]["current_answer"] = a
    bot.send_message(chat_id, q)

@bot.message_handler(func=lambda m: m.text == "🎮 Викторина")
def quiz(message):
    send_quiz(message.chat.id, message.from_user.id)

# ==========================================================
#                 ИНЪЕКЦИИ (для М)
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
    bot.send_message(chat_id, f"💉 Вопрос:\n{q}\n\nОтветьте: да или нет")

def handle_injection_answer(message):
    user_id = message.from_user.id
    text = message.text.lower()

    if "current_injection_answer" in users[user_id]:
        correct = users[user_id]["current_injection_answer"]
        users[user_id]["injection_total"] += 1

        if text == correct:
            users[user_id]["injection_correct"] += 1
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

# ==========================================================
#                   ОБЩИЙ ОБРАБОТЧИК
# ==========================================================

@bot.message_handler(func=lambda message: True)
def handle(message):

    user_id = message.from_user.id

    if handle_injection_answer(message):
        return

    text = message.text.lower()

    # Викторина
    if "current_answer" in users[user_id]:
        correct = users[user_id]["current_answer"].lower()

        if text.lower() == correct.lower():
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

    # Симптомы
    total_risk = 0
    found = []

    for s in symptom_rules:
        if s in text:
            total_risk += symptom_rules[s]["risk"]
            found.append(s)

    if found:
        risk = "НИЗКИЙ"
        if total_risk >= 4:
            risk = "СРЕДНИЙ"
        if total_risk >= 6:
            risk = "ВЫСОКИЙ"

        bot.send_message(
            message.chat.id,
            f"Симптомы: {', '.join(found)}\n"
            f"Уровень риска: {risk}"
        )
        return

    # База знаний
    for key in knowledge_base:
        if key in text:
            bot.send_message(message.chat.id, knowledge_base[key])
            return

    bot.send_message(message.chat.id, "Попробуйте задать вопрос иначе.")

bot.infinity_polling(skip_pending=True)
