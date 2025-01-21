import os
import json
import requests
from telegram import Update, Bot
from telegram.ext import CallbackContext

# Инициализация Telegram Bot
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{bot_token}"

# Функция для отправки сообщения
def send_message(chat_id, text):
    """Отправка сообщения в Telegram чат"""
    response = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={"chat_id": chat_id, "text": text})
    return response.status_code == 200

# Обработка обновлений
def process_update(update):
    """Обрабатывает обновления из Telegram"""
    message = update.get("message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text == "/start":
        send_message(chat_id, "Привет! Отправь команду /getface")
    elif text == "/getface":
        face = get_random_face_without_name()
        if face:
            face_url = f"https://{os.getenv('API_GATEWAY_ID')}.apigw.yandexcloud.net/?face={face['key']}"
            send_message(chat_id, face_url)
        else:
            send_message(chat_id, "Нет доступных лиц без имени.")
    elif text.startswith("/find "):
        name_to_find = text[6:].strip()
        faces = find_faces_by_name(name_to_find)
        if faces:
            for face in faces:
                face_url = f"https://{os.getenv('API_GATEWAY_ID')}.apigw.yandexcloud.net/?face={face['key']}"
                send_message(chat_id, face_url)
        else:
            send_message(chat_id, f"Лица с именем '{name_to_find}' не найдены.")
    else:
        send_message(chat_id, "Неизвестная команда. Попробуйте /start или /getface.")

# Функции для работы с базой данных
def get_random_face_without_name():
    """Возвращает случайное лицо без имени из базы данных"""
    return {"key": "random_face_key.jpg"}

def find_faces_by_name(name):
    """Ищет лица по имени в базе данных"""
    return [{"key": "face_1.jpg"}, {"key": "face_2.jpg"}]

# Главный обработчик событий
def handler(event, context):
    """Основной обработчик Lambda"""
    if event.get("httpMethod") != "POST":
        return {"statusCode": 400, "body": "Bad Request: Only POST method is allowed"}

    try:
        update = json.loads(event.get("body", "{}"))
        process_update(update)
        return {"statusCode": 200, "body": "OK"}
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": "Bad Request: Invalid JSON"}
    except Exception as e:
        return {"statusCode": 500, "body": f"Internal Server Error: {str(e)}"}
