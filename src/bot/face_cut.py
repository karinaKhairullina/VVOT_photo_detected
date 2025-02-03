import io
import json
import os
from uuid import uuid4
from PIL import Image
import boto3
import base64

def extract_face(image_data, face_coords) -> bytes:
    image = Image.open(io.BytesIO(image_data))
    x, y, width, height = face_coords
    cropped_face = image.crop((x, y, x + width, y + height))
    output_buffer = io.BytesIO()
    cropped_face.save(output_buffer, format="JPEG")
    return output_buffer.getvalue()

def process_event(event, context):
    storage = StorageAdapter()
    message_body = json.loads(event["messages"][0]["details"]["message"]["body"])
    original_key = message_body["object_key"]
    face_coords = message_body["face"]

    image_data = storage.retrieve_object(os.getenv("PHOTOS_BUCKET"), original_key)

    face_image = extract_face(image_data, face_coords)

    new_key = f"{uuid4().hex}.jpg"

    metadata = {"Source-Image": original_key}
    storage.store_object(os.getenv("FACES_BUCKET"), new_key, face_image, "image/jpeg", metadata)

    return {
        "statusCode": 200,
        "body": None,
    }

class StorageAdapter:
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

    def store_object(self, bucket, object_key, body, content_type="binary/octet-stream", metadata=None):
        if metadata:
            encoded_metadata = {
                key: base64.b64encode(value.encode("utf-8")).decode("ascii")
                for key, value in metadata.items()
            }
        else:
            encoded_metadata = {}

        self.client.put_object(
            Bucket=bucket,
            Key=object_key,
            Body=body,
            ContentType=content_type,
            Metadata=encoded_metadata
        )