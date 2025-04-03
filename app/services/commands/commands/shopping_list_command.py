import re
from typing import Dict, Any, Optional

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
            # Проверяем, есть ли текущий план диеты
            diet_plan = await self.dependencies['diet_service'].get_current_diet(user_id)

            if not diet_plan:
                return {
                    "success": False, 
                    "message": self.messages.NO_DIET_PLAN
                }

            # Если params содержит параметры для покупки продукта
            if params and 'params' in params:
                product_name = params['params'][0]
                
                # Проверяем формат команды
                product_match = re.match(r'^купил[а]?\s+(.+)$', product_name.lower())
                
                if not product_match:
                    return {
                        "success": False, 
                        "message": self.messages.INVALID_PRODUCT_FORMAT
                    }
                
                # Получаем название продукта
                product = product_match.group(1).strip()
                
                # Помечаем продукт как купленный
                result = await self.dependencies['diet_service'].mark_product_as_purchased(user_id, product)
                
                if result.get("success"):
                    return {
                        "success": True, 
                        "message": self.messages.PRODUCT_MARKED.format(product=product)
                    }
                else:
                    return {
                        "success": False, 
                        "message": self.messages.PRODUCT_NOT_FOUND.format(product=product)
                    }

            # Уведомляем о начале генерации списка покупок
            await self.dependencies['message_service'].send_message(
                self.dependencies['user']['phone_number'], 
                self.messages.SHOPPING_LIST_GENERATION
            )

            # Генерируем список покупок
            shopping_list = await self.dependencies['diet_service'].generate_shopping_list(diet_plan["id"])

            if shopping_list and "error" not in shopping_list:
                # Форматируем список покупок
                formatted_list = self.dependencies['diet_service'].format_shopping_list(shopping_list)
                
                return {
                    "success": True, 
                    "message": formatted_list
                }
            else:
                return {
                    "success": False, 
                    "message": self.messages.SHOPPING_LIST_ERROR
                }

        except Exception as e:
            print(f"Ошибка при работе со списком покупок: {str(e)}")
            return {
                "success": False, 
                "message": self.messages.SHOPPING_LIST_ERROR
            }

    def get_error_message(self) -> str:
        """
        Получение сообщения об ошибке
        
        Returns:
            str: Сообщение об ошибке
        """
        return self.messages.NO_DIET_PLAN