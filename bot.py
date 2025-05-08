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
            f"Пиши только заголовок, без кавычек и пояснений:\n\n{post_text}"
        )
        headline = await generate_post(headline_prompt)
        clean_headline = headline.strip()
        await message.answer(f"<b>{clean_headline}</b>")

        # Шаг 3: выбрать случайную картинку из /backgrounds
        import random
        from pathlib import Path
        background_dir = Path("backgrounds")
        images = list(background_dir.glob("*.jpg")) + list(background_dir.glob("*.png"))
        if not images:
            await message.answer("Нет доступных фоновых изображений.")
            return
        selected_image_path = random.choice(images)

        # Шаг 4: отправить запрос к Replicate
        from replicate import Client
        import io

        replicate_client = Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

        with open(selected_image_path, "rb") as img_file:
            img_bytes = img_file.read()

        # Замените на нужную модель, если используете другую
        output = replicate_client.run(
            "chrisgorgo/text-to-image-on-image",
            input={
                "image": img_bytes,
                "text": clean_headline,
                "text_color": "white",
                "outline_color": "black",
                "font_size": 42
            }
        )

        # Проверяем результат
        if isinstance(output, list) and output:
            image_url = output[0]
            await message.answer_photo(photo=image_url)
        else:
            await message.answer("Не удалось сгенерировать изображение через нейросеть.")

    except Exception as e:
        await message.answer(f"Ошибка при генерации поста:\n\n{str(e)}")
