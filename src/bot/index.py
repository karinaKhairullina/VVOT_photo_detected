import os
import json
import requests

# Инициализация Telegram Bot
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
api_gateway_url = os.getenv('API_GATEWAY_URL')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{bot_token}"


# Функция для отправки сообщения
def send_message(chat_id, text):
    """Отправка сообщения в Telegram чат"""
    response = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={"chat_id": chat_id, "text": text})
    return response.status_code == 200


# Получение случайного лица из бакета
def get_random_face_from_s3():
    """Возвращает случайное лицо через API Gateway"""
    try:
        print(f"Запрос к API Gateway: {api_gateway_url}/?random=true")  # Логируем URL запроса
        response = requests.get(f"{api_gateway_url}/?random=true")

        # Логируем статус ответа и тело ответа
        print(f"Ответ от API Gateway - Статус: {response.status_code}, Тело: {response.text}")

        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and "key" in data:
                    print(f"Получено случайное лицо: {data['key']}")  # Логируем ключ
                    return data
                else:
                    print(f"API Gateway вернул некорректный JSON: {data}")
            except json.JSONDecodeError as e:
                print(f"Ошибка декодирования JSON: {e}")
        else:
            print(f"API Gateway вернул ошибку: {response.status_code}")
    except Exception as e:
        print(f"Ошибка при запросе случайного лица: {e}")

    return None


# Функция для поиска лиц по имени в базе данных
def find_faces_by_name(name):
    """Ищет лица по имени в базе данных"""
    # Пример, как искать лица в базе данных
    return [{"key": f"{name}_face_1.jpg"}, {"key": f"{name}_face_2.jpg"}]


# Обработка обновлений
def process_update(update):
    """Обрабатывает обновления из Telegram"""
    message = update.get("message")
    if not message:
        return
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    print(f"Received message: {text} from chat_id: {chat_id}")  # Логируем входящее сообщение
    if text == "/start":
        send_message(chat_id, "Привет! Отправь команду /getface для получения случайного лица.")
    elif text == "/getface":
        face = get_random_face_from_s3()
        if face:
            # Формируем ссылку на обрезанное лицо через API Gateway
            face_url = f"{api_gateway_url}/face/{face['key']}"
            send_message(chat_id, f"Вот фотография лица: {face_url}")
        else:
            send_message(chat_id, "Нет доступных лиц.")
    elif text.startswith("/find "):
        name_to_find = text[6:].strip()
        print(f"Looking for faces with name: {name_to_find}")  # Логируем запрос на поиск лиц
        faces = find_faces_by_name(name_to_find)
        if faces:
            for face in faces:
                face_url = f"{api_gateway_url}/face/{face['key']}"
                send_message(chat_id, face_url)
        else:
            send_message(chat_id, f"Лица с именем '{name_to_find}' не найдены.")
    else:
        send_message(chat_id, "Неизвестная команда. Попробуйте /start или /getface.")


# Главный обработчик событий
def handler(event, context):
    """Основной обработчик Lambda"""
    print(f"Event: {json.dumps(event)}")  # Логируем полученное событие
    if event.get("httpMethod") != "POST":
        return {"statusCode": 400, "body": "Bad Request: Only POST method is allowed"}
    try:
        update = json.loads(event.get("body", "{}"))
        print(f"Update: {json.dumps(update)}")  # Логируем тело запроса
        process_update(update)
        return {"statusCode": 200, "body": "OK"}
    except json.JSONDecodeError:
        print("Error: Invalid JSON")
        return {"statusCode": 400, "body": "Bad Request: Invalid JSON"}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": f"Internal Server Error: {str(e)}"}