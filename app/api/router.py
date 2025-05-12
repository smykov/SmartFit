from fastapi import APIRouter

from app.api.endpoints import (whatsapp, telegram, messaging)
# , users, diets, tracking
from app.api.endpoints import health

# Создание основного роутера
api_router = APIRouter(prefix="/api")

api_router.include_router(health.router, tags=["health"])

# Универсальный роутер для мессенджеров
api_router.include_router(
    messaging.router,
    prefix="/messaging",
    tags=["Messaging"]
)
# Подключение эндпоинтов TODO убрать обратную совместимость при запуске
api_router.include_router(
    whatsapp.router,
    prefix="/whatsapp",
    tags=["WhatsApp"]
)
# Маршрут для Telegram  TODO убрать обратную совместимость при запуске
api_router.include_router(
    telegram.router,
    prefix="/telegram",
    tags=["Telegram"]
)

# api_router.include_router(
#     users.router,
#     prefix="/users",
#     tags=["Users"]
# )
#
# api_router.include_router(
#     diets.router,
#     prefix="/diets",
#     tags=["Diets"]
# )
#
# api_router.include_router(
#     tracking.router,
#     prefix="/tracking",
#     tags=["Tracking"]
# )
# api_router.include_router(
#     reminders.router,
#     prefix="/reminders",
#     tags=["Reminders"]
# )
