import telebot
import os
import json
import random
from openai import OpenAI
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN)
client = OpenAI(api_key=OPENAI_KEY)

user_sessions = {}

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Начать экзамен", callback_data="start_exam"))
    bot.send_message(message.chat.id, "Медицинский экзамен (20 вопросов)", reply_markup=markup)

# ================= НАЧАТЬ =================

@bot.callback_query_handler(func=lambda call: call.data == "start_exam")
def begin_exam(call):
    user_id = call.message.chat.id

    user_sessions[user_id] = {
        "current": 0,
        "score": 0
    }

    bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    send_question(user_id)

# ================= ГЕНЕРАЦИЯ ВОПРОСА =================

def generate_ai_question():
    prompt = """
    Сгенерируй медицинский тестовый вопрос уровня медколледжа.
    Верни ТОЛЬКО JSON:

    {
      "question": "...",
      "options": ["A","B","C","D"],
      "correct": 0
    }
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()

        start = content.find("{")
        end = content.rfind("}") + 1
        content = content[start:end]

        return json.loads(content)

    except Exception as e:
        print("AI ERROR:", e)
        return {
            "question": "Сколько камер у сердца?",
            "options": ["2", "3", "4", "5"],
            "correct": 2
        }

# ================= ОТПРАВКА ВОПРОСА =================

def send_question(user_id):
    session = user_sessions[user_id]

    if session["current"] >= 20:
        finish_exam(user_id)
        return

    q = generate_ai_question()
    session["current_question"] = q

    text = f"Вопрос {session['current']+1}/20\n\n{q['question']}"

    markup = InlineKeyboardMarkup()
    for i, option in enumerate(q["options"]):
        markup.add(InlineKeyboardButton(option, callback_data=f"ans_{i}"))

    bot.send_message(user_id, text, reply_markup=markup)

# ================= ОТВЕТ =================

@bot.callback_query_handler(func=lambda call: call.data.startswith("ans_"))
def handle_answer(call):
    user_id = call.message.chat.id

    if user_id not in user_sessions:
        return

    session = user_sessions[user_id]
    q = session["current_question"]

    selected = int(call.data.split("_")[1])
    correct = q["correct"]

    bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)

    if selected == correct:
        session["score"] += 1
        bot.send_message(user_id, "✅ Верно")
    else:
        bot.send_message(user_id, f"❌ Неверно\nПравильный ответ: {q['options'][correct]}")

    session["current"] += 1
    send_question(user_id)

# ================= ФИНИШ =================

def finish_exam(user_id):
    score = user_sessions[user_id]["score"]
    bot.send_message(user_id, f"Экзамен завершён\nРезультат: {score}/20")
    del user_sessions[user_id]

bot.infinity_polling()
