# app/services/formatter/shopping_list_formatter.py
from typing import Dict, Any, List, Optional

from app.constants.localization_keys import LocalizationKeys as LK, ProductCategory
from app.services.formatter.base_formatter import BaseFormatter
from app.services.localization.localization_interface import ILocalizationService
from app.utils.format_helper import FormatHelper


class ShoppingListFormatter(BaseFormatter):
    """Класс для форматирования списков покупок"""

    def __init__(self, localization_service: ILocalizationService):
        """
        Инициализация форматтера списка покупок

        Args:
            localization_service: Сервис локализации сообщений
        """
        super().__init__(localization_service)

    def format_shopping_list(self, shopping_list_data: Dict[str, Any], lang: Optional[str] = None) -> str:
        """
        Форматирует список покупок для отправки пользователю

        Args:
            shopping_list_data: Данные списка покупок
            lang: Код языка

        Returns:
            str: Отформатированный список покупок
        """
        try:
            # Формируем заголовок списка
            message = self.get_localized_message(LK.Shopping.HEADER, lang)

            # Получаем категории продуктов и инициализируем словарь для группировки
            categories = {
                category.value: []
                for category in ProductCategory
            }

            # Распределяем продукты по категориям
            for item in shopping_list_data.get("items", []):
                name = item.get("name", "")
                quantity = item.get("quantity", "")
                unit = item.get("unit", "")
                price = item.get("estimated_price", "")
                is_purchased = item.get("is_purchased", False)

                # Определяем категорию продукта
                category = item.get("category", FormatHelper.categorize_product(name))

                # Форматируем элемент списка
                item_text = f"{name}: {quantity} {unit}"
                if price:
                    item_text += f" (~{price} к.)"
                if is_purchased:
                    item_text = f"✅ {item_text}"

                # Добавляем в соответствующую категорию
                categories[category].append(item_text)

            # Формируем сообщение по категориям
            for category, items in categories.items():
                if items:
                    message += self.get_localized_message(
                        LK.Shopping.CATEGORY_FORMAT,
                        lang,
                        category=category
                    )
                    for item in items:
                        message += self.get_localized_message(
                            LK.Shopping.ITEM_FORMAT,
                            lang,
                            item=item
                        )
                    message += "\n"

            # Добавляем общую стоимость
            if "total_estimated_price" in shopping_list_data and shopping_list_data["total_estimated_price"]:
                message += self.get_localized_message(
                    LK.Shopping.TOTAL_PRICE,
                    lang,
                    price=shopping_list_data["total_estimated_price"]
                )

            # Добавляем инструкции для отметки покупок
            message += self.get_localized_message(LK.Shopping.INSTRUCTIONS, lang)

            return self.format_for_whatsapp(message)

        except Exception as e:
            return self.handle_exception(
                e, 
                "Error formatting shopping list", 
                LK.Shopping.FORMATTING_ERROR,
                lang
            )
