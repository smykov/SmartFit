# app/services/localization/localization_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ILocalizationService(ABC):
    """
    Интерфейс для сервиса локализации сообщений
    """

    def __init__(self):
        self.DEFAULT_LANGUAGE = "en"

    @abstractmethod
    def get_message(self, key: str, lang: Optional[str] = None, **params) -> str:
        """
        Получает локализованное сообщение по ключу

        Args:
            key: Ключ сообщения (может быть вложенным через точку, например 'diet.created')
            lang: Код языка (по умолчанию используется системный язык)
            **params: Параметры для форматирования сообщения

        Returns:
            str: Локализованное сообщение с подставленными параметрами
        """
        pass

    @abstractmethod
    async def get_user_language(self, user_id: str) -> str:
        """
        Получает предпочитаемый язык пользователя

        Args:
            user_id: ID пользователя

        Returns:
            str: Код языка пользователя
        """
        pass

    @abstractmethod
    async def set_user_language(self, user_id: str, lang: str) -> bool:
        """
        Устанавливает предпочитаемый язык пользователя

        Args:
            user_id: ID пользователя
            lang: Код языка

        Returns:
            bool: Результат операции
        """
        pass