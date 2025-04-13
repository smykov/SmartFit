# app/services/commands/commands/language_command.py
from typing import Dict, Any, Optional
from app.services.commands.base_command import BaseCommand
from app.constants.localization_keys import LocalizationKeys as LK


class LanguageCommand(BaseCommand):
    """
    Команда для изменения языка пользователя
    """

    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды изменения языка

        Args:
            user_id: ID пользователя
            params: Параметры команды (содержит код языка)

        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        # Получаем текущий язык пользователя
        current_lang = None
        if hasattr(self, 'localization_service') and self.localization_service:
            current_lang = await self.localization_service.get_user_language(user_id)

        phone_number = self.dependencies['user']['phone_number']

        # Получаем код языка из параметров
        if not params or 'language' not in params:
            # Отправляем список доступных языков
            message = self.get_localized_message(LK.Commands.Language.LANGUAGES_LIST, current_lang)

            return {
                "success": True,
                "message": message
            }

        # Получаем код языка
        language_code = params['language']

        # Проверяем доступные языки
        # TODO брать из модуля локализации список языков
        available_languages = ["en", "es", "ru"]

        if language_code not in available_languages:
            return {
                "success": False,
                "message": self.get_localized_message(
                    LK.Commands.Language.UNSUPPORTED_LANGUAGE,
                    current_lang,
                    languages=", ".join(available_languages)
                )
            }

        # Получаем локализационный сервис из зависимостей
        localization_service = self.dependencies.get('localization_service')

        if not localization_service:
            return {
                "success": False,
                "message": self.get_localized_message(LK.Commands.Language.UNAVAILABLE_SERVICE, current_lang)
            }

        # Устанавливаем язык пользователя
        success = await localization_service.set_user_language(user_id, language_code)

        if not success:
            return {
                "success": False,
                "message": self.get_localized_message(LK.Commands.Language.UNAVAILABLE_SERVICE, current_lang)
            }

        # Формируем подтверждающее сообщение на выбранном языке
        # Используем языковые ключи для разных языков
        # TODO брать из модуля локализации список языков
        language_confirmation_keys = {
            "en": LK.Commands.Language.LANGUAGE_CHANGED,
            "ru": LK.Commands.Language.LANGUAGE_CHANGED,
            "es": LK.Commands.Language.LANGUAGE_CHANGED
        }

        # Получаем сообщение на новом языке
        message = self.get_localized_message(
            language_confirmation_keys[language_code],
            language_code
        )

        return {
            "success": True,
            "message": message
        }