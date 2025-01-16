import json
import cv2
import requests

def handler(event, context):
    # Получаем URL изображения из event
    image_data = event["body"]
    image_url = image_data["key"]  # Получаем ссылку на фото

    # Логика для распознавания лиц
    faces = detect_faces(image_url)  # detect_faces - функция распознавания лиц

    tasks = []
    for face in faces:
        task = {
            "photo_key": image_url,
            "face_coordinates": face
        }
        tasks.append(task)

    # Отправка задач в очередь
    send_to_queue(tasks)
    return {"statusCode": 200, "body": json.dumps({"message": "Face detection complete"})}

def detect_faces(image_url):
    # Здесь должна быть логика для распознавания лиц (например, через OpenCV)
    # Возвращаем список координат лиц
    return [{"x": 10, "y": 20, "width": 100, "height": 100}]  # Пример
