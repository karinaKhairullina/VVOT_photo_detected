resource "yandex_iam_service_account_static_access_key" "sa_static_key" {
  service_account_id = var.sa_account
}

# Назначение роли для сервисного аккаунта
resource "yandex_resourcemanager_folder_iam_member" "adm_function_invoker_iam" {
  folder_id = var.folder_id
  role      = "functions.functionInvoker"
  member    = "serviceAccount:${var.sa_account}"
}


# Создание бакета для фотографий
resource "yandex_storage_bucket" "photos_bucket" {
  bucket               = var.photos_bucket
  acl                  = "private"
  default_storage_class = "standard"
  max_size             = 5368709120
  access_key           = yandex_iam_service_account_static_access_key.sa_static_key.access_key
  secret_key           = yandex_iam_service_account_static_access_key.sa_static_key.secret_key
}

# Загрузка объекта в бакет
resource "yandex_storage_object" "photo_object" {
  bucket = yandex_storage_bucket.photos_bucket.bucket  
  key   = "photo.jpg"  
  source = "/Users/karina/Desktop/VvOT/HW2/terraform/photo.jpg" 
  access_key           = yandex_iam_service_account_static_access_key.sa_static_key.access_key
  secret_key           = yandex_iam_service_account_static_access_key.sa_static_key.secret_key
}

# Создание бакета для лиц
resource "yandex_storage_bucket" "faces_bucket" {
  bucket               = var.faces_bucket
  acl                  = "private"
  default_storage_class = "standard"
  max_size             = 1073741824
  access_key           = yandex_iam_service_account_static_access_key.sa_static_key.access_key
  secret_key           = yandex_iam_service_account_static_access_key.sa_static_key.secret_key
}



# Создание Yandex Database (serverless)
resource "yandex_ydb_database_serverless" "database" {
  name               = "vvot44-ydb-serverless"
  folder_id          = var.folder_id  
  deletion_protection = true
}

# Создание функции для обнаружения лиц
resource "yandex_function" "face_detection" {
  name               = "vvot44-face-detection"
  entrypoint         = "face_detect.py"
  memory             = "512"
  runtime            = "python312"
  service_account_id = var.sa_account
  user_hash          = "face-detection-user" 
  content {
    zip_filename = data.archive_file.bot_source.output_path
  }
  environment = {
    ACCESS_KEY      = var.access_key
    SECRET_KEY      = var.secret_key
    PHOTOS_BUCKET   = yandex_storage_bucket.photos_bucket.bucket
    TASK_QUEUE_URL  = yandex_message_queue.tasks_queue.arn
  }
}

# Триггер для обнаружения лиц
resource "yandex_function_trigger" "photo_trigger" {
  name        = "vvot44-photo"
  description = "Trigger for photo upload in photos bucket"
  
  function {
    id                 = yandex_function.face_detection.id
    service_account_id = var.sa_account
  }

  object_storage {
    bucket_id = yandex_storage_bucket.photos_bucket.id
    suffix    = ".jpg"  
    create    = true
  }
}

# Создание обработчика для нарезки лиц
resource "yandex_function" "face_cut" {
  name               = "vvot44-face-cut"
  entrypoint         = "face_cut.py"
  memory             = "256"
  runtime            = "python312"
  service_account_id = var.sa_account
  user_hash          = "face-cut-user"  
  content {
    zip_filename = data.archive_file.bot_source.output_path
  }
  environment = {
    ACCESS_KEY    = var.access_key
    SECRET_KEY    = var.secret_key
    FACES_BUCKET  = yandex_storage_bucket.faces_bucket.bucket
  }
}

# Триггер для задач
resource "yandex_function_trigger" "task_trigger" {
  name        = "vvot44-task"

  function {
    id                 = yandex_function.face_cut.id
    service_account_id = var.sa_account
    retry_attempts     = 3
    retry_interval     = 30
  }

  message_queue {
    queue_id           = yandex_message_queue.tasks_queue.arn
    service_account_id = var.sa_account
    batch_cutoff       = "0"                          
    batch_size         = "1"  
  }
}

# Создание бота
resource "yandex_function" "bot" {
  name               = "vvot44-bot"
  entrypoint         = "index.handler"
  memory             = "128"
  runtime            = "python312"
  service_account_id = var.sa_account
  user_hash          = "bot-user" 
  environment = {
    TELEGRAM_BOT_TOKEN = var.tg_bot_key
    API_GATEWAY_URL    = "https://${yandex_api_gateway.api_gw.domain}"
    ACCESS_KEY         = var.access_key
    SECRET_KEY         = var.secret_key
    QUEUE_URL          = var.queue_url
    FACES_BUCKET       = var.faces_bucket
    PHOTOS_BUCKET=var.photos_bucket
  }
  content {
    zip_filename = data.archive_file.bot_source.output_path
  }
}

# Настройка API Gateway 
resource "yandex_api_gateway" "api_gw" {
  name = "vvot44-apigw"
  spec = <<EOT
openapi: "3.0.0"
info:
  version: 1.0.0
  title: Faces API
paths:
  /:
    get:
      summary: "Get face"
      parameters:
        - name: "face"
          in: "query"
          required: true
          schema:
            type: "string"
      x-yc-apigateway-integration:
        type: "object-storage"
        bucket: "${yandex_storage_bucket.faces_bucket.bucket}"
        object: "{face}"
        service_account_id: "${var.sa_account}"
      responses:
        '200':
          description: "Image found"
        '404':
          description: "Image not found"
EOT
}

# Очередь сообщений для задач
resource "yandex_message_queue" "tasks_queue" {
  name        = var.queue_name
  access_key  = yandex_iam_service_account_static_access_key.sa_static_key.access_key
  secret_key  = yandex_iam_service_account_static_access_key.sa_static_key.secret_key 
}


resource "telegram_bot_webhook" "tg_bot_webhook" {
  url = "https://functions.yandexcloud.net/${yandex_function.bot.id}"
}

# Ресурс для создания архива с кодом
data "archive_file" "bot_source" {
  type        = "zip"
  source_dir  = "../src/bot"
  output_path = "../build/new_bot.zip"
}
