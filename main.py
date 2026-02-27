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
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    question TEXT,
    answer TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS exam_history (
    user_id INTEGER,
    question_id INTEGER,
    PRIMARY KEY(user_id, question_id)
)
""")

conn.commit()

# ================= SEED QUESTIONS =================

def seed():
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] > 0:
        return

    data = []
    categories = ["Инъекции", "Анатомия", "Первая помощь", "Фармакология"]

    for cat in categories:
        for i in range(1, 101):  # 100 на категорию = 400 всего
            data.append((
                cat,
                f"{cat}: медицинский вопрос {i}",
                "да"
            ))

    cursor.executemany(
        "INSERT INTO questions(category, question, answer) VALUES (?,?,?)",
        data
    )
    conn.commit()

seed()

# ================= STATE =================

sessions = {}
duels = {}

# ================= MENUS =================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📚 Тренировка", "📝 Экзамен")
    markup.add("🥊 1 на 1")
    return markup

def category_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Инъекции", "Анатомия")
    markup.add("Первая помощь", "Фармакология")
    markup.add("⬅ Назад")
    return markup

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)",(user_id,))
    conn.commit()

    args = message.text.split()

    if len(args) > 1 and args[1].startswith("duel_"):
        parts = args[1].split("_")
        inviter = int(parts[1])
        category = parts[2]
        start_duel(inviter, user_id, category)
        return

    bot.send_message(user_id,"Выберите режим:",reply_markup=main_menu())

# ================= TRAINING =================

@bot.message_handler(func=lambda m: m.text == "📚 Тренировка")
def training(message):
    sessions[message.chat.id] = {"mode":"training"}
    bot.send_message(message.chat.id,"Выберите категорию:",reply_markup=category_menu())

# ================= EXAM =================

@bot.message_handler(func=lambda m: m.text == "📝 Экзамен")
def exam(message):
    sessions[message.chat.id] = {"mode":"exam","score":0,"count":0}
    bot.send_message(message.chat.id,"Выберите категорию:",reply_markup=category_menu())

# ================= DUEL =================

@bot.message_handler(func=lambda m: m.text == "🥊 1 на 1")
def duel_setup(message):
    sessions[message.chat.id] = {"mode":"duel_setup"}
    bot.send_message(message.chat.id,"Выберите категорию:",reply_markup=category_menu())

def start_duel(p1, p2, category):
    cursor.execute("SELECT * FROM questions WHERE category=? ORDER BY RANDOM() LIMIT 10",(category,))
    pool = cursor.fetchall()

    duels[p1]={"opponent":p2,"pool":pool,"round":0,"score":0}
    duels[p2]={"opponent":p1,"pool":pool,"round":0,"score":0}

    bot.send_message(p1,f"Дуэль началась ({category})")
    bot.send_message(p2,f"Дуэль началась ({category})")

    next_duel_question(p1)
    next_duel_question(p2)

def next_duel_question(user_id):
    duel = duels[user_id]

    if duel["round"] >= 10:
        finish_duel(user_id)
        return

    q = duel["pool"][duel["round"]]
    duel["round"] += 1

    sessions[user_id] = {"mode":"duel","answer":q[3]}
    bot.send_message(user_id,f"Раунд {duel['round']}/10\n{q[2]}")

def finish_duel(user_id):
    duel = duels[user_id]
    opponent = duel["opponent"]

    if duel["score"] > duels[opponent]["score"]:
        bot.send_message(user_id,"🏆 Победа!")
        bot.send_message(opponent,"❌ Поражение.")
    elif duel["score"] < duels[opponent]["score"]:
        bot.send_message(opponent,"🏆 Победа!")
        bot.send_message(user_id,"❌ Поражение.")
    else:
        bot.send_message(user_id,"🤝 Ничья.")
        bot.send_message(opponent,"🤝 Ничья.")

    duels.pop(user_id,None)
    duels.pop(opponent,None)

# ================= CATEGORY =================

@bot.message_handler(func=lambda m: m.text in ["Инъекции","Анатомия","Первая помощь","Фармакология"])
def choose_category(message):
    user_id = message.chat.id
    session = sessions.get(user_id)
    if not session:
        return

    category = message.text

    if session["mode"] == "training":
        ask_random(user_id, category)

    elif session["mode"] == "exam":
        cursor.execute("""
        SELECT * FROM questions
        WHERE category=? AND id NOT IN
        (SELECT question_id FROM exam_history WHERE user_id=?)
        ORDER BY RANDOM() LIMIT 20
        """,(category,user_id))

        pool = cursor.fetchall()
        if len(pool) < 20:
            bot.send_message(user_id,"Вопросы закончились.")
            return

        session["questions"] = pool
        session["category"] = category
        ask_exam(user_id)

    elif session["mode"] == "duel_setup":
        username = bot.get_me().username
        link = f"https://t.me/{username}?start=duel_{user_id}_{category}"
        bot.send_message(user_id,f"Отправь другу ссылку:\n{link}")

# ================= QUESTION LOGIC =================

def ask_random(user_id, category):
    cursor.execute("SELECT * FROM questions WHERE category=? ORDER BY RANDOM() LIMIT 1",(category,))
    q = cursor.fetchone()
    sessions[user_id] = {"mode":"training","answer":q[3],"category":category}
    bot.send_message(user_id,q[2])

def ask_exam(user_id):
    session = sessions[user_id]

    if session["count"] >= 20:
        percent = int((session["score"]/20)*100)
        bot.send_message(user_id,f"Экзамен завершён.\nРезультат: {percent}%")
        sessions.pop(user_id)
        return

    q = session["questions"][session["count"]]
    session["current"] = q
    session["answer"] = q[3]
    session["count"] += 1

    bot.send_message(user_id,f"Вопрос {session['count']}/20\n{q[2]}")

# ================= ANSWERS =================

@bot.message_handler(func=lambda m: True)
def handle_answer(message):
    user_id = message.from_user.id
    session = sessions.get(user_id)

    if not session or "answer" not in session:
        return

    if message.text.lower() == session["answer"]:
        bot.send_message(user_id,"✅ Верно!")
        if session["mode"] == "exam":
            session["score"] += 1
        if session["mode"] == "duel":
            duels[user_id]["score"] += 1
    else:
        bot.send_message(user_id,f"❌ Неверно.\nОтвет: {session['answer']}")

    if session["mode"] == "training":
        ask_random(user_id, session["category"])

    elif session["mode"] == "exam":
        cursor.execute("INSERT INTO exam_history VALUES(?,?)",
                       (user_id,session["current"][0]))
        conn.commit()
        ask_exam(user_id)

    elif session["mode"] == "duel":
        next_duel_question(user_id)

bot.infinity_polling(skip_pending=True)
