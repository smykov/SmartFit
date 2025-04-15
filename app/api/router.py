from fastapi import APIRouter

from app.api.endpoints import (whatsapp)
# , users, diets, tracking
from app.di.container import container

# Создание основного роутера
api_router = APIRouter(prefix="/api")

# Подключение эндпоинтов
api_router.include_router(
    whatsapp.router,
    prefix="/whatsapp",
    tags=["WhatsApp"]
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
