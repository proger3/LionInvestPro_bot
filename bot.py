import random
import asyncio
import os
import logging
import datetime
import aiohttp
import replicate
from io import BytesIO

from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import Command
import re

# Темы по дням недели
background_urls = [
    "https://disk.yandex.ru/i/2Xm6oBM2Zwww9A",
    "https://disk.yandex.ru/i/95YgmR-nwVl0aA",
    "https://disk.yandex.ru/i/wfxrh1dGXVSZhA",
    "https://disk.yandex.ru/i/eF8sPxfN7zK8_w",
    "https://disk.yandex.ru/i/VwI1szpo2XD_Ng",
    "https://disk.yandex.ru/i/WX4MUIc7OsAR5g",
    "https://disk.yandex.ru/i/ClReyWAp8SbzeA",
    "https://disk.yandex.ru/i/XYUEUflKtyKysw",
    "https://disk.yandex.ru/i/tCL_01Yp3R7SQw",
    "https://disk.yandex.ru/i/9HxrIVUhxrg9pQ",   
    "https://disk.yandex.ru/i/-y-Rz_p9QGn8-g",
    "https://disk.yandex.ru/i/kNNwbfINfEi3UQ",
    "https://disk.yandex.ru/i/LSdlgoOYss3tIg",
    "https://disk.yandex.ru/i/hZPj3OoIN_PI7w",
    "https://disk.yandex.ru/i/P2OupYx_sEBmEQ",
    "https://disk.yandex.ru/i/JSbEfkQK_ih5iQ",
    "https://disk.yandex.ru/i/cs-lkHjf2rOQ9g",
    "https://disk.yandex.ru/i/GrfCtYaAvOMR8w",
    "https://disk.yandex.ru/i/xsE6Fstw8xoK_g",
    "https://disk.yandex.ru/i/ZOqskY_okJaSNw",
    "https://disk.yandex.ru/i/S3wox7U1o9yw6A",
    "https://disk.yandex.ru/i/gnRc4lbGtrA7gA",
    "https://disk.yandex.ru/i/pufipYa9RjPeTQ",
    "https://disk.yandex.ru/i/XQbURiAllj0cVw",
    "https://disk.yandex.ru/i/eKKHTF_vPlQblg",
    "https://disk.yandex.ru/i/EYgQv2wNH7b85Q",
    "https://disk.yandex.ru/i/lydkWdj7OMqEGw",
    "https://disk.yandex.ru/i/fx9TQbZgTGZz5Q",
    "https://disk.yandex.ru/i/QjkXiQ5G76chmQ",
    "https://disk.yandex.ru/i/ZxHXV-K6fFTtKQ",
    "https://disk.yandex.ru/i/JzKzVWa-ofCgRQ"
]
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
'''
 async def generate_image_with_text(image_url: str, headline: str) -> BytesIO:
    output = replicate.run(
        "fofr/eyecandy:db21d39fdc00c2f578263b218505b26de1392f58a9ad6d17d2166bda9a49d8c1",
        input={
            "image": image_url,
            "prompt": headline,
            "font": "Anton",
            "text_color": "white",
            "outline_color": "black"
        }
    )
'''
    # Получаем ссылку на сгенерированное изображение
    result_url = output["image"] if isinstance(output, dict) else output

    # Загружаем изображение по этой ссылке
    async with aiohttp.ClientSession() as session:
        async with session.get(result_url) as resp:
            if resp.status == 200:
                return BytesIO(await resp.read())
            else:
                raise Exception(f"Ошибка загрузки изображения: {resp.status}")
                
# Обработчик команды /getpost
@dp.message(Command("getpost"))
async def handle_getpost(message: Message):
    try:
        # Шаг 1: сформировать пост
        prompt = f"Для Telegram-канала тематики Инвестиции для новичков сделай пост на тему {today_topic}"
        post_text = await generate_post(prompt)
        await message.answer(post_text)

        # Шаг 2: сформировать короткий заголовок
        headline_prompt = (
            f"Прочитай текст ниже и придумай к нему короткий заголовок (1-3 слова), отражающий суть. "
            f"Пиши только заголовок, без кавычек и пояснений.\n\n{post_text}"
        )
        headline = await generate_post(headline_prompt)
        headline = headline.strip()

        await message.answer(f"<b>{headline}</b>")

        # Шаг 3: выбрать случайный фон
        background_url = random.choice(background_urls)

        # Шаг 4: создать изображение с текстом
      #  image_bytes = await generate_image_with_text(headline, background_url)

        # Шаг 5: отправить изображение
      #  await message.answer_photo(types.InputFile(image_bytes, filename="poster.jpg"))

    except Exception as e:
        await message.answer(f"Ошибка при генерации поста:\n\n{str(e)}")

# Основная функция запуска бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
