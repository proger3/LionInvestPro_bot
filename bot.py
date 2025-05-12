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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
logger.info(f'Сегодня {today}, тема: {today_topic}')

# Ссылки на фоновые изображения (замените на свои рабочие URL)
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

# Загружаем токены из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("Не заданы обязательные переменные окружения!")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Удаление эмодзи из текста
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

# Генерация текста поста через OpenRouter
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

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                error = await response.text()
                logger.error(f"OpenRouter error: {error}")
                raise Exception(f"Ошибка OpenRouter: {response.status}")
    except Exception as e:
        logger.error(f"Error in generate_post: {str(e)}", exc_info=True)
        raise

# Генерация изображения с текстом
async def generate_image_with_text(image_url: str, headline: str) -> BytesIO:
    try:
        logger.info(f"Generating image with text: {headline[:30]}...")
        
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
        
        result_url = output if isinstance(output, str) else output.get("image", "")
        if not result_url:
            raise Exception("Replicate не вернул URL изображения")

        async with aiohttp.ClientSession() as session:
            async with session.get(result_url) as resp:
                if resp.status == 200:
                    return BytesIO(await resp.read())
                raise Exception(f"Ошибка загрузки: {resp.status}")
                
    except Exception as e:
        logger.error(f"Error in generate_image_with_text: {str(e)}", exc_info=True)
        raise

# Обработчик команды /getpost
@dp.message(Command("getpost"))
async def handle_getpost(message: Message):
    try:
        # 1. Генерация текста поста
        logger.info("Generating post text...")
        post_text = await generate_post(f"Создай пост для Telegram на тему: {today_topic}. Пиши интересно и понятно.")
        await message.answer(post_text)

        # 2. Создание заголовка
        logger.info("Generating headline...")
        headline = await generate_post(
            f"Придумай короткий (1-3 слова) броский заголовок для этого поста:\n\n{post_text}\n\n"
            "Пиши только заголовок без кавычек и пояснений."
        )
        headline = remove_emojis(headline).strip('"').strip()
        await message.answer(f"<b>Заголовок:</b> {headline}")

        # 3. Выбор случайного фона
        background_url = random.choice(background_urls)
        logger.info(f"Selected background: {background_url}")
        
        # 4. Генерация и отправка изображения
        logger.info("Generating final image...")
        image_bytes = await generate_image_with_text(background_url, headline)
        
        try:
            await message.answer_photo(
                types.InputFile(image_bytes, filename="post.jpg"),
                caption=headline
            )
        finally:
            image_bytes.close()

    except Exception as e:
        logger.error(f"Error in handle_getpost: {str(e)}", exc_info=True)
        await message.answer(f"⚠️ Произошла ошибка при создании поста. Попробуйте позже.")

# Тестовая команда для проверки изображений
@dp.message(Command("test_image"))
async def test_image(message: Message):
    try:
        url = random.choice(background_urls)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    await message.answer_photo(types.InputFile(BytesIO(await resp.read())))
                else:
                    await message.answer(f"Ошибка загрузки: HTTP {resp.status}")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")

# Запуск бота
async def main():
     logger.info("Starting bot...")
    
    # Удаляем старые webhooks (если были)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
