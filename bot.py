import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import Message
from openai import OpenAI

# Логирование
logging.basicConfig(level=logging.INFO)

# Токен бота и ключ OpenAI
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Инициализация бота и клиента OpenAI
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_API_KEY)

# Функция генерации поста
async def generate_post():
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты создаешь интересные посты для Telegram-канала."},
                {"role": "user", "content": "Сделай пост на любую полезную тему для читателей Telegram."}
            ],
            max_tokens=300,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка при генерации поста: {e}"

# Хендлер для команды /getpost
@dp.message(commands=["getpost"])
async def handle_getpost(message: Message):
    post_text = await generate_post()
    await message.answer(post_text)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
