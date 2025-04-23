import asyncio
import os
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import Command

from openai import OpenAI  # добавлено

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # добавлено

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

client = OpenAI(api_key=OPENAI_API_KEY)  # добавлено

@dp.message(Command("getpost"))  # добавлено
async def handle_getpost(message: Message):  # добавлено
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты пишешь пост для Telegram-канала на тему инвестиций"},
                {"role": "user", "content": "Придумай интересный пост про инвестиции"}
            ],
        )
        post_text = completion.choices[0].message.content
        await message.answer(post_text)
    except Exception as e:
        await message.answer(f"Ошибка при генерации поста:\n\n{e}")

@dp.message()
async def echo_handler(message: Message):
    await message.answer(f"Ты написал: {message.text}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
