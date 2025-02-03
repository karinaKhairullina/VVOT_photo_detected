import json
import os
import base64
import boto3
import requests

class AppHandler:
    def __init__(self):
        # Инициализация клиента S3
        self.s3_client = boto3.client(
            service_name="s3",
            aws_access_key_id=os.getenv("ACCESS_KEY"),
            aws_secret_access_key=os.getenv("SECRET_KEY"),
            region_name="ru-central1",
            endpoint_url="https://storage.yandexcloud.net",
        )
        self.telegram_api_url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}"

    def fetch_s3_objects(self, bucket):
        # список объектов из S3
        try:
            response = self.s3_client.list_objects(Bucket=bucket)
            objects = [obj["Key"] for obj in response.get("Contents", [])]
            print(f"Найдено объектов в бакете '{bucket}': {len(objects)}")
            return objects
        except Exception as e:
            print(f"Ошибка при получении объектов из бакета '{bucket}': {str(e)}")
            return []

    def get_s3_metadata(self, bucket, object_key):
        # Получает метаданные объекта из S3
        try:
            response = self.s3_client.head_object(Bucket=bucket, Key=object_key)
            metadata = {
                key: base64.b64decode(value).decode("utf-8")
                for key, value in response["Metadata"].items()
            }
            print(f"Метаданные для объекта '{object_key}' в бакете '{bucket}': {metadata}")
            return metadata
        except Exception as e:
            print(f"Ошибка при получении метаданных для объекта '{object_key}': {str(e)}")
            return {}

    def update_s3_metadata(self, bucket, object_key, new_metadata):
        try:
            old_metadata = self.get_s3_metadata(bucket, object_key)
            combined_metadata = {**old_metadata, **new_metadata}
            encoded_metadata = {
                key: base64.b64encode(value.encode("utf-8")).decode("ascii")
                for key, value in combined_metadata.items()
            }
            self.s3_client.copy_object(
                Bucket=bucket,
                CopySource={"Bucket": bucket, "Key": object_key},
                Key=object_key,
                Metadata=encoded_metadata,
                MetadataDirective="REPLACE",
            )
        except Exception as e:
            print(f"Ошибка при обновлении данных для объекта '{object_key}': {str(e)}")

    def send_telegram_message(self, chat_id, text, reply_to_message_id=None):
        url = f"{self.telegram_api_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        if reply_to_message_id:
            payload["reply_parameters"] = {"message_id": reply_to_message_id}
        try:
            response = requests.post(url=url, json=payload)
            if response.status_code == 200:
                print(f"Сообщение успешно отправлено в чат '{chat_id}': {text}")
            else:
                print(f"Ошибка отправки сообщения в чат '{chat_id}': {response.text}")
        except Exception as e:
            print(f"Ошибка при отправке сообщения в Telegram: {str(e)}")

    def send_telegram_photo(self, chat_id, photo_url, reply_to_message_id=None):
        url = f"{self.telegram_api_url}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": photo_url,
        }
        if reply_to_message_id:
            payload["reply_parameters"] = {"message_id": reply_to_message_id}
        try:
            response = requests.post(url=url, json=payload)
            if response.status_code == 200:
                file_unique_id = response.json()["result"]["photo"][-1]["file_unique_id"]
                print(f"Фото успешно отправлено в чат '{chat_id}'. File Unique ID: {file_unique_id}")
                return file_unique_id
            else:
                print(f"Ошибка отправки фото в чат '{chat_id}': {response.text}")
                return None
        except Exception as e:
            print(f"Ошибка при отправке фото в Telegram: {str(e)}")
            return None

def find_unnamed_face(app_handler):
    bucket = os.getenv("FACES_BUCKET")
    images = app_handler.fetch_s3_objects(bucket)
    for image in images:
        metadata = app_handler.get_s3_metadata(bucket, image)
        if not metadata.get("Name"):
            print(f"Найдено фото без имени: {image}")
            return image
    print("Все фото имеют имена.")
    return None

def locate_face_by_unique_id(app_handler, file_unique_id):
    bucket = os.getenv("FACES_BUCKET")
    images = app_handler.fetch_s3_objects(bucket)
    print(f"Поиск фото с File Unique ID '{file_unique_id}' в бакете '{bucket}'...")
    for image in images:
        metadata = app_handler.get_s3_metadata(bucket, image)
        if metadata.get("Tg-File-Unique-Id") == file_unique_id:
            print(f"Фото найдено: {image}")
            return image
    return None

def collect_originals_by_name(app_handler, name):
    bucket = os.getenv("FACES_BUCKET")
    originals = []
    images = app_handler.fetch_s3_objects(bucket)
    print(f"Поиск фото с именем '{name}' в бакете '{bucket}'...")
    for image in images:
        metadata = app_handler.get_s3_metadata(bucket, image)
        if metadata.get("Name") == name:
            originals.append(metadata["Original-Photo"])
    if not originals:
        print(f"Фотографии с именем '{name}' не найдены.")
    return originals

def process_incoming_message(app_handler, message):
    text = message.get("text")
    chat_id = message["chat"]["id"]
    reply_to_message_id = message.get("message_id")

    if text == "/start":
        app_handler.send_telegram_message(
            chat_id,
            "Привет! Отправь команду /getface для получения лица",
            reply_to_message_id
        )

    elif text == "/getface":
        face_key = find_unnamed_face(app_handler)
        if not face_key:
            app_handler.send_telegram_message(
                chat_id,
                "Все лица уже имеют имена.",
                reply_to_message_id
            )
            return
        unique_id = app_handler.send_telegram_photo(
            chat_id,
            f"{os.getenv('API_GATEWAY_URL')}?face={face_key}",
            reply_to_message_id
        )
        if unique_id:
            app_handler.update_s3_metadata(os.getenv("FACES_BUCKET"), face_key, {"Tg-File-Unique-Id": unique_id})

    elif text and "reply_to_message" in message and "photo" in message["reply_to_message"]:
        photo_info = message["reply_to_message"]["photo"][-1]
        unique_id = photo_info["file_unique_id"]
        face_key = locate_face_by_unique_id(app_handler, unique_id)
        if face_key:
            app_handler.update_s3_metadata(os.getenv("FACES_BUCKET"), face_key, {"Name": text})
            app_handler.send_telegram_message(
                chat_id,
                f"Лицо успешно названо: {text}",
                reply_to_message_id
            )

    elif text.startswith("/find"):
        name = text[len("/find"):].strip()
        originals = collect_originals_by_name(app_handler, name)
        if not originals:
            app_handler.send_telegram_message(
                chat_id,
                f"Фотографии с {name} не найдены.",
                reply_to_message_id
            )
            return
        media_urls = [f"{os.getenv('API_GATEWAY_URL')}/originals/{item}" for item in originals]
        app_handler.send_telegram_media_group(chat_id, media_urls, reply_to_message_id)

    else:
        app_handler.send_telegram_message(
            chat_id,
            "Неизвестная команда. Попробуйте /start или /getface.",
            reply_to_message_id
        )

def handler(event, context):
    if event.get("httpMethod") != "POST":
        return {"statusCode": 400, "body": "Bad Request: Only POST method is allowed"}
    try:
        update = json.loads(event.get("body", "{}"))
        message = update.get("message")
        if message:
            app_handler = AppHandler()
            process_incoming_message(app_handler, message)
        return {"statusCode": 200, "body": "OK"}
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": "Bad Request: Invalid JSON"}
    except Exception as e:
        return {"statusCode": 500, "body": f"Internal Server Error: {str(e)}"}