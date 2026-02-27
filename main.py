import os
import telebot
from telebot import types
import sqlite3
import random
import threading

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

cursor.execute("""
CREATE TABLE IF NOT EXISTS exam_history (
    user_id INTEGER,
    question_id INTEGER,
    PRIMARY KEY(user_id, question_id)
)
""")

conn.commit()

# ================= QUESTIONS =================

def seed():
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] > 0:
        return

    questions_data = [
        ("Анатомия",
         "Сколько камер у сердца?",
         "2","3","4","5",
         "C",
         "У сердца 2 предсердия и 2 желудочка."),

        ("Анатомия",
         "Сколько костей у взрослого человека?",
         "206","208","210","212",
         "A",
         "У взрослого человека 206 костей."),

        ("Инъекции",
         "Под каким углом выполняется внутримышечная инъекция?",
         "30°","45°","90°","120°",
         "C",
         "Внутримышечная инъекция выполняется под 90°."),

        ("Первая помощь",
         "Что делать при артериальном кровотечении?",
         "Наложить жгут","Дать воду","Массировать","Ничего",
         "A",
         "Жгут накладывается выше раны."),

        ("Фармакология",
         "Антибиотики действуют против:",
         "Вирусов","Бактерий","Грибов","Аллергии",
         "B",
         "Антибиотики действуют на бактерии.")
    ]

    cursor.executemany("""
    INSERT INTO questions(category,question,a,b,c,d,correct,explanation)
    VALUES (?,?,?,?,?,?,?,?)
    """, questions_data)

    conn.commit()

seed()

# ================= STATE =================

sessions = {}

# ================= MENUS =================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📚 Тренировка","📝 Экзамен")
    return markup

def category_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Анатомия","Инъекции")
    markup.add("Первая помощь","Фармакология")
    markup.add("⬅ Назад")
    return markup

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):
    sessions.pop(message.chat.id, None)
    bot.send_message(message.chat.id,"Выберите режим:",reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text=="⬅ Назад")
def back(message):
    sessions.pop(message.chat.id,None)
    bot.send_message(message.chat.id,"Выберите режим:",reply_markup=main_menu())

# ================= TRAINING =================

@bot.message_handler(func=lambda m: m.text=="📚 Тренировка")
def training(message):
    sessions[message.chat.id]={"mode":"training"}
    bot.send_message(message.chat.id,"Выберите категорию:",reply_markup=category_menu())

# ================= EXAM =================

@bot.message_handler(func=lambda m: m.text=="📝 Экзамен")
def exam(message):
    sessions[message.chat.id]={"mode":"exam","score":0,"count":0}
    bot.send_message(message.chat.id,"Выберите категорию:",reply_markup=category_menu())

# ================= CATEGORY =================

@bot.message_handler(func=lambda m: m.text in ["Анатомия","Инъекции","Первая помощь","Фармакология"])
def category(message):
    user_id=message.chat.id
    session=sessions.get(user_id)
    if not session:
        return

    if session["mode"]=="training":
        ask_random(user_id,message.text)

    elif session["mode"]=="exam":
        cursor.execute("""
        SELECT * FROM questions
        WHERE category=? AND id NOT IN
        (SELECT question_id FROM exam_history WHERE user_id=?)
        ORDER BY RANDOM() LIMIT 10
        """,(message.text,user_id))

        pool=cursor.fetchall()
        if len(pool)<1:
            bot.send_message(user_id,"Вопросы закончились.")
            return

        session["questions"]=pool
        session["category"]=message.text
        ask_exam(user_id)

# ================= ASK QUESTION =================

def send_question(user_id,q):
    markup=types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("A",callback_data="A"),
        types.InlineKeyboardButton("B",callback_data="B"),
        types.InlineKeyboardButton("C",callback_data="C"),
        types.InlineKeyboardButton("D",callback_data="D")
    )

    bot.send_message(user_id,
                     f"{q[2]}\n\nA) {q[3]}\nB) {q[4]}\nC) {q[5]}\nD) {q[6]}",
                     reply_markup=markup)

    # таймер 30 секунд
    timer=threading.Timer(30,timeout,args=(user_id,))
    sessions[user_id]["timer"]=timer
    timer.start()

def timeout(user_id):
    session=sessions.get(user_id)
    if not session or "current" not in session:
        return
    bot.send_message(user_id,f"⏰ Время вышло.\nПравильный ответ: {session['current'][7]}")
    next_step(user_id)

def ask_random(user_id,category):
    cursor.execute("SELECT * FROM questions WHERE category=? ORDER BY RANDOM() LIMIT 1",(category,))
    q=cursor.fetchone()
    sessions[user_id]={"mode":"training","current":q,"category":category}
    send_question(user_id,q)

def ask_exam(user_id):
    session=sessions[user_id]

    if session["count"]>=10:
        percent=int((session["score"]/10)*100)
        bot.send_message(user_id,f"Экзамен завершён.\nРезультат: {percent}%")
        sessions.pop(user_id)
        return

    q=session["questions"][session["count"]]
    session["current"]=q
    session["count"]+=1
    send_question(user_id,q)

# ================= ANSWERS =================

@bot.callback_query_handler(func=lambda call: True)
def handle_answer(call):
    user_id=call.message.chat.id
    session=sessions.get(user_id)
    if not session:
        return

    session["timer"].cancel()

    if call.data==session["current"][7]:
        bot.send_message(user_id,"✅ Верно!")
        if session["mode"]=="exam":
            session["score"]+=1
    else:
        bot.send_message(user_id,
                         f"❌ Неверно.\nПравильный ответ: {session['current'][7]}")

    bot.send_message(user_id,f"📖 {session['current'][8]}")

    if session["mode"]=="exam":
        cursor.execute("INSERT OR IGNORE INTO exam_history VALUES (?,?)",
                       (user_id,session["current"][0]))
        conn.commit()

    next_step(user_id)

def next_step(user_id):
    session=sessions.get(user_id)
    if not session:
        return

    if session["mode"]=="training":
        ask_random(user_id,session["category"])
    elif session["mode"]=="exam":
        ask_exam(user_id)

bot.infinity_polling(skip_pending=True)
