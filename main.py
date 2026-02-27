print("BOT STARTED")

while True:
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print("CRASH:", e)
