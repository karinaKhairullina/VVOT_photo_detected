import json
import os
import cv2
import numpy as np
from yandex.cloud import storage

def handler(event, context):
    task = event
    image_key = task["image_key"]
    face_coordinates = task["face_coordinates"]
    access_key = os.environ['ACCESS_KEY']
    secret_key = os.environ['SECRET_KEY']

    # Инициализация клиента Yandex Storage
    storage_client = storage.Client(access_key=access_key, secret_key=secret_key)

    # Скачиваем оригинальное изображение
    bucket_name = "vvot44-photos"
    object_data = storage_client.get_object(bucket_name, image_key)
    image_bytes = object_data.read()

    # Обработка изображения
    np_image = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
    x, y, w, h = face_coordinates["x"], face_coordinates["y"], face_coordinates["width"], face_coordinates["height"]
    face = image[y:y+h, x:x+w]

    # Сохранение лица
    bucket_name_faces = "vvot44-faces"
    face_file_name = f"face_{image_key.split('.')[0]}_{x}_{y}.jpg"
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    _, encoded_face = cv2.imencode('.jpg', face, encode_param)
    storage_client.put_object(bucket_name_faces, face_file_name, encoded_face.tobytes())

    # Сохранение метаданных
    save_metadata(image_key, face_file_name)

    return json.dumps({"message": "Face cut and saved."})

def save_metadata(original_image_key, face_image_key):
    # Сохранение метаданных в базу данных
    pass
