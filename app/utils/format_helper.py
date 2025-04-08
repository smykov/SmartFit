# app/utils/format_helper.py
import re
from typing import Dict, Any, List

from app.constants.localization_keys import ProductCategory


class FormatHelper:
    """Класс-помощник для форматирования текстов"""

    @staticmethod
    def format_message_for_whatsapp(message: str) -> str:
        """
        Форматирует текст сообщения для WhatsApp

        Args:
            message: Исходное сообщение

        Returns:
            str: Отформатированное сообщение
        """
        # Добавляем отступы для лучшей читаемости
        formatted_text = message

        # Форматируем нумерованные списки: находим шаблон "N. Текст" и добавляем перенос строки
        formatted_text = re.sub(r'(\d+\.\s*[^\n.]+)\.?\s+(?=\d+\.)', r'\1.\n', message)

        # Добавляем отступы между маркерами списка
        # formatted_text = re.sub(r'(•[^\n]+)', r'\1\n', formatted_text)

        # Убираем лишние пустые строки
        formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)

        return formatted_text

    @staticmethod
    def apply_style(text: str, style: str) -> str:
        """
        Применяет стиль форматирования к тексту для WhatsApp

        Args:
            text: Исходный текст
            style: Стиль форматирования ('bold', 'italic', 'strikethrough', 'monospace')

        Returns:
            str: Отформатированный текст
        """
        if style == 'bold':
            return f"*{text}*"
        elif style == 'italic':
            return f"_{text}_"
        elif style == 'strikethrough':
            return f"~{text}~"
        elif style == 'monospace':
            return f"```{text}```"
        else:
            return text

    @staticmethod
    def get_relevance_stars(score: int) -> str:
        """
        Возвращает звездочки для отображения релевантности

        Args:
            score: Оценка релевантности (1-10)

        Returns:
            str: Строка со звездочками
        """
        if not score:
            return ""

        # Преобразуем оценку 1-10 в шкалу 1-5 звезд
        stars_count = max(1, min(5, round(score / 2)))
        return "★" * stars_count

    @staticmethod
    def categorize_product(product_name: str) -> str:
        """
        Определяет категорию продукта по его названию

        Args:
            product_name: Название продукта

        Returns:
            str: Категория продукта
        """
        name_lower = product_name.lower()

        # Словарь категорий с ключевыми словами
        category_keywords = {
            ProductCategory.FRUITS_VEGETABLES.value: [
                "фрукт", "овощ", "ягод", "банан", "яблок", "морковь", "картофель",
                "помидор", "огурец", "груш", "апельсин", "капуст", "лук", "чеснок"
            ],
            ProductCategory.MEAT_FISH.value: [
                "мясо", "рыба", "курица", "говядина", "свинина", "филе", "фарш",
                "котлет", "стейк", "сосиск", "колбас", "индейк", "лосось", "треск"
            ],
            ProductCategory.DAIRY.value: [
                "молоко", "сыр", "творог", "йогурт", "кефир", "сметана", "масло",
                "сливк", "ряженк", "простокваш", "брынза"
            ],
            ProductCategory.BREAD_CEREALS.value: [
                "хлеб", "крупа", "рис", "овсянка", "мука", "макароны", "паста",
                "булочк", "булка", "гречка", "пшено", "перловка", "кускус"
            ],
            ProductCategory.SPICES.value: [
                "специя", "соль", "перец", "приправа", "соус", "паприка", "карри",
                "базилик", "майоран", "куркума", "корица", "гвоздика", "орегано"
            ],
            ProductCategory.DRINKS.value: [
                "напиток", "вода", "сок", "чай", "кофе", "компот", "морс", "квас",
                "лимонад", "коктейль", "смузи", "молочный коктейль"
            ]
        }

        # Проверяем каждую категорию на соответствие ключевым словам
        for category, keywords in category_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                return category

        # Если ни одна категория не подошла
        return ProductCategory.OTHER.value
