import pytest
import os
import sys
from pathlib import Path
import asyncio
from typing import Dict, Any
from unittest.mock import MagicMock, AsyncMock
import logging

from app.db.firebase import FirebaseClient
from app.services.llm.base_llm_service import BaseLLMService
from app.services.messaging.clients.twilio_whatsapp_client import TwilioWhatsAppClient
from app.services.localization.localization_service import LocalizationService
from app.services.diet.diet_service import DietService
from app.services.tracking.tracking_service import TrackingService
from app.services.onboarding.onboarding_service import OnboardingService

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

# Устанавливаем переменные окружения для тестов
os.environ['TESTING'] = 'True'
os.environ['USE_MOCK_SERVICES'] = 'True'

# Импортируем все фикстуры из других файлов
from fixtures.firebase_fixtures import *
from fixtures.llm_fixtures import *
from fixtures.whatsapp_fixtures import *
from fixtures.user_fixtures import *
from fixtures.diet_fixtures import *
from fixtures.localization_fixtures import *
from fixtures.service_fixtures import *


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Настройка тестового окружения перед запуском всех тестов."""
    # Здесь можно добавить глобальную настройку для всех тестов
    # Например, создание тестовой БД, очистка кэшей и т.д.

    # Устанавливаем кодировку для Python
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

    # Выполняется перед всеми тестами
    yield
    # Выполняется после всех тестов (очистка)
    pass


@pytest.fixture(scope="function", autouse=True)
def reset_mocks(whatsapp_service_mock):
    """Сбрасывает состояние моков перед каждым тестом."""
    # Выполняется перед каждым тестом
    whatsapp_service_mock.clear_messages()

    yield
    # Выполняется после каждого теста
    pass

@pytest.fixture
def test_config():
    """Тестовая конфигурация с необходимыми параметрами."""
    return {
        "TIMEZONE": "America/Guatemala",
        "WHATSAPP_MAX_MESSAGE_SIZE": 1500,
        "TWILIO_PHONE_NUMBER": "+1234567890",
        "DEFAULT_LANGUAGE": "es"
    }


@pytest.fixture
def firebase_mock():
    """Мок для Firebase клиента."""
    mock = MagicMock(spec=FirebaseClient)

    # Настраиваем методы, чтобы они возвращали предопределенные значения, а не корутины
    mock.get_document = AsyncMock()
    mock.add_document = AsyncMock()
    mock.update_document = AsyncMock()
    mock.query_documents = AsyncMock()
    mock.get_all_documents = AsyncMock(return_value=[])

    return mock


@pytest.fixture
def llm_service_mock():
    """Мок для LLM сервиса."""
    mock = AsyncMock(spec=BaseLLMService)

    # Предварительно определенные ответы для разных запросов
    predefined_responses = {
        # Формат: (system_prompt_substring, user_prompt_substring): response
        ("diet plan", "personalized"): '{"meals": [{"type": "breakfast", "title": "Овсянка с фруктами"}]}',
        ("shopping list",
         "generate"): '[{"name": "Овсянка", "quantity": 500, "unit": "г"}, {"name": "Яблоки", "quantity": 3, "unit": "шт."}]',
        ("update diet",
         "change"): '{"updated_days": {"monday": {"meals": [{"type": "breakfast", "title": "Омлет с овощами"}]}}, "comment": "Изменения внесены согласно вашему запросу"}'
    }

    async def generate_completion_mock(system_prompt, user_prompt, **kwargs):
        # Ищем подходящий ответ на основе фрагментов промптов
        for (sys_key, user_key), response in predefined_responses.items():
            if sys_key in system_prompt and user_key in user_prompt:
                return response
        return '{"error": "No predefined response found"}'

    mock.generate_completion = AsyncMock(side_effect=generate_completion_mock)

    # Дополнительные методы, имитирующие конкретные функции
    mock.generate_diet_plan = AsyncMock(return_value={"daily_plans": {
        "monday": {"meals": [{"type": "breakfast", "title": "Омлет"}]},
        "tuesday": {"meals": [{"type": "breakfast", "title": "Каша"}]}
    }})

    mock.update_diet_plan = AsyncMock(return_value={
        "success": True,
        "updated_days": {"monday": {"meals": [{"type": "breakfast", "title": "Омлет с овощами"}]}}
    })

    mock.create_shopping_list = AsyncMock(return_value=[
        {"name": "Яйца", "quantity": 6, "unit": "шт."},
        {"name": "Помидоры", "quantity": 2, "unit": "шт."}
    ])

    return mock


@pytest.fixture
def message_client_mock():
    """Мок для клиента отправки сообщений WhatsApp."""
    mock = AsyncMock(spec=TwilioWhatsAppClient)

    # Имитируем успешную отправку сообщений
    mock.send_message.return_value = "message-id-123"
    mock.send_template_message.return_value = "template-message-id-123"

    return mock


@pytest.fixture
def localization_service_mock():
    """Мок для сервиса локализации."""
    mock = MagicMock(spec=LocalizationService)

    # Словарь с переводами для тестов
    translations = {
        "diet.full.created": {
            "es": "¡Tu plan de alimentación está listo!",
            "ru": "Твой план питания готов!",
            "en": "Your diet plan is ready!"
        },
        "onboarding.welcome": {
            "es": "¡Bienvenido a GuateFit!",
            "ru": "Добро пожаловать в GuateFit!",
            "en": "Welcome to GuateFit!"
        }
        # Можно добавить больше переводов по мере необходимости
    }

    def get_message_mock(key, lang=None, **params):
        lang = lang or "en"
        if key in translations and lang in translations[key]:
            message = translations[key][lang]
            # Подставляем параметры, если они есть
            for param_key, param_value in params.items():
                message = message.replace(f"{{{param_key}}}", str(param_value))
            return message
        return key

    mock.get_message = MagicMock(side_effect=get_message_mock)
    mock.get_user_language = AsyncMock(return_value="es")

    return mock


@pytest.fixture
def test_user_data():
    """Тестовые данные пользователя."""
    return {
        "id": "test-user-id",
        "phone_number": "+5012345678",
        "name": "Test User",
        "gender": "male",
        "age": 35,
        "height": 175,
        "current_weight": 85,
        "target_weight": 75,
        "activity_level": "moderate",
        "weight_goal": "lose",
        "diet_preference": "regular",
        "allergies": [],
        "disliked_products": ["mushrooms"],
        "budget_limit": 500,
        "language": "es",
        "is_onboarding_completed": True
    }


@pytest.fixture
def test_diet_plan_data():
    """Тестовые данные плана диеты."""
    return {
        "id": "test-diet-plan-id",
        "user_id": "test-user-id",
        "version": "short",
        "status": "pending",
        "daily_plans": {
            "monday": {
                "meals": [
                    {
                        "type": "breakfast",
                        "title": "Овсянка с фруктами",
                        "calories": 350,
                        "products": [
                            {"name": "Овсянка", "quantity": 50, "unit": "г"},
                            {"name": "Банан", "quantity": 1, "unit": "шт."}
                        ]
                    },
                    {
                        "type": "lunch",
                        "title": "Куриный салат",
                        "calories": 450,
                        "products": [
                            {"name": "Куриная грудка", "quantity": 150, "unit": "г"},
                            {"name": "Салат", "quantity": 100, "unit": "г"}
                        ]
                    }
                ],
                "total_calories": 800
            },
            "tuesday": {
                "meals": [
                    {
                        "type": "breakfast",
                        "title": "Яичница с тостами",
                        "calories": 400,
                        "products": [
                            {"name": "Яйца", "quantity": 2, "unit": "шт."},
                            {"name": "Хлеб", "quantity": 2, "unit": "ломтика"}
                        ]
                    }
                ],
                "total_calories": 400
            }
        },
        "created_at": "2023-01-01T12:00:00Z"
    }


@pytest.fixture(scope="session", autouse=True)
def initialize_localization():
    """
    Инициализирует систему локализации для тестов.
    Эта фикстура выполняется автоматически перед всеми тестами.
    """
    logger.info("Инициализация системы локализации для тестов")

    try:
        # Импортируем реестр локализации
        from app.localization.registry import registry

        # Проверяем, инициализированы ли языки
        if not hasattr(registry, 'languages') or not registry.languages:
            logger.info("Загрузка языков в реестр локализации")
            registry.load_languages()

        # Проверяем загруженные языки
        loaded_languages = list(registry.languages.keys())
        logger.info(f"Загружены языки: {loaded_languages}")

        # Проверяем наличие русского языка (основной для тестов)
        if 'ru' not in loaded_languages:
            logger.warning("Русский язык не загружен в реестр локализации!")

        # Тестируем базовую строку локализации
        test_key = "tracking.weight.recorded"
        test_message = registry.get(test_key, "ru", weight=80)
        logger.info(f"Тестовая локализация '{test_key}': {test_message}")

        return registry
    except ImportError as e:
        logger.error(f"Ошибка импорта модулей локализации: {e}")
        raise
    except Exception as e:
        logger.error(f"Ошибка инициализации локализации: {e}")
        raise


@pytest.fixture
def localization_registry():
    """
    Возвращает инициализированный реестр локализации для использования в тестах.
    """
    from app.localization.registry import registry
    return registry


@pytest.fixture
def check_localization_key():
    """
    Создает функцию для проверки наличия ключей локализации

    Returns:
        Callable: Функция для проверки ключей локализации
    """
    from app.localization.registry import registry

    def _check_key(key: str, lang: str = "ru") -> bool:
        """
        Проверяет наличие ключа локализации и выводит информацию о нем

        Args:
            key: Ключ локализации для проверки
            lang: Код языка (ru, en, es)

        Returns:
            bool: True, если ключ существует и может быть локализован
        """
        message = registry.get(key, lang)
        exists = message != key  # Если вернулся тот же ключ, значит локализация не найдена

        if exists:
            logger.info(f"Ключ локализации '{key}' найден: {message}")
        else:
            logger.warning(f"Ключ локализации '{key}' не найден")

        return exists

    return _check_key


@pytest.fixture
def test_localization():
    """
    Создает функцию для тестирования локализации с параметрами

    Returns:
        Callable: Функция для тестирования локализации
    """
    from app.localization.registry import registry

    def _test_localization(key: str, params: Dict[str, Any], lang: str = "ru") -> str:
        """
        Тестирует локализацию с заданными параметрами

        Args:
            key: Ключ локализации
            params: Параметры для подстановки
            lang: Код языка

        Returns:
            str: Локализованная строка с подстановкой параметров
        """
        message = registry.get(key, lang, **params)
        logger.info(f"Локализация '{key}' с параметрами {params}: {message}")
        return message

    return _test_localization