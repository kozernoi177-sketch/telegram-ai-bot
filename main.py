import os
import telebot
from telebot import types
import sqlite3
import random
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# ================= DATABASE =================

conn = sqlite3.connect("med_trainer.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    points INTEGER DEFAULT 0,
    correct INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    question TEXT,
    answer TEXT,
    explanation TEXT
)
""")

conn.commit()

# ================= SEED QUESTIONS =================

def seed_questions():
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] > 0:
        return

    questions = []

    categories = ["Инъекции", "Анатомия", "Первая помощь", "Фармакология"]

    for cat in categories:
        for i in range(1, 51):
            questions.append((
                cat,
                f"{cat}: Вопрос №{i}",
                "да",
                "Это учебный демонстрационный вопрос."
            ))

    cursor.executemany(
        "INSERT INTO questions(category, question, answer, explanation) VALUES (?,?,?,?)",
        questions
    )
    conn.commit()

seed_questions()

# ================= STATE =================

active_sessions = {}
active_duels = {}

TIME_LIMIT = 30

# ================= UTIL =================

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()

def create_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    conn.commit()

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📚 Тренировка", "📝 Экзамен")
    markup.add("🥊 1 на 1")
    markup.add("📊 Профиль")
    return markup

def category_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Инъекции", "Анатомия")
    markup.add("Первая помощь", "Фармакология")
    return markup

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    create_user(user_id)

    args = message.text.split()

    if len(args) > 1 and args[1].startswith("duel_"):
        parts = args[1].split("_")
        inviter = int(parts[1])
        category = parts[2]
        start_duel(inviter, user_id, category)
        return

    if not get_user(user_id)[1]:
        bot.send_message(user_id, "Введите своё имя:")
    else:
        bot.send_message(user_id, "Добро пожаловать!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: get_user(m.from_user.id) and not get_user(m.from_user.id)[1])
def set_name(message):
    cursor.execute("UPDATE users SET name=? WHERE user_id=?",
                   (message.text, message.from_user.id))
    conn.commit()
    bot.send_message(message.chat.id, "Готово!", reply_markup=main_menu())

# ================= ТРЕНИРОВКА =================

@bot.message_handler(func=lambda m: m.text == "📚 Тренировка")
def training(message):
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=category_menu())
    active_sessions[message.chat.id] = {"mode": "training"}

# ================= ЭКЗАМЕН =================

@bot.message_handler(func=lambda m: m.text == "📝 Экзамен")
def exam(message):
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=category_menu())
    active_sessions[message.chat.id] = {
        "mode": "exam",
        "score": 0,
        "count": 0,
        "questions": []
    }

# ================= ДУЭЛЬ =================

@bot.message_handler(func=lambda m: m.text == "🥊 1 на 1")
def duel_choose_category(message):
    bot.send_message(message.chat.id, "Выберите категорию для дуэли:",
                     reply_markup=category_menu())
    active_sessions[message.chat.id] = {"mode": "duel_setup"}

def start_duel(p1, p2, category):
    cursor.execute("SELECT * FROM questions WHERE category=? ORDER BY RANDOM() LIMIT 10",
                   (category,))
    pool = cursor.fetchall()

    active_duels[p1] = {"opponent": p2, "pool": pool, "round": 0, "score": 0}
    active_duels[p2] = {"opponent": p1, "pool": pool, "round": 0, "score": 0}

    bot.send_message(p1, f"🔥 Дуэль началась! Категория: {category}")
    bot.send_message(p2, f"🔥 Дуэль началась! Категория: {category}")

    next_duel_question(p1)
    next_duel_question(p2)

def next_duel_question(user_id):
    duel = active_duels[user_id]

    if duel["round"] >= 10:
        finish_duel(user_id)
        return

    q = duel["pool"][duel["round"]]
    duel["round"] += 1

    active_sessions[user_id] = {
        "mode": "duel",
        "answer": q[3],
        "time": time.time()
    }

    bot.send_message(user_id, f"Раунд {duel['round']}/10\n{q[2]}")

def finish_duel(user_id):
    duel = active_duels.get(user_id)
    if not duel:
        return

    opponent = duel["opponent"]

    score1 = duel["score"]
    score2 = active_duels[opponent]["score"]

    if score1 > score2:
        bot.send_message(user_id, "🏆 Победа!")
        bot.send_message(opponent, "❌ Поражение.")
    elif score2 > score1:
        bot.send_message(opponent, "🏆 Победа!")
        bot.send_message(user_id, "❌ Поражение.")
    else:
        bot.send_message(user_id, "🤝 Ничья.")
        bot.send_message(opponent, "🤝 Ничья.")

    active_duels.pop(user_id, None)
    active_duels.pop(opponent, None)

# ================= ОБРАБОТКА КАТЕГОРИИ =================

@bot.message_handler(func=lambda m: m.text in ["Инъекции", "Анатомия", "Первая помощь", "Фармакология"])
def category_selected(message):
    user_id = message.chat.id
    session = active_sessions.get(user_id)

    if not session:
        return

    if session["mode"] == "training":
        cursor.execute("SELECT * FROM questions WHERE category=? ORDER BY RANDOM() LIMIT 1",
                       (message.text,))
        q = cursor.fetchone()

        active_sessions[user_id] = {
            "mode": "training",
            "answer": q[3],
            "explanation": q[4],
            "time": time.time(),
            "category": message.text
        }

        bot.send_message(user_id, q[2])

    elif session["mode"] == "exam":
        cursor.execute("SELECT * FROM questions WHERE category=? ORDER BY RANDOM() LIMIT 20",
                       (message.text,))
        session["questions"] = cursor.fetchall()
        session["category"] = message.text
        ask_exam_question(user_id)

    elif session["mode"] == "duel_setup":
        username = bot.get_me().username
        link = f"https://t.me/{username}?start=duel_{user_id}_{message.text}"
        bot.send_message(user_id, f"Отправь другу ссылку:\n{link}")

# ================= ЭКЗАМЕН ЛОГИКА =================

def ask_exam_question(user_id):
    session = active_sessions[user_id]

    if session["count"] >= 20:
        percent = int((session["score"] / 20) * 100)
        bot.send_message(user_id, f"Экзамен завершён!\nРезультат: {percent}%")
        active_sessions.pop(user_id)
        return

    q = session["questions"][session["count"]]
    session["count"] += 1

    session["answer"] = q[3]
    session["time"] = time.time()

    bot.send_message(user_id, f"Вопрос {session['count']}/20\n{q[2]}")

# ================= ОТВЕТЫ =================

@bot.message_handler(func=lambda m: True)
def handle_answer(message):
    user_id = message.from_user.id
    session = active_sessions.get(user_id)

    if not session or "answer" not in session:
        return

    if time.time() - session["time"] > TIME_LIMIT:
        bot.send_message(user_id, "⏳ Время вышло!")
        return

    if message.text.lower() == session["answer"]:
        bot.send_message(user_id, "✅ Верно!")
        if session["mode"] == "duel":
            active_duels[user_id]["score"] += 1
        if session["mode"] == "exam":
            session["score"] += 1
    else:
        bot.send_message(user_id, f"❌ Неверно.\nОтвет: {session['answer']}")
        if session["mode"] == "training":
            bot.send_message(user_id, f"📖 Объяснение: {session['explanation']}")

    if session["mode"] == "duel":
        next_duel_question(user_id)
    elif session["mode"] == "exam":
        ask_exam_question(user_id)

# ================= ПРОФИЛЬ =================

@bot.message_handler(func=lambda m: m.text == "📊 Профиль")
def profile(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id,
                     f"Имя: {user[1]}\nОчки: {user[2]}\nПравильных: {user[3]}/{user[4]}")

bot.infinity_polling(skip_pending=True)
