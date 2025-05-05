import asyncio
import os
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import Command
import aiohttp
import datetime

# Темы по дням недели
topics_by_day = {
    'Monday': 'Финансовое мышление',
    'Tuesday': 'Базовые знания и ликбез',
    'Wednesday': 'Новости и события рынка',
    'Thursday': 'Разборы и сравнения',
    'Friday': 'Ошибки и страхи новичков',
    'Saturday': 'Истории и вдохновение',
    'Sunday': 'Пошаговые инструкции / Гайды'
}

# Определяем текущий день недели
today = datetime.datetime.now().strftime('%A')  # например, 'Monday'

# Получаем тему для сегодняшнего дня
today_topic = topics_by_day.get(today, 'Тема не задана')

print(f'Сегодня {today}, тема: {today_topic}')
# Загружаем токены
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем экземпляры бота и диспетчера
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Функция генерации поста через OpenRouter
async def generate_post(prompt_text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt_text}],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data['choices'][0]['message']['content']
            else:
                error = await response.text()
                raise Exception(f"Ошибка при запросе OpenRouter: {error}")

# Обработчик команды /getpost
@dp.message(Command("getpost"))
async def handle_getpost(message: Message):
    try:
        prompt = "Для Telegram-канала тематики Инвестиции для новичков сделай пост на тему {topics_by_day}"
        post_text = await generate_post(prompt)
        await message.answer(post_text)
    except Exception as e:
        await message.answer(f"Ошибка при генерации поста:\n\n{str(e)}")

# Основная функция запуска бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
