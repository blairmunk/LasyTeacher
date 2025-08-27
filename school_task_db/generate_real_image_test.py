# generate_real_image_test.py
import uuid
import json
import base64
from PIL import Image, ImageDraw
import io

# Создаем простое тестовое изображение
def create_test_graph():
    # Создаем изображение 400x300
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # Рисуем оси координат
    draw.line([(50, 250), (350, 250)], fill='black', width=2)  # X axis
    draw.line([(50, 50), (50, 250)], fill='black', width=2)   # Y axis
    
    # Рисуем параболу y = x^2 - 5x + 6 = (x-2)(x-3)
    points = []
    for x in range(0, 6):
        y = x*x - 5*x + 6
        # Масштабируем координаты для изображения
        screen_x = 50 + x * 50  # 50 пикселей на единицу
        screen_y = 250 - y * 20  # 20 пикселей на единицу, инвертируем Y
        points.append((screen_x, screen_y))
    
    # Рисуем кривую
    for i in range(len(points)-1):
        draw.line([points[i], points[i+1]], fill='blue', width=3)
    
    # Отмечаем корни x=2 и x=3
    draw.ellipse([(50 + 2*50 - 5, 250-5), (50 + 2*50 + 5, 250+5)], fill='red')  # x=2
    draw.ellipse([(50 + 3*50 - 5, 250-5), (50 + 3*50 + 5, 250+5)], fill='red')  # x=3
    
    # Сохраняем в памяти как PNG
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer.getvalue()

# Генерируем изображение
image_data = create_test_graph()
base64_string = base64.b64encode(image_data).decode('utf-8')

# Создаем UUID для тестирования
group_uuid = str(uuid.uuid4())
task_uuid = str(uuid.uuid4())  
image_uuid = str(uuid.uuid4())

# Создаем JSON с реальным изображением
test_data = {
    "format_version": "1.0",
    "metadata": {
        "description": "Тест импорта РЕАЛЬНОГО изображения",
        "created_at": "2024-08-26T20:00:00Z"
    },
    "topics": [
        {
            "name": "Квадратные уравнения",
            "subject": "Математика",
            "grade_level": 8,
            "section": "Алгебра"
        }
    ],
    "analog_groups": [
        {
            "id": group_uuid,
            "name": "Квадратные уравнения с графиками",
            "description": "Задания с реальными изображениями графиков"
        }
    ],
    "tasks": [
        {
            "id": task_uuid,
            "text": "На рисунке изображен график функции y = x² - 5x + 6. Найдите корни уравнения x² - 5x + 6 = 0.",
            "answer": "x₁ = 2, x₂ = 3",
            "short_solution": "Корни функции — это точки пересечения с осью X",
            "topic": {
                "name": "Квадратные уравнения",
                "subject": "Математика", 
                "grade_level": 8
            },
            "groups": [group_uuid]
        }
    ],
    "task_images": [
        {
            "id": image_uuid,
            "task_uuid": task_uuid,
            "filename": "quadratic_graph.png",
            "base64_data": f"data:image/png;base64,{base64_string}",
            "position": "right_40",
            "caption": "График функции y = x² - 5x + 6",
            "order": 1
        }
    ]
}

# Сохраняем тестовый файл
with open('test_real_image.json', 'w', encoding='utf-8') as f:
    json.dump(test_data, f, ensure_ascii=False, indent=2)

print("✅ Создан файл test_real_image.json с реальным изображением")
print(f"📊 Размер base64: {len(base64_string)} символов")
print(f"🖼️ Размер изображения: {len(image_data)} байт")
print(f"Task UUID: {task_uuid}")
print(f"Image UUID: {image_uuid}")
