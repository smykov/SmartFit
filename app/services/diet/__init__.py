# app/services/diet/__init__.py

from app.services.diet.diet_service import DietService

# Создаем экземпляр сервиса для диет
diet_service = DietService()

# Экспортируем только один основной сервис для использования в других модулях
__all__ = ['diet_service']