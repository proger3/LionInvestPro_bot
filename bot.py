import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import openai
import logging
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
openai.api_key = OPENAI_API_KEY

scheduled_posts = {}

async def generate_post():
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Сгенерируй короткий и интересный пост для Telegram канала про инвестиции."}]
    )
    content = response.choices[0].message["content"]
    scheduled_posts["09:00"] = content
    print(f"[{datetime.now()}] Пост добавлен в план на завтра в 9:00:\n{content}")

async def publish_scheduled_post():
    content = scheduled_posts.pop("09:00", None)
    if content:
        # Тут позже будет отправка в канал. Сейчас просто лог:
        print(f"[{datetime.now()}] Публикация запланированного поста:\n{content}")

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        create_and_schedule_post,
        trigger='cron',
        hour=9,
        minute=0
    )
    scheduler.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
