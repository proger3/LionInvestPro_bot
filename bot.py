openai.api_key = OPENAI_API_KEY
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Пример простого эхо-хендлера (можно убрать, если не нужен)
@dp.message()
async def echo_handler(message: Message):
    await message.answer(f"Ты написал: {message.text}")

# Функция генерации через ChatGPT
async def generate_post():
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "user",
            "content": (
                "Сгенерируй короткий и полезный пост для Telegram-канала на тему личной эффективности. "
                "Объём — до 200 символов."
            )
        }]
    )
    return resp.choices[0].message.content

# Задача по расписанию — каждый день в 9:00 по UTC (12:00 по Москве/Oslo)
@crontab('0 9 * * *')
async def daily_post():
    try:
        text = await generate_post()
        await bot.send_message(CHANNEL_ID, text)
    except exceptions.TelegramAPIError as e:
        print(f"Ошибка при отправке в канал: {e}")

async def main():
    # Убираем вебхуки и запускаем поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот запущен. Ожидаем расписание...")
    while True:
        await asyncio.sleep(3600)  # удерживаем цикл

if __name__ == "__main__":
    asyncio.run(main())
