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

# Ссылки на фоновые изображения (ЗАМЕНИТЕ НА РЕАЛЬНЫЕ ССЫЛКИ!)
background_urls = [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
]

# Загружаем токены
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("Токены не заданы!")

# Инициализация бота
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Удаление эмодзи
def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002700-\U000027BF"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

# Генерация поста
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
            error = await response.text()
            logger.error(f"OpenRouter error: {error}")
            raise Exception(f"Ошибка OpenRouter: {response.status}")

# Генерация изображения
async def generate_image_with_text(image_url: str, headline: str) -> BytesIO:
    try:
        logger.info(f"Starting image generation with URL: {image_url[:50]}...")
        
        # Проверяем, что ссылка валидная
        if not image_url.startswith(('http://', 'https://')):
            raise ValueError("Invalid image URL format")

        output = await asyncio.to_thread(
            replicate.run,
            "fofr/eyecandy:db21d39fdc00c2f578263b218505b26de1392f58a9ad6d17d2166bda9a49d8c1",
            input={
                "image": image_url,
                "prompt": headline,
                "font": "Anton",
                "text_color": "white",
                "outline_color": "black",
                "font_size": 60  # Добавим размер шрифта
            }
        )
        
        # Получаем URL результата
        result_url = output if isinstance(output, str) else output.get("image", "")
        if not result_url:
            raise Exception("Replicate не вернул URL изображения")
        
        logger.info(f"Image generated at: {result_url[:50]}...")

        # Загружаем изображение с таймаутом
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.get(result_url) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Ошибка загрузки изображения: {resp.status} {error_text}")
                
                image_data = await resp.read()
                if not image_data:
                    raise Exception("Получены пустые данные изображения")
                
                return BytesIO(image_data)
                
    except Exception as e:
        logger.error(f"CRITICAL IMAGE ERROR: {str(e)}", exc_info=True)
        raise Exception(f"Не удалось создать изображение: {str(e)}")
# Команда /getpost
@dp.message(Command("getpost"))
async def handle_getpost(message: Message):
    try:
        # 1. Генерация текста поста
        post_text = await generate_post(f"Создай пост на тему: {today_topic}")
        await message.answer(post_text)

        # 2. Генерация заголовка
        headline = await generate_post(f"Создай заголовок (1-3 слова) для: {post_text}")
        headline = remove_emojis(headline).strip('"').strip()
        await message.answer(f"<b>Заголовок:</b> {headline}")

        # 3. Выбор фона
        background_url = random.choice(background_urls)
        
        # 4. Создание изображения
        image_bytes = await generate_image_with_text(background_url, headline)
        try:
            await message.answer_photo(
                types.InputFile(image_bytes, filename="post.jpg"),
                caption=headline
            )
        finally:
            image_bytes.close()

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}", exc_info=True)  # ← 8 пробелов отступа
        await message.answer(f"⚠️ Ошибка при создании поста:\n{str(e)[:200]}")

# Команда /test
@dp.message(Command("test"))
async def test_cmd(message: Message):
    await message.answer("✅ Бот работает!")

@dp.message(Command("test_images"))
async def test_images(message: Message):
    for url in background_urls:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        await message.answer(f"✅ {url[:50]}... работает")
                    else:
                        await message.answer(f"❌ {url[:50]}... ошибка {resp.status}")
        except Exception as e:
            await message.answer(f"❌ {url[:50]}... ошибка: {str(e)}")

@dp.message(Command("test_replicate"))
async def test_replicate(message: Message):
    try:
        output = replicate.run(
            "fofr/eyecandy:db21d39fdc00c2f578263b218505b26de1392f58a9ad6d17d2166bda9a49d8c1",
            input={"image": "https://example.com/image.jpg", "prompt": "Test"}
        )
        await message.answer(f"Replicate работает: {str(output)[:100]}")
    except Exception as e:
        await message.answer(f"Replicate error: {str(e)}")

@dp.message(Command("debug"))
async def cmd_debug(message: Message):
    session = await bot.get_session()
    status = "🟢 Активна" if not session._closed else "🔴 Закрыта"
    await message.answer(
        f"Статус сессии: {status}\n"
        f"Время запуска: {datetime.now()}\n"
        f"Версия бота: 2.0"
    )
    
# Запуск бота
async def on_startup():
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Бот запущен")

# 1. Добавьте этот код ПОСЛЕ создания диспетчера (dp), но ПЕРЕД функцией main()
from aiogram import Dispatcher

async def on_shutdown(dispatcher: Dispatcher):
    """Очистка ресурсов при завершении работы"""
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()
    await bot.session.close()
    logger.info("Bot shutdown completed")

# 2. Модифицируйте функцию main() следующим образом:
async def main():
    import time
    time.sleep(10)  # Ждём завершения старых процессов
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Добавляем проверку активных сессий
    session = await bot.get_session()
    if session._closed:  # Если сессия уже закрыта
        await session.close()  # Принудительно освобождаем
        
    logger.info("Fresh bot instance starting...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
# 3. Измените блок запуска (в самом конце файла):
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
