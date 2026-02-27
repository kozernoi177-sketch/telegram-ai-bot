import os
import telebot
from telebot import types
import sqlite3
import random

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# ================= DATABASE =================

conn = sqlite3.connect("med_bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    question TEXT,
    a TEXT,
    b TEXT,
    c TEXT,
    d TEXT,
    correct TEXT,
    explanation TEXT
)
""")

conn.commit()

# ================= SEED =================

def seed():
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] > 0:
        return

    data = [
        ("Анатомия","Сколько камер у сердца?","2","3","4","5","C","2 предсердия и 2 желудочка."),
        ("Анатомия","Сколько костей у взрослого человека?","206","208","210","212","A","У взрослого человека 206 костей."),
        ("Инъекции","Под каким углом делают внутримышечную инъекцию?","30°","45°","90°","120°","C","Внутримышечно вводят под 90°."),
        ("Первая помощь","Что делать при артериальном кровотечении?","Жгут","Вода","Массаж","Ничего","A","Жгут накладывают выше раны."),
        ("Фармакология","Антибиотики действуют против:","Вирусов","Бактерий","Грибов","Аллергии","B","Антибиотики действуют на бактерии.")
    ]

    cursor.executemany("""
    INSERT INTO questions(category,question,a,b,c,d,correct,explanation)
    VALUES (?,?,?,?,?,?,?,?)
    """, data)

    conn.commit()

seed()

# ================= STATE =================

sessions = {}

# ================= MENUS =================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📚 Тренировка", "📝 Экзамен")
    return markup

def category_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Анатомия", "Инъекции")
    markup.add("Первая помощь", "Фармакология")
    markup.add("⬅ Назад")
    return markup

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):
    sessions.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "Выберите режим:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "⬅ Назад")
def back(message):
    sessions.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "Выберите режим:", reply_markup=main_menu())

# ================= MODE =================

@bot.message_handler(func=lambda m: m.text == "📚 Тренировка")
def training(message):
    sessions[message.chat.id] = {"mode": "training"}
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=category_menu())

@bot.message_handler(func=lambda m: m.text == "📝 Экзамен")
def exam(message):
    sessions[message.chat.id] = {"mode": "exam", "score": 0, "count": 0}
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=category_menu())

# ================= CATEGORY =================

@bot.message_handler(func=lambda m: m.text in ["Анатомия","Инъекции","Первая помощь","Фармакология"])
def category(message):
    user_id = message.chat.id
    session = sessions.get(user_id)
    if not session:
        return

    cursor.execute("SELECT * FROM questions WHERE category=?", (message.text,))
    questions = cursor.fetchall()

    if not questions:
        bot.send_message(user_id, "Нет вопросов.")
        return

    random.shuffle(questions)

    session["questions"] = questions[:10] if session["mode"] == "exam" else questions
    session["category"] = message.text
    session["count"] = 0

    ask_question(user_id)

# ================= ASK QUESTION =================

def ask_question(user_id):
    session = sessions[user_id]

    if session["mode"] == "exam" and session["count"] >= 10:
        percent = int((session["score"] / 10) * 100)
        bot.send_message(user_id, f"Экзамен завершён.\nРезультат: {percent}%")
        sessions.pop(user_id)
        return

    q = session["questions"][session["count"]]
    session["current"] = q
    session["answered"] = False

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("A", callback_data="A"),
        types.InlineKeyboardButton("B", callback_data="B"),
        types.InlineKeyboardButton("C", callback_data="C"),
        types.InlineKeyboardButton("D", callback_data="D")
    )

    bot.send_message(
        user_id,
        f"{q[2]}\n\nA) {q[3]}\nB) {q[4]}\nC) {q[5]}\nD) {q[6]}",
        reply_markup=markup
    )

# ================= ANSWER =================

@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    user_id = call.message.chat.id
    session = sessions.get(user_id)

    if not session or session.get("answered"):
        return

    session["answered"] = True

    bot.edit_message_reply_markup(
        chat_id=user_id,
        message_id=call.message.message_id,
        reply_markup=None
    )

    correct = session["current"][7]

    if call.data == correct:
        bot.send_message(user_id, "✅ Верно!")
        if session["mode"] == "exam":
            session["score"] += 1
    else:
        bot.send_message(user_id, f"❌ Неверно.\nПравильный ответ: {correct}")

    bot.send_message(user_id, f"📖 {session['current'][8]}")

    session["count"] += 1
    ask_question(user_id)

print("BOT STARTED")
bot.infinity_polling(skip_pending=True)
