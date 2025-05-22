import random
import asyncio
import os
import logging
import datetime
import aiohttp
from io import BytesIO
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, BufferedInputFile
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram import Router
from PIL import Image, ImageDraw, ImageFont
import sqlite3
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Не задан BOT_TOKEN!")

# Создаем роутер после инициализации бота
router = Router()

# Затем подключаем роутер к диспетчеру
dp.include_router(router)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Ссылки на фоновые изображения
background_urls = [
    "https://i.ibb.co/bjDyM39N/1.png",
    "https://i.ibb.co/gbn4mq0L/2.png",
    # ... остальные URL ...
]

# Инициализация БД
# Инициализация БД с логгированием
def init_db():
    try:
        conn = sqlite3.connect("posts.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id INTEGER PRIMARY KEY,
                chat_id INTEGER,
                post_text TEXT,
                image_data BLOB,
                scheduled_time DATETIME
            )
        """)
        conn.commit()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
    finally:
        conn.close()


# Генерация совета по инвестициям
def generate_investment_advice():
    topics = [
        "Как начать инвестировать с маленькой суммой?",
        "ТОП-5 ошибок начинающих инвесторов",
        "Куда вложить 10 000 рублей в этом году?",
        "Акции vs Облигации: что выбрать новичку?",
        "Как диверсифицировать портфель?"
    ]
    
    tips = [
        "Начните с ETF – это просто и безопасно.",
        "Не вкладывайте все деньги в один актив.",
        "Регулярно пополняйте инвестиционный счёт.",
        "Изучайте компанию перед покупкой её акций.",
        "Используйте сложный процент – ваш лучший друг."
    ]
    
    post = (
        f"📈 {random.choice(topics)}\n\n"
        f"🔹 {random.choice(tips)}\n"
        f"🔹 {random.choice(tips)}\n\n"
        f"#Инвестиции #Финансы #СоветыНовичкам"
    )
    
    return post

# Получение случайного фона
async def get_investment_background():
    return random.choice(background_urls)

# Генерация изображения с текстом
async def generate_image_with_text(bg_url: str, headline: str) -> BytesIO:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(bg_url) as resp:
                if resp.status != 200:
                    raise Exception(f"Ошибка загрузки фона: HTTP {resp.status}")
                bg_data = await resp.read()

        with Image.open(BytesIO(bg_data)) as img:
            draw = ImageDraw.Draw(img)
            font_size = 74
            
            try:
                font = ImageFont.truetype("arialbd.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                    font.size = font_size

            text_color = (255, 255, 0)  # Жёлтый
            outline_color = (0, 0, 0)   # Чёрная обводка

            # Разбиваем текст на строки
            max_width = img.width * 0.8
            lines = []
            current_line = ""
            
            for word in headline.split():
                test_line = f"{current_line} {word}".strip()
                bbox = draw.textbbox((0, 0), test_line, font=font)
                test_width = bbox[2] - bbox[0]
                
                if test_width <= max_width:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            if len(lines) > 3:
                lines = lines[:3]
                lines[-1] = lines[-1][:20] + "..." if len(lines[-1]) > 20 else lines[-1]

            line_spacing = 20
            total_text_height = sum(
                draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1]
                for line in lines
            ) + (len(lines) - 1) * line_spacing
            
            y = (img.height - total_text_height) // 2

            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (img.width - text_width) // 2
                
                for x_offset, y_offset in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                    draw.text((x + x_offset, y + y_offset), line, 
                             fill=outline_color, font=font)
                
                draw.text((x, y), line, fill=text_color, font=font)
                y += (bbox[3] - bbox[1]) + line_spacing

            buf = BytesIO()
            img.save(buf, format="JPEG", quality=95)
            buf.seek(0)
            return buf
            
    except Exception as e:
        logger.error(f"Ошибка генерации изображения: {str(e)}")
        raise

# Проверка запланированных постов
async def check_scheduled_posts():
    try:
        conn = sqlite3.connect("posts.db")
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Проверка запланированных постов (текущее время: {now})")
        
        cursor.execute(
            "SELECT id, chat_id, post_text, image_data FROM scheduled_posts WHERE scheduled_time <= datetime('now')"
        )
        posts = cursor.fetchall()
        
        if not posts:
            logger.info("Нет постов для публикации")
            return
            
        logger.info(f"Найдено {len(posts)} постов для публикации")
        
        for post_id, chat_id, post_text, image_data in posts:
            try:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=BufferedInputFile(image_data, filename="post.jpg"),
                    caption=post_text
                )
                cursor.execute("DELETE FROM scheduled_posts WHERE id = ?", (post_id,))
                conn.commit()
                logger.info(f"Пост {post_id} опубликован в чате {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка отправки поста {post_id}: {e}")
        
    except Exception as e:
        logger.error(f"Ошибка при проверке запланированных постов: {e}")
    finally:
        if conn:
            conn.close()
            

# Команда /getpost
# Теперь можно использовать декоратор @router
@router.message(Command("getpost"))
async def cmd_getpost(message: types.Message):
    try:
        # 1. Генерация поста
        post_text = generate_investment_advice()
        bg_url = random.choice(background_urls)
        
        # 2. Создаем изображение
        image_with_text = await generate_image_with_text(bg_url, post_text)
        
        # 3. Отправляем превью
        await message.answer_photo(
            types.BufferedInputFile(
                image_with_text.getvalue(),
                filename="preview.jpg"
            ),
            caption=f"🔹 Превью поста:\n\n{post_text}"
        )
        
        # 4. Сохраняем в БД для отложенной публикации
        scheduled_time = datetime.now().replace(
            hour=9, minute=0, second=0
        ) + timedelta(days=1)
        
        conn = sqlite3.connect("posts.db")
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO scheduled_posts (chat_id, post_text, image_data, scheduled_time) VALUES (?, ?, ?, ?)",
                (message.chat.id, post_text, image_with_text.getvalue(), scheduled_time)
            )
            conn.commit()
            await message.answer("✅ Пост добавлен в план на завтра в 9:00!")
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Ошибка в /getpost: {e}", exc_info=True)
        await message.answer("❌ Ошибка генерации поста. Попробуйте позже.")
        
# Периодическая проверка постов
async def scheduler():
    while True:
        await check_scheduled_posts()
        await asyncio.sleep(60)  # Проверка каждую минуту

# Запуск бота
async def main():
    init_db()
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
