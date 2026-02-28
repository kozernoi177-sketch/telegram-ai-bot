import telebot
import json
import os
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Загружаем вопросы
with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

user_sessions = {}

# ===============================
# СТАРТ
# ===============================

@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Анатомия", callback_data="cat_Анатомия"),
        InlineKeyboardButton("Инъекции", callback_data="cat_Инъекции")
    )
    markup.add(
        InlineKeyboardButton("Первая помощь", callback_data="cat_Первая помощь"),
        InlineKeyboardButton("Фармакология", callback_data="cat_Фармакология")
    )

    bot.send_message(
        message.chat.id,
        "Выбери раздел для экзамена:",
        reply_markup=markup
    )

# ===============================
# ВЫБОР КАТЕГОРИИ
# ===============================

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def choose_category(call):
    category = call.data.replace("cat_", "")
    user_id = call.message.chat.id

    if category not in QUESTIONS:
        bot.answer_callback_query(call.id, "Ошибка категории")
        return

    questions = QUESTIONS[category]

    if len(questions) < 20:
        bot.send_message(user_id, "В разделе меньше 20 вопросов.")
        return

    selected = random.sample(questions, 20)

    user_sessions[user_id] = {
        "category": category,
        "questions": selected,
        "current": 0,
        "score": 0
    }

    bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    send_next_question(user_id)

# ===============================
# СЛЕДУЮЩИЙ ВОПРОС
# ===============================

def send_next_question(user_id):
    session = user_sessions[user_id]
    index = session["current"]

    if index >= 20:
        finish_exam(user_id)
        return

    q = session["questions"][index]

    text = f"Вопрос {index+1}/20\n\n{q['question']}"

    markup = InlineKeyboardMarkup()

    for i, option in enumerate(q["options"]):
        markup.add(
            InlineKeyboardButton(option, callback_data=f"answer_{i}")
        )

    bot.send_message(user_id, text, reply_markup=markup)

# ===============================
# ОБРАБОТКА ОТВЕТА
# ===============================

@bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
def handle_answer(call):
    user_id = call.message.chat.id

    if user_id not in user_sessions:
        return

    session = user_sessions[user_id]
    index = session["current"]
    q = session["questions"][index]

    selected = int(call.data.split("_")[1])
    correct = q["correct"]

    # Убираем кнопки (чтобы нельзя было нажимать снова)
    bot.edit_message_reply_markup(
        chat_id=user_id,
        message_id=call.message.message_id,
        reply_markup=None
    )

    if selected == correct:
        session["score"] += 1
        bot.send_message(user_id, "✅ Верно!")
    else:
        correct_text = q["options"][correct]
        bot.send_message(user_id, f"❌ Неверно.\nПравильный ответ: {correct_text}")

    session["current"] += 1
    send_next_question(user_id)

# ===============================
# ЗАВЕРШЕНИЕ
# ===============================

def finish_exam(user_id):
    session = user_sessions[user_id]
    score = session["score"]

    bot.send_message(
        user_id,
        f"Экзамен завершён!\n\nРезультат: {score}/20"
    )

    del user_sessions[user_id]

# ===============================
# ЗАПУСК
# ===============================

bot.polling(none_stop=True)
