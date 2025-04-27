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

if __name__ == "__main__":
    asyncio.run(main())
