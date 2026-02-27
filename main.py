import os
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

medical_data = {
    "головная боль": "Головная боль может быть вызвана стрессом, усталостью или обезвоживанием. Если боль сильная или длится долго — обратитесь к врачу.",
    "температура": "Повышенная температура — признак инфекции. Пейте больше жидкости и наблюдайте за состоянием.",
    "кашель": "Кашель может быть симптомом простуды или аллергии. Если длится больше 2 недель — обратитесь к врачу.",
    "боль в животе": "Боль в животе может иметь разные причины — от несварения до воспаления. При сильной боли срочно к врачу."
}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
        "🩺 Медицинский бот\n\n"
        "Напишите симптом, например:\n"
        "головная боль\n"
        "температура\n"
        "кашель\n"
        "боль в животе\n\n"
        "⚠️ Бот не заменяет врача."
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.lower()

    if text in medical_data:
        bot.reply_to(message, medical_data[text])
    else:
        bot.reply_to(message,
            "Я пока не знаю этот симптом.\n"
            "Попробуйте
