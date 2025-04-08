# app/services/commands/commands/language_command.py
from typing import Dict, Any, Optional
from app.services.commands.base_command import BaseCommand


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
        phone_number = self.dependencies['user']['phone_number']

        # Получаем код языка из параметров
        if not params or 'language' not in params:
            # Отправляем список доступных языков
            message = "Доступные языки / Idiomas disponibles:\n\n" + \
                      "🇪🇸 Español: Escriba 'idioma es'\n" + \
                      "🇷🇺 Русский: Напишите 'язык ru'"

            return {
                "success": True,
                "message": message
            }

        # Получаем код языка
        language_code = params['language']

        # Проверяем доступные языки
        available_languages = ["es", "ru"]

        if language_code not in available_languages:
            return {
                "success": False,
                "message": f"Неподдерживаемый код языка. Доступные варианты: {', '.join(available_languages)}"
            }

        # Получаем локализационный сервис из зависимостей
        localization_service = self.dependencies.get('localization_service')

        if not localization_service:
            return {
                "success": False,
                "message": "Сервис локализации недоступен"
            }

        # Устанавливаем язык пользователя
        success = await localization_service.set_user_language(user_id, language_code)

        if not success:
            return {
                "success": False,
                "message": "Не удалось обновить язык пользователя"
            }

        # Формируем подтверждающее сообщение на выбранном языке
        languages = {
            "es": "¡Idioma cambiado a Español!",
            "ru": "Язык изменен на Русский!"
        }

        return {
            "success": True,
            "message": languages[language_code]
        }