# app/services/localization/localization_service.py
from typing import Dict, Any, Optional
import logging
from app.db.interfaces.user_repository_interface import IUserRepository
from app.services.localization.localization_interface import ILocalizationService
from app.services.localization.localization_messages import LOCALIZED_MESSAGES

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
        self.messages = LOCALIZED_MESSAGES

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
        # Если язык не указан, используем язык по умолчанию
        if not lang:
            lang = self.DEFAULT_LANGUAGE

        # Проверяем существование языка
        if lang not in self.messages:
            lang = self.DEFAULT_LANGUAGE

        # Разбиваем ключ на части для поддержки вложенной структуры
        key_parts = key.split('.')

        # Получаем сообщение по ключу
        message_dict = self.messages[lang]

        for part in key_parts:
            if isinstance(message_dict, dict) and part in message_dict:
                message_dict = message_dict[part]
            else:
                # Если ключ не найден, ищем в языке по умолчанию
                if lang != self.DEFAULT_LANGUAGE:
                    return self.get_message(key, self.DEFAULT_LANGUAGE, **params)

                # Если ключ не найден и в языке по умолчанию, возвращаем ключ
                logger.warning(f"Message key not found: {key} (lang: {lang})")
                return f"[{key}]"

        # Если сообщение не является строкой, возвращаем ключ
        if not isinstance(message_dict, str):
            logger.warning(f"Message is not a string: {key} (lang: {lang})")
            return f"[{key}]"

        # Форматируем сообщение с переданными параметрами
        try:
            return message_dict.format(**params)
        except KeyError as e:
            # В случае ошибки форматирования, логируем и возвращаем шаблон как есть
            logger.warning(f"Missing format parameter in message {key}: {e}")
            return message_dict
        except Exception as e:
            # Любая другая ошибка
            logger.error(f"Error formatting message {key}: {e}")
            return message_dict

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
                return self.DEFAULT_LANGUAGE

            # Получаем язык из данных пользователя, если он есть
            lang = user.get("language", self.DEFAULT_LANGUAGE)

            # Проверяем существование языка
            if lang not in self.messages:
                return self.DEFAULT_LANGUAGE

            return lang

        except Exception as e:
            logger.error(f"Error getting user language: {e}")
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
            logger.info(f"Устанавливает предпочитаемый язык пользователя: '{lang}'")
            # Проверяем существование языка
            if lang not in self.messages:
                logger.error(f"Localization texts for '{lang}' not found")
                return False

            # Обновляем язык пользователя в репозитории
            result = await self.user_repository.update(user_id, {"language": lang})
            logger.info(f"result: '{result}'")
            return result

        except Exception as e:
            logger.error(f"Error setting user language: {e}")
            return False