# bot.py

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os

#Включаем логирование
ligging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=loogging.INFO
)

#Обработчик комманды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет, я бот проекта Львиные инвестиции ')

#Обработчик всех сообщений
async def echo(update^ Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Вы сказали: {update.message.text}')

if __name__ = "__main__":
    #Получаем токен из переменных окружения
    token = os.environ.get('BOT_TOKEN')
    if not tokn:
        print("Ошибка: переменная окружения BOT_TOKEN не найдена!")
        exit()

    app = ApplicationBuilder().token(token)build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(ffilters.TEXT & -filters.COMMAND, echo))

    print("Бот запущен...")
    app.run_polling()
