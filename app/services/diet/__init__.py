# app/services/diet/__init__.py

from app.services.diet.diet_service import DietService
from app.di.container import container

# Получаем экземпляр сервиса из контейнера DI
diet_service = container.diet_service()

# Экспортируем только один основной сервис для использования в других модулях
__all__ = ['diet_service']