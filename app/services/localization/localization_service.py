from typing import Dict, Any, Optional
import logging

from app.db.interfaces.user_repository_interface import IUserRepository
from app.services.localization.localization_interface import ILocalizationService
from app.localization.registry import get_message

logger = logging.getLogger(__name__)


class LocalizationService(ILocalizationService):
    """
    Сервис для локализации сообщений в приложении
    """

    DEFAULT_LANGUAGE = "en"

    def __init__(self, user_repository: IUserRepository):
        """
        Инициализация сервиса локализации

        Args:
            user_repository: Репозиторий для работы с пользователями
        """
        self.user_repository = user_repository

    def get_message(self, key: str, lang: Optional[str] = None, **params) -> str:
        """
        Получает локализованное сообщение по ключу

        Args:
            key: Ключ сообщения
            lang: Код языка (по умолчанию используется системный язык)
            **params: Параметры для форматирования сообщения

        Returns:
            str: Локализованное сообщение с подставленными параметрами
        """
        logger.debug(f"Localization request: key='{key}', lang='{lang}', params={params}")

        # Если язык не указан, используем язык по умолчанию
        if not lang:
            lang = self.DEFAULT_LANGUAGE
            logger.debug(f"No lang specified, using default: '{lang}'")

        try:
            # Копируем параметры, чтобы избежать модификации исходного словаря
            params_copy = params.copy()

            # Убедимся, что 'lang' не дублируется
            if 'lang' in params_copy:
                # Если lang не передан явно, используем из params
                if lang is None:
                    lang = params_copy['lang']
                # Удаляем из параметров, чтобы избежать дублирования
                del params_copy['lang']

            # Получаем результат
            result = get_message(key, lang, **params_copy)
            logger.debug(f"Localization result for '{key}': '{result}'")

            # Проверка на возврат самого ключа (признак ошибки)
            if result == key:
                logger.warning(f"Possible localization error: key='{key}' returned as value")

        except Exception as e:
            logger.error(f"Error getting localized message: {e}")
            # В случае ошибки возвращаем ключ
            return f"[{key}]"

    async def get_user_language(self, user_id: str) -> str:
        """
        Получает предпочитаемый язык пользователя

        Args:
            user_id: ID пользователя

        Returns:
            str: Код языка пользователя
        """
        try:
            # Получаем пользователя из репозитория
            user = await self.user_repository.get_by_id(user_id)

            if not user:
                logger.warning(f"User (id: {user_id}) not found")
                return self.DEFAULT_LANGUAGE

            # Получаем язык из данных пользователя, если он есть
            lang = user.get("language", self.DEFAULT_LANGUAGE)

            return lang

        except Exception as e:
            logger.error(f"Error getting user language: {str(e)}")
            return self.DEFAULT_LANGUAGE

    async def set_user_language(self, user_id: str, lang: str) -> bool:
        """
        Устанавливает предпочитаемый язык пользователя

        Args:
            user_id: ID пользователя
            lang: Код языка

        Returns:
            bool: Результат операции
        """
        try:
            logger.info(f"Setting user preferred language: '{lang}'")

            # Обновляем язык пользователя в репозитории
            result = await self.user_repository.update(user_id, {"language": lang})
            logger.info(f"Result: '{result}'")
            return result

        except Exception as e:
            logger.error(f"Error setting user language: {e}")
            return False
