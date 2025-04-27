import asyncio
import os
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import Command

from openai import OpenAI  # добавлено

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # добавлено

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_API_KEY)  # добавлено

async def main():
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())
