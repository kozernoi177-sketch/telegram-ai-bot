import os
import telebot
from telebot import types
import random

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

users = {}

# ========================= ОБЩАЯ БАЗА =========================

knowledge_base = {
    "сколько костей": "У взрослого человека 206 костей.",
    "сколько органов": "В организме человека около 78 органов.",
    "что такое инсульт": "Инсульт — нарушение кровоснабжения мозга.",
    "что такое инфаркт": "Инфаркт — отмирание ткани из-за нехватки крови.",
}

# ========================= ИНЪЕКЦИИ (для М) =========================

injection_base = [
    ("Может ли нарушение стерильности привести к инфекции?", "да"),
    ("Является ли аллергическая реакция возможным осложнением инъекции?", "да"),
    ("Важно ли соблюдать асептику при инъекциях?", "да"),
    ("Может ли неправильная техника вызвать гематому?", "да"),
    ("Нужно ли проверять срок годности препарата?", "да"),
    ("Может ли появиться отёк после инъекции?", "да"),
    ("Может ли покраснение быть признаком воспаления?", "да"),
    ("Нужно ли использовать стерильные инструменты?", "да"),
]

def generate_injection_questions():
    questions = []
    for i in range(10):  # 8 × 10 = 80 вопросов
        for q in injection_base:
            questions.append(q)
    return random.sample(questions, len(questions))

# ========================= МЕНЮ =========================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🧠 Вопрос")
    markup.add("💉 Инъекции (для М)")
    return markup

# ========================= START =========================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {}
    bot.send_message(
        message.chat.id,
        "Медицинский бот.\nВыберите раздел:",
        reply_markup=main_menu()
    )

# ========================= ИНЪЕКЦИИ ЛОГИКА =========================

@bot.message_handler(func=lambda m: m.text == "💉 Инъекции (для М)")
def start_injection_section(message):
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
    # Сначала проверяем раздел Инъекции
    if handle_injection_answer(message):
        return

    text = message.text.lower()

    # Поиск по базе знаний
    for key in knowledge_base:
        if key in text:
            bot.send_message(message.chat.id, knowledge_base[key])
            return

    bot.send_message(
        message.chat.id,
        "Я не нашёл точный ответ. Попробуйте задать медицинский вопрос."
    )

bot.infinity_polling(skip_pending=True)
