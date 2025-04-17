import os
import json
from typing import Dict
from pydantic import BaseSettings
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

class Settings(BaseSettings):
    # Основные настройки приложения
    APP_NAME: str = "GuateFit"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # PostgreSQL настройки
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER = os.getenv("POSTGRES_USER", "guatefit")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "guatefit_password")
    POSTGRES_DATABASE = os.getenv("POSTGRES_DB", "guatefit")
    POSTGRES_MIN_CONN = int(os.getenv("POSTGRES_MIN_CONN", "5"))
    POSTGRES_MAX_CONN = int(os.getenv("POSTGRES_MAX_CONN", "20"))

    # Выбор движка БД по умолчанию: firebase или postgres
    DB_ENGINE = os.getenv("DB_ENGINE", "firebase")

    # Настройки Firebase
    FIREBASE_CREDENTIALS: str = os.getenv("FIREBASE_CREDENTIALS", "")
    FIREBASE_DATABASE_URL: str = os.getenv("FIREBASE_DATABASE_URL", "")

    # Настройки OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # Настройки WhatsApp (через Twilio)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    # Настройки WhatsApp
    WHATSAPP_WEBHOOK_URL: str = os.getenv("WHATSAPP_WEBHOOK_URL", "")
    WHATSAPP_RETRY_INTERVAL_SECONDS: int = 300  # 5 минут
    WHATSAPP_MAX_MESSAGE_SIZE: int = 1500
    WHATSAPP_MAX_MESSAGE_AGE_HOURS: int = 72  # 3 дня

    # Временная зона для Гватемалы
    TIMEZONE: str = "America/Guatemala"

    # Настройки для тестирования и разработки
    USE_MOCK_SERVICES: bool = os.getenv("USE_MOCK_SERVICES", "False").lower() == "true"

    # LLM настройки
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "deepseek")  # openai, deepseek или hybrid

    # Маппинг задач для гибридного режима, в формате JSON
    # {"diet_plan": "openai", "nutrition_question": "deepseek", "shopping_list": "deepseek"}
    _LLM_TASK_MAPPING: str = os.getenv("LLM_TASK_MAPPING",
                                       '{"diet_plan": "deepseek", "nutrition_question": "deepseek", "shopping_list": "deepseek"}')

    @property
    def LLM_TASK_MAPPING(self) -> Dict[str, str]:
        try:
            return json.loads(self._LLM_TASK_MAPPING)
        except json.JSONDecodeError:
            return {}

    # DeepSeek
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_API_BASE: str = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")

    class Config:
        env_file = ".env"


# Создаем экземпляр настроек
settings = Settings()