import replicate
import os
import random
from PIL import Image
import io

# Установи свой API-ключ
os.environ["REPLICATE_API_TOKEN"] = "your_replicate_api_token"

# Путь к папке с фоновыми изображениями
backgrounds_folder = "./backgrounds"

# Получение списка изображений
background_images = [f for f in os.listdir(backgrounds_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]

# Выбор случайного изображения
selected_image = random.choice(background_images)
image_path = os.path.join(backgrounds_folder, selected_image)

# Открытие изображения
with open(image_path, "rb") as img_file:
    image_bytes = img_file.read()

# Заголовок, который нужно разместить
headline = "Финансовая свобода"

# Инициализация клиента Replicate
client = replicate.Client()

# Запуск модели Recraft V3
output = client.run(
    "recraft-ai/recraft-v3",
    input={
        "image": image_bytes,
        "prompt": headline
    }
)

# Сохранение результата
output_image_url = output["image"]
print(f"Сгенерированное изображение доступно по ссылке: {output_image_url}")
