import asyncio
import os
import logging
import datetime
import aiohttp

from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import Command
from image_generator import generate_image_text
import re

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

# Определяем текущий день недели и тему
today = datetime.datetime.now().strftime('%A')
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

# Удаление эмодзи из строки
def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002700-\U000027BF"  # Dingbats
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

# Функция генерации текста через OpenRouter
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
        # Шаг 1: сгенерировать пост
        prompt = f"Для Telegram-канала тематики 'Инвестиции для новичков' сделай пост на тему '{today_topic}'."
        post_text = await generate_post(prompt)
        await message.answer(post_text)

        # Шаг 2: сгенерировать короткий заголовок
        headline_prompt = (
            f"Прочитай текст ниже и придумай к нему короткий заголовок (1-3 слова), отражающий суть. "
            f"Пиши только заголовок, без кавычек и пояснений:\n\n{post_text}"
        )
        raw_headline = await generate_post(headline_prompt)
        clean_headline = remove_emojis(raw_headline.strip())
        await message.answer(f"<b>{clean_headline}</b>")

    except Exception as e:
        await message.answer(f"Ошибка при генерации поста:\n\n{str(e)}")

# Основная функция запуска бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
