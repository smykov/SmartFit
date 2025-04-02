import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.api.router import api_router
from app.services import whatsapp_service
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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )


# код для запуска инициализации при старте приложения
@app.on_event("startup")
async def startup_event():
    # Запускаем процесс отправки неотправленных сообщений при старте
    await whatsapp_service.initialize()
    logger.info("WhatsApp service initialized")
