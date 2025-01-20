import os
import json
import requests
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackContext

# Инициализация Telegram Bot
bot_token = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_API_URL = f"https://api.telegram.org/bot{bot_token}"

# Функция для отправки сообщения
def send_message(chat_id, text):
    """Отправка сообщения в Telegram чат"""
    response = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={"chat_id": chat_id, "text": text})
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")
    else:
        print(f"Message sent to {chat_id}")

# Команда /start
def start(update, context):
    """Команда /start, приветствие"""
    send_message(update.message.chat.id, "Привет! Отправь команду /getface")

# Команда /getface
def get_face(update, context):
    """Команда /getface, отправка случайного лица"""
    face = get_random_face_without_name()
    if face:
        face_url = f"https://{os.environ['API_GATEWAY_ID']}.apigw.yandexcloud.net/?face={face['key']}"
        context.user_data["last_sent_face_key"] = face['key']
        send_message(update.message.chat.id, face_url)
    else:
        send_message(update.message.chat.id, "No unnamed faces found.")

# Сохранение имени для лица
def save_face_name(update, context):
    """Сохранение имени для лица"""
    face_name = update.message.text
    last_sent_face_key = context.user_data.get("last_sent_face_key")
    if last_sent_face_key:
        save_face_name_in_db(last_sent_face_key, face_name)
        send_message(update.message.chat.id, "Face name saved.")
    else:
        send_message(update.message.chat.id, "No face to name.")

# Поиск лиц по имени
def find_face(update, context):
    """Поиск лиц по имени"""
    if not context.args:
        send_message(update.message.chat.id, "Usage: /find {name}")
        return

    name_to_find = context.args[0]
    faces = find_faces_by_name(name_to_find)
    if faces:
        for face in faces:
            face_url = f"https://{os.environ['API_GATEWAY_ID']}.apigw.yandexcloud.net/?face={face['key']}"
            send_message(update.message.chat.id, face_url)
    else:
        send_message(update.message.chat.id, f"Фотографии с {name_to_find} не найдены")

# Функции для работы с базой данных и хранения лиц
def get_random_face_without_name():
    """Возвращает случайное лицо без имени из базы данных"""
    return {"key": "random_face_key.jpg"}

def save_face_name_in_db(face_key, face_name):
    """Сохраняет имя для лица в базе данных"""
    pass

def find_faces_by_name(name):
    """Поиск лиц по имени в базе данных"""
    return [{"key": "face_1.jpg"}, {"key": "face_2.jpg"}]

# Основная точка входа для Telegram-бота
def handler(event, context):
    """Точка входа для обработки webhook-запроса от Telegram"""
    if not os.environ.get('TELEGRAM_BOT_TOKEN'):
        return {"statusCode": 200, "body": ""}

    try:
        # Парсим JSON из тела запроса
        update = json.loads(event["body"])

        # Создаем объект Update из данных события
        update_obj = Update.de_json(update, None)

        # Обрабатываем команду /start или другие команды
        if update_obj.message:
            # Используем update_obj (полный объект) вместо message
            message = update_obj.message
            if message.text.startswith('/start'):
                start(update_obj, None)  # передаем полный update объект
            elif message.text.startswith('/getface'):
                get_face(update_obj, None)  # передаем полный update объект
            elif message.text.startswith('/find'):
                find_face(update_obj, None)  # передаем полный update объект
            else:
                save_face_name(update_obj, None)  # передаем полный update объект

        return {"statusCode": 200, "body": "OK"}

    except Exception as e:
        return {"statusCode": 500, "body": f"Internal Server Error: {str(e)}"}
