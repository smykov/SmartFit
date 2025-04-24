# app/services/commands/commands/shopping_list_command.py
import re
from typing import Dict, Any, Optional

from app.constants.localization_keys import LocalizationKeys as LK
from app.services.commands.base_command import BaseCommand


class ShoppingListCommand(BaseCommand):
    """
    Команда для работы со списком покупок
    """

    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды работы со списком покупок

        Args:
            user_id: ID пользователя
            params: Параметры команды (содержит текст сообщения)

        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        try:
            # Получаем язык пользователя
            lang = None
            if hasattr(self, 'localization_service') and self.localization_service:
                lang = await self.localization_service.get_user_language(user_id)

            # Проверяем, есть ли текущий план диеты
            diet_plan = await self.dependencies['diet_service'].get_current_diet(user_id)

            if not diet_plan:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.ShoppingList.NO_DIET_PLAN, lang)
                }

            # Если params содержит параметры для покупки продукта
            if params and 'params' in params:
                product_name = params['params'][0]

                # Проверяем формат команды
                product_match = re.match(r'^купил[а]?\s+(.+)$', product_name.lower())

                if not product_match:
                    return {
                        "success": False,
                        "message": self.get_localized_message(LK.Commands.ShoppingList.INVALID_PRODUCT_FORMAT, lang)
                    }

                # Получаем название продукта
                product = product_match.group(1).strip()

                # Помечаем продукт как купленный
                result = await self.dependencies['diet_service'].mark_product_as_purchased(user_id, product)

                if result.get("success"):
                    return {
                        "success": True,
                        "message": self.get_localized_message(LK.Commands.ShoppingList.PRODUCT_MARKED, lang,
                                                              product=product)
                    }
                else:
                    return {
                        "success": False,
                        "message": self.get_localized_message(LK.Commands.ShoppingList.PRODUCT_NOT_FOUND, lang,
                                                              product=product)
                    }

            # Уведомляем о начале генерации списка покупок
            await self.dependencies['message_service'].send_message(
                self.dependencies['user'].get('phone_number', ''),
                self.get_localized_message(LK.Commands.ShoppingList.GENERATING, lang),
                {"user_id": user_id}
            )

            # Генерируем список покупок
            shopping_list = await self.dependencies['diet_service'].generate_shopping_list(diet_plan["id"], lang)

            if shopping_list and "error" not in shopping_list:
                # Форматируем список покупок
                formatted_list = self.dependencies['diet_service'].format_shopping_list(shopping_list, lang)

                return {
                    "success": True,
                    "message": formatted_list
                }
            else:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.ShoppingList.ERROR, lang)
                }

        except Exception as e:
            self.logger.error(f"Error processing shopping list command: {str(e)}")
            return {
                "success": False,
                "message": self.get_localized_message(LK.Commands.ShoppingList.ERROR, lang)
            }

    def get_error_message(self) -> str:
        """
        Получение сообщения об ошибке

        Returns:
            str: Сообщение об ошибке
        """
        return self.get_localized_message(LK.Commands.ShoppingList.NO_DIET_PLAN)
