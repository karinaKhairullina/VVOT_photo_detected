import cv2
import numpy as np
import os
import boto3
import json

def detect_faces(image_data):
    face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    image_array = np.frombuffer(image_data, dtype=np.uint8)
    decoded_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    grayscale_image = cv2.cvtColor(decoded_image, cv2.COLOR_BGR2GRAY)
    detected_faces = face_detector.detectMultiScale(grayscale_image, scaleFactor=1.1, minNeighbors=5)
    return [list(face) for face in detected_faces]

def process_event(event, context):

    queue = QueueAdapter()
    storage = StorageManager()

    event_details = event["messages"][0]["details"]
    bucket_name = event_details["bucket_id"]
    object_key = event_details["object_id"]

    image_data = storage.retrieve_object(bucket_name, object_key)

    faces = detect_faces(image_data)

    for face_coords in faces:
        queue.enqueue_message({
            "source_key": object_key,
            "face_coordinates": face_coords,
        })

    return {
        "statusCode": 200,
        "body": None,
    }

class StorageManager:
    def __init__(self):
        self.client = boto3.client(
            service_name="s3",
            aws_access_key_id=os.getenv("ACCESS_KEY"),
            aws_secret_access_key=os.getenv("SECRET_KEY"),
            region_name="ru-central1",
            endpoint_url="https://storage.yandexcloud.net",
        )

    def retrieve_object(self, bucket, object_key) -> bytes:
        response = self.client.get_object(Bucket=bucket, Key=object_key)
        return response["Body"].read()

class QueueAdapter:
    def __init__(self):
        self.client = boto3.client(
            service_name="sqs",
            endpoint_url="https://message-queue.api.cloud.yandex.net",
            region_name="ru-central1",
            aws_access_key_id=os.getenv("ACCESS_KEY"),
            aws_secret_access_key=os.getenv("SECRET_KEY"),
        )

    def enqueue_message(self, message):
        self.client.send_message(
            QueueUrl=os.getenv("QUEUE_URL"),
            MessageBody=json.dumps(message)
        )