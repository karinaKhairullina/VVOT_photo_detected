import json
import requests

def handler(event, context):
    telegram_api_url = f"https://api.telegram.org/bot{event['environment']['TELEGRAM_BOT_TOKEN']}/sendPhoto"
    data = json.loads(event["body"])
    command = data.get("message", {}).get("text", "")

    if command == "/getface":
        face_image = get_face_image()
        send_telegram_photo(telegram_api_url, face_image)
    elif command.startswith("/find "):
        name = command.split(" ")[1]
        found_images = find_images_by_name(name)
        send_telegram_message(telegram_api_url, found_images)
    else:
        send_telegram_message(telegram_api_url, "Ошибка")

def send_telegram_photo(api_url, image_url):
    data = {
        "chat_id": data["message"]["chat"]["id"],
        "photo": image_url
    }
    requests.post(api_url, data=data)

def send_telegram_message(api_url, message):
    data = {
        "chat_id": data["message"]["chat"]["id"],
        "text": message
    }
    requests.post(api_url, data=data)
