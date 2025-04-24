# app/localization/formats.py
from typing import Dict, Any, Optional, Union
import re
import datetime
import locale
from decimal import Decimal


class PluralRule:
    """
    Класс для определения правил выбора плюральной формы
    для различных языков
    """

    @staticmethod
    def get_plural_form(count: Union[int, float], lang: str = 'en') -> str:
        """
        Возвращает название плюральной формы для числа и языка

        Args:
            count: Число для определения формы
            lang: Код языка (en, ru, es)

        Returns:
            str: Название плюральной формы ('one', 'few', 'many', 'other')
        """
        # Округляем число для определения формы
        if isinstance(count, float):
            count_int = int(count)
        else:
            count_int = count

        # Правила для английского (и большинства других языков)
        if lang in ['en', 'es']:
            return 'one' if abs(count_int) == 1 else 'other'

        # Правила для русского языка
        elif lang == 'ru':
            count_abs = abs(count_int)
            mod10 = count_abs % 10
            mod100 = count_abs % 100

            # 1, 21, 31, ... (кроме 11, 111, ...)
            if mod10 == 1 and mod100 != 11:
                return 'one'
            # 2-4, 22-24, ... (кроме 12-14, 112-114, ...)
            elif 2 <= mod10 <= 4 and (mod100 < 12 or mod100 > 14):
                return 'few'
            # 0, 5-20, 25-30, ...
            else:
                return 'many'

        # По умолчанию
        return 'other'


class NumberFormatter:
    """
    Класс для форматирования чисел с учетом локали
    """

    @staticmethod
    def format_number(number: Union[int, float, Decimal],
                      lang: str = 'en',
                      decimal_places: int = 2) -> str:
        """
        Форматирует число с учетом локали

        Args:
            number: Число для форматирования
            lang: Код языка (определяет локаль)
            decimal_places: Количество десятичных знаков

        Returns:
            str: Отформатированное число
        """
        # Определяем локаль
        locale_map = {
            'en': 'en_US.UTF-8',
            'ru': 'ru_RU.UTF-8',
            'es': 'es_ES.UTF-8'
        }

        # Проверяем, является ли число целым
        is_integer = False
        if isinstance(number, int):
            is_integer = True
        elif isinstance(number, float) and number.is_integer():
            is_integer = True
        elif isinstance(number, Decimal) and number == int(number):
            is_integer = True

        try:
            # Пытаемся установить локаль
            current_locale = locale.getlocale(locale.LC_NUMERIC)
            locale.setlocale(locale.LC_NUMERIC, locale_map.get(lang, 'en_US.UTF-8'))

            # Форматируем число
            if is_integer:
                # Целое число
                formatted = locale.format_string("%d", int(number), grouping=True)
            else:
                # Число с плавающей точкой
                format_string = f"%.{decimal_places}f"
                formatted = locale.format_string(format_string, number, grouping=True)

            # Восстанавливаем предыдущую локаль
            locale.setlocale(locale.LC_NUMERIC, current_locale)

            return formatted

        except (locale.Error, ValueError):
            # В случае ошибки локали используем базовое форматирование
            if is_integer:
                return f"{int(number):,d}"
            else:
                return f"{number:,.{decimal_places}f}"


class DateFormatter:
    """
    Класс для форматирования дат в соответствии с локалью
    """

    @staticmethod
    def format_date(date_value: Union[datetime.date, datetime.datetime, str],
                    format_str: Optional[str] = None,
                    lang: str = 'en') -> str:
        """
        Форматирует дату с учетом локали

        Args:
            date_value: Дата для форматирования
            format_str: Строка формата (если None, используется формат по умолчанию для локали)
            lang: Код языка

        Returns:
            str: Отформатированная дата
        """
        # Преобразуем строку в дату, если необходимо
        if isinstance(date_value, str):
            try:
                date_value = datetime.datetime.fromisoformat(date_value)
            except ValueError:
                try:
                    date_value = datetime.datetime.strptime(date_value, "%Y-%m-%d")
                except ValueError:
                    return date_value

        # Определяем форматы для разных языков
        if format_str is None:
            format_map = {
                'en': '%B %d, %Y',  # December 31, 2023
                'ru': '%d %B %Y',  # 31 декабря 2023
                'es': '%d de %B de %Y'  # 31 de diciembre de 2023
            }
            format_str = format_map.get(lang, '%d.%m.%Y')

        # Определяем локаль
        locale_map = {
            'en': 'en_US.UTF-8',
            'ru': 'ru_RU.UTF-8',
            'es': 'es_ES.UTF-8'
        }

        try:
            # Пытаемся установить локаль
            current_locale = locale.getlocale(locale.LC_TIME)
            locale.setlocale(locale.LC_TIME, locale_map.get(lang, 'en_US.UTF-8'))

            # Форматируем дату
            formatted = date_value.strftime(format_str)

            # Восстанавливаем предыдущую локаль
            locale.setlocale(locale.LC_TIME, current_locale)

            return formatted

        except (locale.Error, ValueError, AttributeError):
            # В случае ошибки используем базовое форматирование
            try:
                return date_value.strftime('%d.%m.%Y')
            except (ValueError, AttributeError):
                return str(date_value)


class StringUtils:
    """
    Утилиты для работы со строками локализации
    """

    @staticmethod
    def apply_style(text: str, style: str) -> str:
        """
        Применяет стилевое оформление для мессенджеров

        Args:
            text: Исходный текст
            style: Тип стиля ('bold', 'italic', 'code', 'strikethrough')

        Returns:
            str: Отформатированный текст
        """
        if not text:
            return text

        style_markers = {
            'bold': '*{}*',
            'italic': '_{}_',
            'code': '`{}`',
            'pre': '```{}```',
            'strikethrough': '~{}~',
        }

        marker = style_markers.get(style.lower())
        if marker:
            return marker.format(text)
        return text