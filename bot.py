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
# Кэшируем результаты проверки
from functools import lru_cache

@lru_cache(maxsize=32)
async def get_image(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()
            
# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("Не заданы обязательные переменные окружения!")

# Инициализация бота (сессия будет создана при запуске)
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

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

# Ссылки на фоновые изображения

# Ссылки на фоновые изображения (замените на свои рабочие URL)
background_urls = [
    "https://i.ibb.co/bjDyM39N/1.png"
    "https://i.ibb.co/gbn4mq0L/2.png"
    "https://i.ibb.co/dwr85Wvb/3.png"
    "https://i.ibb.co/0pqTmWJ4/4.png"
    "https://i.ibb.co/Xrt3N4Xx/5.png"
    "https://i.ibb.co/NdCxnnQs/6.png"
    "https://i.ibb.co/7dqm37hX/7.png"
    "https://i.ibb.co/sdjjt4BL/8.png"
    "https://i.ibb.co/C3Jwq9Kw/9.png"
    "https://i.ibb.co/847ZNS07/10.png"
    "https://i.ibb.co/35BQPfnP/11.png"
    "https://i.ibb.co/Kp0XsJWH/12.png"
    "https://i.ibb.co/PvWFp2Yv/13.png"
    "https://i.ibb.co/jkWpPJ9R/14.png"
    "https://i.ibb.co/v447B9Pd/14-31.png"
    "https://i.ibb.co/Y7Ddhm0b/15.png"
    "https://i.ibb.co/d0TwNPnN/16.png"
    "https://i.ibb.co/XTrZ6PM/17.png"
    "https://i.ibb.co/5hK7PD2Q/18.png"
    "https://i.ibb.co/pjHxzxYt/19.png"
    "https://i.ibb.co/jvNrckxz/20.png"
    "https://i.ibb.co/RGCNgKGs/21.png"
    "https://i.ibb.co/MDXX4m7g/22.png"
    "https://i.ibb.co/fzf521M0/23.png"
    "https://i.ibb.co/bwwffVg/24.png"
    "https://i.ibb.co/bgxbpgDN/25.png"
    "https://i.ibb.co/tT0b5cZp/26.png"
    "https://i.ibb.co/fYB6RbXF/27.png"
    "https://i.ibb.co/1f1wSTSh/28.png"
    "https://i.ibb.co/r29pJ22q/29.png"
    "https://i.ibb.co/1tLHk4jp/30.png"
]

#Проверка правильности ссылки на фотку
async def validate_images():
    broken = []
    async with aiohttp.ClientSession() as session:
        for url in background_urls:
            try:
                async with session.head(url) as resp:
                    if resp.status != 200:
                        broken.append(url)
            except:
                broken.append(url)
    if broken:
        logger.warning(f"Broken images: {broken}")
        
# Удаление эмодзи
def remove_emojis(text):
    emoji_pattern = re.compile("["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002700-\U000027BF"
        "]+", flags=re.UNICODE)
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
        # Бесплатная модель (не требует карты)
        model_version = "stability-ai/sdxl-lite@af1a68a91b0b9a00b5e05a7b7dfa80f6d0b05b6b"
        
        output = replicate.run(
            model_version,
            input={
                "prompt": f"Профессиональный фон с текстом: '{headline}'",
                "negative_prompt": "text, blurry",
                "width": 1024,
                "height": 512
            }
        )
        
        result_url = output[0]  # SDXL возвращает список ссылок
        async with aiohttp.ClientSession() as session:
            async with session.get(result_url) as resp:
                return BytesIO(await resp.read())
                
    except Exception as e:
        logger.error(f"Ошибка генерации: {str(e)}")
        raise Exception("Не удалось создать изображение")
        
@dp.message(Command("test_model"))
async def test_model(message: Message):
    try:
        model_version = "stability-ai/sdxl:c221b2b8ef527988fb59bf24a8b97c4561f1c671f73bd389f866bfb27c061316"
        
        output = replicate.run(
            model_version,
            input={"prompt": "Test image with text 'Hello World'"}
        )
        
        await message.answer_photo(
            output[0],
            caption="✅ Тест модели успешен!"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        
# Команда /getpost
@dp.message(Command("getpost"))
async def handle_getpost(message: Message):
    try:
        # 1. Получаем текущую тему
        today = datetime.datetime.now().strftime('%A')
        today_topic = topics_by_day.get(today, 'Общая тема')
        logger.info(f"Создание поста по теме: {today_topic}")

        # 2. Генерация текста поста
        try:
            post_text = await asyncio.wait_for(
                generate_post(f"Напиши пост для Telegram на тему '{today_topic}'. Формат: 1-2 абзаца."),
                timeout=30
            )
            if not post_text.strip():
                raise Exception("Пустой текст поста")
            await message.answer(post_text)
        except Exception as e:
            raise Exception(f"Ошибка генерации текста: {str(e)}")

        # 3. Создание заголовка
        try:
            headline = await asyncio.wait_for(
                generate_post(f"Придумай короткий заголовок (2-4 слова) для этого поста:\n\n{post_text}"),
                timeout=20
            )
            headline = remove_emojis(headline).strip('"').strip()
            if not headline:
                raise Exception("Не удалось создать заголовок")
            await message.answer(f"<b>Заголовок:</b> {headline}")
        except Exception as e:
            raise Exception(f"Ошибка генерации заголовка: {str(e)}")

        # 4. Выбор и проверка изображения
        try:
            bg_url = random.choice(background_urls)
            logger.info(f"Выбрано фоновое изображение: {bg_url}")
            
            # 5. Генерация картинки
            image_bytes = await asyncio.wait_for(
                generate_image_with_text(bg_url, headline),
                timeout=60
            )
            
            if not image_bytes:
                raise Exception("Не удалось сгенерировать изображение")

            # 6. Отправка результата
            try:
                await message.answer_photo(
                    types.InputFile(image_bytes, filename="post.jpg"),
                    caption=headline
                )
            finally:
                image_bytes.close()
                
        except Exception as e:
            raise Exception(f"Ошибка работы с изображением: {str(e)}")

    except Exception as e:
        error_msg = f"⚠️ Ошибка при создании поста:\n{str(e)[:300]}"
        logger.error(error_msg, exc_info=True)
        await message.answer(error_msg)

# Команда /test
@dp.message(Command("test"))
async def test_cmd(message: Message):
    await message.answer("✅ Бот работает!")

# Управление запуском
async def on_startup():
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started")

async def on_shutdown():
    """Корректное завершение работы бота"""
    try:
        # Закрываем сессию бота
        session = await bot.session
        await session.close()
        logger.info("Сессия бота закрыта")
        
        # Дополнительные очистки (если нужно)
        await dp.storage.close()
        logger.info("Хранилище диспетчера закрыто")
    except Exception as e:
        logger.error(f"Ошибка при завершении: {str(e)}", exc_info=True)
    finally:
        logger.info("Бот завершил работу")

async def main():
    """Основной цикл бота"""
    try:
        # Для Render: ждем завершения старых процессов
        await asyncio.sleep(2)
        
        # Очистка предыдущих вебхуков
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Вебхуки очищены")
        
        # Запуск поллинга
        logger.info("Запускаем поллинг...")
        await dp.start_polling(bot)
        
    except asyncio.CancelledError:
        logger.info("Поллинг отменён")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}", exc_info=True)
    finally:
        await on_shutdown()
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную")
    except Exception as e:
        logger.critical(f"Фатальная ошибка: {str(e)}", exc_info=True)
