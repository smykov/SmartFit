import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, Optional

from app.services.localization.localization_interface import ILocalizationService


@pytest.fixture
def localization_translations():
    """Возвращает набор переводов для тестов."""
    return {
        "diet.full.created": {
            "es": "¡Tu plan de alimentación está listo!",
            "ru": "Твой план питания готов!",
            "en": "Your diet plan is ready!"
        },
        "diet.full.summary.header": {
            "es": "*📋 PLAN DE ALIMENTACIÓN PERSONALIZADO*\n\n",
            "ru": "*📋 ПЕРСОНАЛЬНЫЙ ПЛАН ПИТАНИЯ*\n\n",
            "en": "*📋 PERSONALIZED DIET PLAN*\n\n"
        },
        "diet.day.header": {
            "es": "🗓️ MENÚ PARA {day_name}, {date_formatted}:\n\n",
            "ru": "🗓️ МЕНЮ НА {day_name}, {date_formatted}:\n\n",
            "en": "🗓️ MENU FOR {day_name}, {date_formatted}:\n\n"
        },
        "tracking.weight.recorded": {
            "es": "✅ ¡Excelente! Registré tu peso: {weight} kg.",
            "ru": "✅ Отлично! Я записал твой вес: {weight} кг.",
            "en": "✅ Great! I recorded your weight: {weight} kg."
        },
        "tracking.water.recorded": {
            "es": "💧 ¡Excelente! Registré tu consumo de agua: {amount} vasos (~{ml_amount} ml).",
            "ru": "💧 Отлично! Я записал твое потребление воды: {amount} стаканов (~{ml_amount} мл).",
            "en": "💧 Great! I recorded your water intake: {amount} cups (~{ml_amount} ml)."
        },
        "shopping.header": {
            "es": "*🛒 LISTA DE COMPRAS*\n\n",
            "ru": "*🛒 СПИСОК ПОКУПОК*\n\n",
            "en": "*🛒 SHOPPING LIST*\n\n"
        },
        "onboarding.welcome": {
            "es": "👋 ¡Hola! Bienvenido a GuateFit - tu asistente personal para adelgazar.",
            "ru": "👋 Привет! Добро пожаловать в SmartFit - твой персональный ассистент для похудения.",
            "en": "👋 Hello! Welcome to SmartFit - your personal weight loss assistant."
        },
        "common.weekday_names.monday": {
            "es": "Lunes",
            "ru": "Понедельник",
            "en": "Monday"
        },
        "common.weekday_names.tuesday": {
            "es": "Martes",
            "ru": "Вторник",
            "en": "Tuesday"
        },
        "common.meal_types.breakfast": {
            "es": "Desayuno",
            "ru": "Завтрак",
            "en": "Breakfast"
        },
        "common.meal_types.lunch": {
            "es": "Almuerzo",
            "ru": "Обед",
            "en": "Lunch"
        },
        "commands.help.helpText": {
            "es": "Aquí está la lista de comandos disponibles:...",
            "ru": "Вот список доступных команд:...",
            "en": "Here is a list of available commands:..."
        }
    }


@pytest.fixture
def localization_service_mock(localization_translations):
    """Возвращает мок для сервиса локализации."""
    mock = MagicMock(spec=ILocalizationService)
    translations = localization_translations

    # Метод для получения локализованного сообщения
    def get_message(key, lang=None, **params):
        lang = lang or "en"
        if key in translations and lang in translations[key]:
            message = translations[key][lang]
            # Подставляем параметры, если они есть
            for param_key, param_value in params.items():
                placeholder = "{" + param_key + "}"
                if placeholder in message:
                    message = message.replace(placeholder, str(param_value))
            return message
        return key

    # Метод для получения языка пользователя
    async def get_user_language(user_id):
        # Для тестов возвращаем фиксированный язык, если не указан иной
        return "ru"

    # Метод для установки языка пользователя
    async def set_user_language(user_id, lang):
        return True

    # Привязываем методы к моку
    mock.get_message = MagicMock(side_effect=get_message)
    mock.get_user_language = AsyncMock(side_effect=get_user_language)
    mock.set_user_language = AsyncMock(side_effect=set_user_language)

    return mock