import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.db.postgres import PostgresClient

from app.api.router import api_router
from app.di.container import container
from config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
# Отключение логов Twilio - установка уровня ERROR или CRITICAL
logging.getLogger('twilio').setLevel(logging.ERROR)
logging.getLogger('twilio.http_client').setLevel(logging.ERROR)
# Создание FastAPI приложения
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-ассистент для похудения, учитывающий местные продукты и культурные особенности Гватемалы",
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене нужно указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация контейнера DI
container.config.from_dict({
    "app_name": settings.APP_NAME,
    "app_version": settings.APP_VERSION,
})

# Регистрация контейнера в FastAPI приложении для внедрения зависимостей через ручки API
app.container = container

# Подключение API роутеров
app.include_router(api_router)


# Обработка исключений
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Глобальная ошибка: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Произошла внутренняя ошибка сервера"},
    )


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Код для запуска инициализации при старте приложения
@app.on_event("startup")
async def startup_event():
    """Действия при запуске приложения"""

    # Проверяем, используется ли PostgreSQL
    if os.getenv("DB_ENGINE", settings.DB_ENGINE) == "postgres":
        # Инициализируем PostgreSQL клиент
        postgres_client = container.postgres_client()
        await postgres_client.initialize()

    # Проверка необходимых переменных окружения
    # required_env_vars = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"]
    # missing_vars = [var for var in required_env_vars if not getattr(settings, var, None)]
    #
    # if missing_vars:
    #     logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    #     raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Проверка всех зависимостей в контейнере
    try:
        # Пробуем получить все основные зависимости
        container.user_repository()
        container.message_repository()
        container.whatsapp_client()
        container.telegram_client()
        container.whatsapp_messenger()
        container.telegram_messenger()
        container.localization_service()
        container.diet_service()
        container.tracking_service()
        container.message_processor_service()
        container.text_splitter()
        container.command_factory()
        container.command_handler_service()
        container.onboarding_service()

        logger.info("All dependencies successfully resolved")
    except Exception as e:
        logger.error(f"Error resolving dependencies: {str(e)}")
        raise

    try:
        # Получаем необходимые зависимости
        messenger_registry = container.messenger_registry()
        whatsapp_messenger = container.whatsapp_messenger()
        telegram_messenger = container.telegram_messenger()

        # Регистрируем мессенджеры в реестре (если это не сделано в DI-контейнере)
        messenger_registry.register_messenger(whatsapp_messenger)
        messenger_registry.register_messenger(telegram_messenger)
        logger.info("Messengers registered successfully")

        # Инициализируем единый сервис мессенджеров вместо отдельных сервисов
        messenger_service = container.messenger_service()
        await messenger_service.initialize()
        logger.info("Messenger service initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing messaging services: {str(e)}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Действия при остановке приложения"""
    # Проверяем, используется ли PostgreSQL
    if os.getenv("DB_ENGINE", settings.DB_ENGINE) == "postgres":
        # Закрываем соединения с PostgreSQL
        postgres_client = container.postgres_client()
        if postgres_client:
            await postgres_client.close()


app.add_event_handler("startup", startup_event)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
