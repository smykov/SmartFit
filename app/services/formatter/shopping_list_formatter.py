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

            # Получаем общее количество продуктов
            total_items = len(shopping_list_data.get("items", []))

            # Добавляем информацию о количестве продуктов с поддержкой плюральных форм
            message += self.get_localized_message(
                LK.Shopping.ITEMS_COUNT,
                lang,
                count=total_items
            )
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

                # Форматируем элемент списка с использованием локализации
                item_text = self.get_localized_message(
                    LK.Shopping.ITEM_INFO_FORMAT,
                    lang,
                    name=name,
                    quantity=quantity,
                    unit=unit
                )

                # Добавляем информацию о цене, если она есть
                if price:
                    item_text += self.get_localized_message(
                        LK.Shopping.PRICE_FORMAT,
                        lang,
                        price=price
                    )

                # Отмечаем купленные продукты
                if is_purchased:
                    item_text = self.get_localized_message(
                        LK.Shopping.PURCHASED_ITEM_FORMAT,
                        lang,
                        item=item_text
                    )
                else:
                    item_text = item_text  # Без дополнительного форматирования

                # Добавляем в соответствующую категорию
                categories[category].append(item_text)

            # Формируем сообщение по категориям
            for category, items in categories.items():
                if items:
                    # Получаем локализованное название категории
                    category_name = self.get_localized_message(
                        f"shopping.categories.{category.lower()}",
                        lang
                    )

                    # Добавляем заголовок категории с количеством продуктов
                    message += self.get_localized_message(
                        LK.Shopping.CATEGORY_WITH_COUNT_FORMAT,
                        lang,
                        category=category_name,
                        count=len(items)
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

            # Подсчет купленных и оставшихся продуктов
            purchased_items = sum(1 for item in shopping_list_data.get("items", []) if item.get("is_purchased", False))
            total_items = len(shopping_list_data.get("items", []))
            remaining_items = total_items - purchased_items

            # Добавляем информацию о прогрессе покупок
            if total_items > 0:
                message += self.get_localized_message(
                    LK.Shopping.SHOPPING_PROGRESS,
                    lang,
                    purchased=purchased_items,
                    remaining=remaining_items,
                    total=total_items,
                    percentage=int(purchased_items / total_items * 100) if total_items > 0 else 0
                )

            return self.format_for_whatsapp(message)

        except Exception as e:
            return self.handle_exception(
                e,
                "Error formatting shopping list",
                LK.Shopping.FORMATTING_ERROR,
                lang
            )
