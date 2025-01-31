import boto3
import cv2
import numpy as np
import json
import os
import random

# Создание клиентов через boto3.session.Session
session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net',
    region_name='ru-central1'
)
sqs = session.client(
    service_name='sqs',
    endpoint_url='https://message-queue.api.cloud.yandex.net',
    region_name='ru-central1'
)

QUEUE_URL = 'https://message-queue.api.cloud.yandex.net/b1gk0l897h6p4jnm5nmo/aoek3m6f3s8e8u7jv64a/vvot44-task'


def lambda_handler(event, context):
    print("=== НАЧАЛО ОБРАБОТКИ СОБЫТИЯ ===")
    print(f"Получено событие: {json.dumps(event)}")  # Логируем входящее событие

    # Проверяем, что событие содержит записи
    if 'Records' not in event or len(event['Records']) == 0:
        print("!!! ОШИБКА: Событие не содержит записей.")
        return {"statusCode": 400, "body": "Bad Request: No records found in event"}

    for record in event['Records']:
        try:
            print(f"=== ОБРАБОТКА ЗАПИСИ ===")
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            print(f"Обработка файла: {key} из бакета: {bucket}")  # Логируем имя файла

            # Загружаем фото с S3
            image = download_image_from_s3(bucket, key)
            if image is None:
                print(f" Не удалось загрузить изображение: {key}")
                continue

            # Используем OpenCV для обнаружения лиц
            faces = detect_faces(image)
            if not faces:
                print(f"Лица не обнаружены на изображении: {key}")
                continue

            print(f"Обнаружено {len(faces)} лиц на изображении: {key}")  # Логируем количество лиц
            for face in faces:
                print(f"Координаты лица: {face.tolist()}")  # Логируем координаты каждого лица

            # Отправляем задачи в очередь
            for face in faces:
                send_task_to_queue(key, face.tolist())

        except Exception as e:
            print(f"!!! ОШИБКА при обработке записи: {e}")

    return {"statusCode": 200, "body": "OK"}


def download_image_from_s3(bucket, key):
    try:
        print(f"=== ЗАГРУЗКА ИЗОБРАЖЕНИЯ ===")
        print(f"Попытка загрузить изображение: {key} из бакета: {bucket}")
        response = s3.get_object(Bucket=bucket, Key=key)
        image_data = np.frombuffer(response['Body'].read(), np.uint8)
        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        if image is None:
            print(f"Не удалось декодировать изображение: {key}")
        else:
            print(f"Изображение успешно загружено: {key}")
        return image
    except Exception as e:
        print(f"!!! ОШИБКА при загрузке изображения: {e}")
        return None


def detect_faces(image):
    try:
        print(f"=== ОБНАРУЖЕНИЕ ЛИЦ ===")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
        if not os.path.exists(cascade_path):
            return []
        print(f"Используется файл каскада Хаара: {cascade_path}")
        face_cascade = cv2.CascadeClassifier(cascade_path)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        print(f"Обнаружено {len(faces)} лиц.")
        return faces
    except Exception as e:
        print(f"!!! ОШИБКА при обнаружении лиц: {e}")
        return []


def send_task_to_queue(key, face):
    message = {
        'file_name': key,
        'face_coordinates': face
    }
    try:
        print(f"Подготовленное сообщение для отправки: {message}")
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message)
        )
        print(f"Задача успешно отправлена в очередь: {message}")
    except Exception as e:
        print(f"!!! ОШИБКА при отправке сообщения: {e}")