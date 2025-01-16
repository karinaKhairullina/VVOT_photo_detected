terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
      version = "0.80.0"
    }
    telegram = {
      source  = "yi-jiayu/telegram"
      version = "0.3.1"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  cloud_id                = var.cloud_id
  folder_id               = var.folder_id
  service_account_key_file = pathexpand(var.key_file_path)  
  zone                     = "ru-central1-a"
}



provider "telegram" {
  bot_token = var.tg_bot_key
}