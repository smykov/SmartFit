# Инициализация всех сервисов

# Импортируем LLM сервисы
from app.services.llm import llm_service, LLMFactory

# Другие сервисы
from app.services.diet import diet_service
from app.services.tracking.tracking_service import tracking_service
from app.services.whatsapp_service import whatsapp_service

# Экспортируем сервисы для удобства импорта
__all__ = [
    'llm_service',
    'LLMFactory',
    'diet_service',
    'tracking_service',
    'whatsapp_service'
]