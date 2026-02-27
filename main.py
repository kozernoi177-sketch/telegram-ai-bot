import os

if os.path.exists("med_bot.db"):
    os.remove("med_bot.db")
    print("База удалена")
