import boto3
from PIL import Image
import io
import json
import random
import string

s3 = boto3.client('s3', endpoint_url='https://storage.yandexcloud.net')
sqs = boto3.client('sqs', endpoint_url='https://message-queue.api.cloud.yandex.net')

QUEUE_URL = 'https://message-queue.api.cloud.yandex.net/b1gk0l897h6p4jnm5nmo/aoek3m6f3s8e8u7jv64a/vvot44-task'
INPUT_BUCKET = 'vvot44-photo'
OUTPUT_BUCKET = 'vvot44-faces'


def lambda_handler(event, context):
    print("Получено событие:", json.dumps(event))  # Логируем входящее событие
    messages = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=10)

    if 'Messages' not in messages:
        print("Очередь пуста. Нет задач для обработки.")
        return {"statusCode": 200, "body": "OK"}

    for message in messages['Messages']:
        receipt_handle = message['ReceiptHandle']
        body = json.loads(message['Body'])
        file_name = body['file_name']
        face_coordinates = body['face_coordinates']

        print(f"Обработка задачи: файл {file_name}, координаты лица: {face_coordinates}")  # Логируем задачу

        # Загружаем изображение с S3
        image = download_image_from_s3(file_name)
        if image is None:
            print(f"Ошибка загрузки изображения: {file_name}")
            continue

        # Обрезаем лицо
        x, y, w, h = face_coordinates
        face_image = crop_face(image, x, y, w, h)
        if face_image is None:
            print(f"Ошибка обрезки лица: {file_name}")
            continue

        # Генерируем случайное имя для нового файла
        new_file_name = generate_random_key() + '.jpg'
        print(f"Сохранение обрезанного лица: {new_file_name}")  # Логируем сохранение

        # Сохраняем обрезанное лицо в бакет
        save_face_to_s3(face_image, new_file_name)

        # Удаляем сообщение из очереди
        sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt_handle)
        print(f"Задача завершена и удалена из очереди: {file_name}")

    return {"statusCode": 200, "body": "OK"}


def download_image_from_s3(key):
    try:
        response = s3.get_object(Bucket=INPUT_BUCKET, Key=key)
        image_data = response['Body'].read()
        return Image.open(io.BytesIO(image_data))
    except Exception as e:
        print(f"Ошибка загрузки изображения из S3: {e}")
        return None


def crop_face(image, x, y, w, h):
    try:
        return image.crop((x, y, x + w, y + h))
    except Exception as e:
        print(f"Ошибка обрезки лица: {e}")
        return None


def generate_random_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))


def save_face_to_s3(image, file_name):
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    try:
        s3.put_object(Bucket=OUTPUT_BUCKET, Key=file_name, Body=buffer.getvalue(), ContentType='image/jpeg')
        print(f"Изображение успешно сохранено в бакет: {file_name}")  # Логируем успешное сохранение
    except Exception as e:
        print(f"Ошибка сохранения изображения в S3: {e}")