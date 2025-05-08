# image_generator.py

import os
import random
import replicate

# Папка с изображениями на GitHub
BACKGROUND_DIR = "backgrounds"  # локальная папка или путь к скачанным фонам
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# Модель для генерации текста на изображении (можно заменить на другую)
MODEL_NAME = "lucataco/vision-text-overlay"

# Функция генерации изображения с текстом
def generate_image_with_text(text):
    # Случайное изображение из папки
    image_files = os.listdir(BACKGROUND_DIR)
    if not image_files:
        raise Exception("Фоновые изображения не найдены в папке.")
    selected_image = random.choice(image_files)
    image_path = os.path.join(BACKGROUND_DIR, selected_image)

    with open(image_path, "rb") as f:
        image_data = f.read()

    # Отправка запроса в Replicate
    output = replicate.run(
        f"{MODEL_NAME}",
        input={
            "image": image_data,
            "text": text,
            "text_color": "white",
            "outline_color": "black",
            "font_size": 48,
            "gravity": "center"  # Можно настроить: "north", "south", "center", etc.
        }
    )
    return output  # URL сгенерированного изображения
