# app/services/commands/commands/language_command.py
from typing import Dict, Any, Optional
from app.services.commands.base_command import BaseCommand
from app.constants.localization_keys import LocalizationKeys as LK


# Добавить в CommandFactory новую команду
class SetMessengerCommand(BaseCommand):
    """Команда для изменения предпочитаемого мессенджера"""

    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Получаем текущий язык пользователя
        current_lang = None
        if hasattr(self, 'localization_service') and self.localization_service:
            current_lang = await self.localization_service.get_user_language(user_id)

        try:
            if not params or 'messenger' not in params:
                message = self.get_localized_message(LK.Commands.Messenger.MESSENGER_LIST, current_lang)
                return {
                    "success": False,
                    "message": message
                }

            messenger = params['messenger'].lower()
            if messenger not in ['whatsapp', 'telegram']:
                message = self.get_localized_message(LK.Commands.Messenger.MESSENGER_LIST, current_lang)

                return {
                    "success": False,
                    "message": message
                }

            # Обновляем предпочтения пользователя
            result = await self.user_repository.update(user_id, {"preferred_messenger": messenger})

            if result:
                message = self.get_localized_message(LK.Commands.Messenger.MESSENGER_CHANGED, current_lang, messenger_name=messenger.capitalize())
                return {
                    "success": True,
                    "message": message
                }
            else:
                message = self.get_localized_message(LK.Commands.Messenger.ERROR, current_lang)
                return {
                    "success": False,
                    "message": message
                }

        except Exception as e:
            message = self.get_localized_message(LK.Commands.Messenger.ERROR, current_lang)
            return {
                "success": False,
                "message": message
            }
