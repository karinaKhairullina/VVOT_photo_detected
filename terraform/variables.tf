variable "sa_account" {
  description = "ID сервизного аккаунта"
  type        = string
}


variable "cloud_id" {
  description = "ID облака в Yandex Cloud"
  type        = string
}

variable "folder_id" {
  description = "ID папки в Yandex Cloud"
  type        = string
}


variable "photos_bucket" {
  description = "Название бакета для оригинальных фотографий"
  type        = string
}

variable "faces_bucket" {
  description = "Название бакета для фотографий лиц"
  type        = string
}

variable "queue_name" {
  description = "Название очереди сообщений"
  type        = string
}

variable "bot_function" {
  description = "Название функции для Telegram бота"
  type        = string
}

variable "tg_bot_key" {
  description = "Telegram Bot Token"
  type        = string
  sensitive   = true
}

variable "api_gateway" {
  description = "Название API Gateway"
  type        = string
}

variable "registry_name" {
  description = "Название реестра для Docker образов"
  type        = string
}

variable "db_name" {
  description = "Название базы данных для фотографий"
  type        = string
}

variable "db_user" {
  description = "Юзернэйм для бд"
  type        = string
  default = "karina"
}

variable "db_password" {
  description = "Пароль для бд"
  type        = string
}

variable "network_id" {
  description = "ID сети для подключения ресурсов"
  type        = string
}

variable "access_key" {
  description = "Access key "
  type        = string
}

variable "secret_key" {
  description = "Secret key "
  type        = string
}


variable "key_file_path" {
  type        = string
  description = "Ключ сервисного аккаунта"
  default     = "/Users/karina/Desktop/VvOT/HW2/terraform/key.json"
}