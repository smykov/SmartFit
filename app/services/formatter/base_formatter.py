# app/services/formatter/base_formatter.py
import logging
from typing import Dict, Any, Optional

from app.constants.localization_keys import LocalizationKeys as LK
from app.services.localization.localization_interface import ILocalizationService
from app.utils.date_helper import DateHelper
from app.utils.format_helper import FormatHelper


class BaseFormatter:
    """Базовый класс для всех форматтеров сообщений"""

    def __init__(self, localization_service: ILocalizationService):
        """
        Инициализация базового форматтера

        Args:
            localization_service: Сервис локализации сообщений
        """
        self.localization_service = localization_service
        self.logger = logging.getLogger(self.__class__.__name__)
        self.date_helper = DateHelper()
        self.format_helper = FormatHelper()

    def get_localized_message(self, key: str, lang: Optional[str] = None, **params) -> str:
        """
        Получает локализованное сообщение по ключу

        Args:
            key: Ключ сообщения
            lang: Код языка
            **params: Параметры для форматирования

        Returns:
            str: Локализованное сообщение
        """
        return self.localization_service.get_message(key, lang, **params)

    def get_localized_meal_type(self, meal_type: str, lang: Optional[str] = None) -> str:
        """
        Получает локализованный тип приема пищи

        Args:
            meal_type: Тип приема пищи на английском
            lang: Код языка

        Returns:
            str: Локализованный тип приема пищи
        """
        return self.get_localized_message(LK.Common.MEAL_TYPES.format(meal_type), lang)

    def get_meal_emoji(self, meal_type: str, lang: Optional[str] = None) -> str:
        """
        Возвращает эмодзи для типа приема пищи

        Args:
            meal_type: Тип приема пищи
            lang: Код языка

        Returns:
            str: Эмодзи
        """
        emoji = self.get_localized_message(LK.Common.MEAL_EMOJIS.format(meal_type), lang)
        if not emoji:
            emoji = "🍴"
        return emoji.lower()

    def format_for_whatsapp(self, message: str | None) -> str | None:
        """
        Форматирует сообщение для WhatsApp

        Args:
            message: Исходное сообщение

        Returns:
            str: Отформатированное сообщение
        """
        if not message:
            return None
        return self.format_helper.format_message_for_whatsapp(message)

    def handle_exception(self, e: Exception, error_message: str, error_key: str, lang: Optional[str] = None) -> str:
        """
        Обрабатывает исключение и возвращает сообщение об ошибке

        Args:
            e: Исключение
            error_message: Сообщение для логирования
            error_key: Ключ локализации для сообщения об ошибке
            lang: Код языка

        Returns:
            str: Локализованное сообщение об ошибке
        """
        self.logger.error(f"{error_message}: {str(e)}")
        return self.get_localized_message(error_key, lang)
