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
from aiogram.types import BufferedInputFile
from aiogram.enums import ParseMode   
from aiogram.filters import Command
import re
# Кэшируем результаты проверки
from functools import lru_cache
from dotenv import load_dotenv
from aiogram import __version__ as aiogram_version
#from replicate import __version__ as replicate_version
from importlib.metadata import version  # Для получения версий
from PIL import Image, ImageDraw, ImageFont
import textwrap

try:
    replicate_version = version('replicate')
except:
    replicate_version = "unknown"

load_dotenv()

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

# Получаем версии
REPLICATE_VERSION = version('replicate')
AIOGRAM_VERSION = version('aiogram')

# Конфигурация
REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY")
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
    "https://i.ibb.co/bjDyM39N/1.png",
    "https://i.ibb.co/gbn4mq0L/2.png",
    "https://i.ibb.co/dwr85Wvb/3.png",
    "https://i.ibb.co/0pqTmWJ4/4.png",
    "https://i.ibb.co/Xrt3N4Xx/5.png",
    "https://i.ibb.co/NdCxnnQs/6.png",
    "https://i.ibb.co/7dqm37hX/7.png",
    "https://i.ibb.co/sdjjt4BL/8.png",
    "https://i.ibb.co/C3Jwq9Kw/9.png",
    "https://i.ibb.co/847ZNS07/10.png",
    "https://i.ibb.co/35BQPfnP/11.png",
    "https://i.ibb.co/Kp0XsJWH/12.png",
    "https://i.ibb.co/PvWFp2Yv/13.png",
    "https://i.ibb.co/jkWpPJ9R/14.png",
    "https://i.ibb.co/v447B9Pd/14-31.png",
    "https://i.ibb.co/Y7Ddhm0b/15.png",
    "https://i.ibb.co/d0TwNPnN/16.png",
    "https://i.ibb.co/XTrZ6PM/17.png",
    "https://i.ibb.co/5hK7PD2Q/18.png",
    "https://i.ibb.co/pjHxzxYt/19.png",
    "https://i.ibb.co/jvNrckxz/20.png",
    "https://i.ibb.co/RGCNgKGs/21.png",
    "https://i.ibb.co/MDXX4m7g/22.png",
    "https://i.ibb.co/fzf521M0/23.png",
    "https://i.ibb.co/bwwffVg/24.png",
    "https://i.ibb.co/bgxbpgDN/25.png",
    "https://i.ibb.co/tT0b5cZp/26.png",
    "https://i.ibb.co/fYB6RbXF/27.png",
    "https://i.ibb.co/1f1wSTSh/28.png",
    "https://i.ibb.co/r29pJ22q/29.png",
    "https://i.ibb.co/1tLHk4jp/30.png",
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
async def generate_image_with_text(headline: str) -> BytesIO:
    try:
        bg_url = random.choice(background_urls)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(bg_url) as resp:
                if resp.status != 200:
                    raise Exception(f"Ошибка загрузки фона: HTTP {resp.status}")
                bg_data = await resp.read()

        with Image.open(BytesIO(bg_data)) as img:
            draw = ImageDraw.Draw(img)
            
            # Шрифт и текст
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except:
                font = ImageFont.load_default()
            
            # Современный способ расчета размера текста
            bbox = draw.textbbox((0, 0), headline, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Позиционирование по центру
            x = (img.width - text_width) / 2
            y = (img.height - text_height) / 2
            
            draw.text((x, y), headline, fill="white", font=font)
            
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=85)
            buf.seek(0)
            return buf
            
    except Exception as e:
        logger.error(f"Ошибка генерации изображения: {str(e)}")
        raise Exception(f"Ошибка создания изображения: {str(e)[:200]}")

#Проверка версий
@dp.message(Command("versions"))
async def show_versions(message: Message):
    versions = {
        "Aiogram": version('aiogram'),
        "Replicate": version('replicate'),
        "Python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }
    await message.answer("\n".join(f"{k}: {v}" for k,v in versions.items()))
    
#Проверка ключа
@dp.message(Command("check_key"))
async def check_key(message: Message):
    try:
        client = replicate.Client(api_token=REPLICATE_API_KEY)
        models = client.models.list()
        await message.answer(f"✅ Ключ действителен! Доступно моделей: {len(list(models))}")
    except Exception as e:
        await message.answer(f"❌ Ошибка ключа: {str(e)}")
        
#Проверка Replicate
@dp.message(Command("check_replicate"))
async def check_replicate(message: Message):
    try:
        client = replicate.Client(api_token=REPLICATE_API_KEY)
        
        # Получаем первую модель (без параметра limit)
        models = list(client.models.list())
        model = models[0] if models else None
        
        await message.answer(
            f"Replicate Status:\n"
            f"• Models available: {len(models)}\n"
            f"• First model: {model.id if model else 'None'}\n"
            f"• API Key: {REPLICATE_API_KEY[:5]}...{REPLICATE_API_KEY[-3:]}"
        )
    except Exception as e:
        await message.answer(f"Replicate check failed: {str(e)}")

#Провекра ключа Replicate
@dp.message(Command("validate_key"))
async def validate_key(message: Message):
    try:
        # Проверяем ключ через реальный запрос
        client = replicate.Client(api_token=REPLICATE_API_KEY)
        models = client.models.list(limit=1)
        
        if models:
            await message.answer("✅ Ключ действителен! Доступные модели:")
            for model in models[:3]:
                await message.answer(f"- {model.name}")
        else:
            await message.answer("⚠️ Ключ работает, но нет доступа к моделям")
            
    except Exception as e:
        await message.answer(f"❌ Недействительный ключ: {str(e)}")
        logger.error(f"Invalid Replicate key: {REPLICATE_API_KEY[:5]}...")

#проверка доступных моделей
@dp.message(Command("free_models"))
async def list_free_models(message: Message):
    free_models = [
        "stability-ai/sdxl-lite",
        "bytedance/sdxl-lightning",
        "fofr/sdxl-emoji"  # Примеры бесплатных моделей
    ]
    await message.answer("Бесплатные модели:\n" + "\n".join(free_models))
    
#Диагностика ошибки
@dp.message(Command("debug_image"))
async def debug_image(message: Message):
    try:
        # Тестовые параметры
        test_text = "Тест " + datetime.now().strftime("%H:%M:%S")
        
        # Проверка доступности модели
        model = replicate.models.get("stability-ai/sdxl")
        await message.answer(f"🔄 Модель {model.name} доступна")
        
        # Генерация изображения
        image_bytes = await generate_image_with_text("", test_text)  # URL не нужен для SDXL
        
        # Отправка результата
        await message.answer_photo(
            types.InputFile(image_bytes, filename="test.jpg"),
            caption=f"✅ Сгенерировано: {test_text}"
        )
        
    except Exception as e:
        await message.answer(f"🔴 Ошибка:\n{str(e)[:300]}")
        
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
        post_text = await generate_post(
            f"Напиши пост для Telegram на тему '{today_topic}'. Формат: 1-2 абзаца."
        )
        if not post_text.strip():
            raise Exception("Пустой текст поста")
        
        await message.answer(post_text)

        # 3. Создание заголовка
        headline = await generate_post(
            f"Придумай короткий заголовок (2-4 слова) для этого поста:\n\n{post_text}"
        )
        headline = remove_emojis(headline).strip('"').strip()
        if not headline:
            raise Exception("Не удалось создать заголовок")
        
        await message.answer(f"<b>Заголовок:</b> {headline}")

        # 4. Генерация изображения
        bg_url = random.choice(background_urls)
        logger.info(f"Выбрано фоновое изображение: {bg_url}")
        
        image_bytes = await generate_image_with_text(bg_url, headline)
        
        if not image_bytes:
            raise Exception("Не удалось сгенерировать изображение")

        # 5. Отправка результата
        photo_file = BufferedInputFile(
            file=image_bytes.getvalue(),
            filename="post.jpg"
        )
        
        await message.answer_photo(
            photo=photo_file,
            caption=headline
        )

    except Exception as e:
        error_msg = f"⚠️ Ошибка при создании поста:\n{str(e)[:300]}"
        logger.error(error_msg, exc_info=True)
        await message.answer(error_msg)

# Команда /test
@dp.message(Command("test"))
async def test_cmd(message: Message):
    await message.answer("✅ Бот работает!")
#Проверка API-ключа
@dp.message(Command("check_key"))
async def check_key(message: Message):
    valid = False
    try:
        client = replicate.Client(api_token=REPLICATE_API_KEY)
        client.models.list()  # Проверяем доступ
        valid = True
    except:
        pass
    await message.answer(f"🔑 Ключ Replicate: {'✅ Рабочий' if valid else '❌ Недействительный'}")

#Список доступных моделей
@dp.message(Command("list_models"))
async def list_models(message: Message):
    try:
        client = replicate.Client(api_token=REPLICATE_API_KEY)
        models = [m.name for m in client.models.list()][:10]
        await message.answer(f"Доступные модели:\n" + "\n".join(models))
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
        
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

async def init_services():
    """Инициализация и проверка всех зависимостей"""
    try:
        # Проверка наличия ключей
        if not REPLICATE_API_KEY:
            raise ValueError("REPLICATE_API_KEY не задан")

        # Создаем синхронный клиент для проверки
        client = replicate.Client(api_token=REPLICATE_API_KEY)
        
        # Получаем список моделей
        try:
            models = list(client.models.list())
            if not models:
                raise ConnectionError("Replicate не вернул модели")
            logger.info(f"Replicate доступен. Первая модель: {models[0].id}")
            return True
        except Exception as e:
            raise ConnectionError(f"Ошибка Replicate API: {str(e)}")

    except Exception as e:
        logger.critical(f"Сервисы не инициализированы: {str(e)}", exc_info=True)
        raise
        
async def shutdown():
    """Корректное завершение всех подключений"""
    try:
        tasks = []
        
        # Закрытие сессии бота
        if hasattr(bot, 'session'):
            tasks.append(bot.session.close())
        
        # Закрытие хранилища диспетчера
        if hasattr(dp, 'storage'):
            tasks.append(dp.storage.close())
        
        # Другие подключения (например Redis)
        # if 'redis' in globals():
        #     tasks.append(redis.close())
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Все сервисы корректно остановлены")
    except Exception as e:
        logger.error(f"Ошибка при завершении работы: {str(e)}", exc_info=True)
        
async def main():
    """Основной цикл работы бота"""
    try:
        # 1. Принудительная очистка
        if hasattr(bot, 'session'):
            await bot.session.close()
            await asyncio.sleep(3)  # Для Render
        
        # 2. Очистка вебхуков
        await bot.delete_webhook(drop_pending_updates=True)
        
        # 3. Инициализация сервисов
        await init_services()
        
        # 4. Запуск бота
        logger.info("Запускаем поллинг...")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            close_bot_session=False  # Теперь закрываем вручную в shutdown()
        )
        
    except asyncio.CancelledError:
        logger.info("Поллинг отменен")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}", exc_info=True)
    finally:
        await shutdown()
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную")
    except Exception as e:
        logger.critical(f"Фатальная ошибка: {str(e)}", exc_info=True)
