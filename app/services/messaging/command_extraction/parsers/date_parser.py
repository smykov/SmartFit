# app/services/messaging/command_extraction/parsers/date_parser.py
import re
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
import calendar
from app.utils.date_helper import DateHelper


class DateParsingError(Exception):
    """Исключение для ошибок парсинга дат"""
    pass


class DateParser:
    """
    Парсер для работы с датами в различных форматах.
    Следует принципу SRP - только парсинг дат.
    """

    # Словари для локализации (можно вынести в отдельный конфиг)
    MONTH_NAMES = {
        'ru': {
            'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
            'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
            'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
        },
        'en': {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        },
        'es': {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
    }

    WEEKDAY_NAMES = {
        'ru': {
            'понедельник': 'monday', 'вторник': 'tuesday', 'среда': 'wednesday',
            'четверг': 'thursday', 'пятница': 'friday', 'суббота': 'saturday', 'воскресенье': 'sunday'
        },
        'en': {
            'monday': 'monday', 'tuesday': 'tuesday', 'wednesday': 'wednesday',
            'thursday': 'thursday', 'friday': 'friday', 'saturday': 'saturday', 'sunday': 'sunday'
        },
        'es': {
            'lunes': 'monday', 'martes': 'tuesday', 'miércoles': 'wednesday',
            'jueves': 'thursday', 'viernes': 'friday', 'sábado': 'saturday', 'domingo': 'sunday'
        }
    }

    def __init__(self, user_timezone: Optional[str] = None, language: str = 'ru'):
        """
        Инициализация парсера дат

        Args:
            user_timezone: Часовой пояс пользователя
            language: Язык для локализации
        """
        self.user_timezone = user_timezone
        self.language = language
        self.today = DateHelper.get_tracking_date(user_timezone)

    def parse_relative_date(self, relative_term: str) -> Optional[date]:
        """
        Парсит относительные даты (сегодня, завтра, вчера)

        Args:
            relative_term: Относительный термин

        Returns:
            Optional[date]: Дата или None
        """
        relative_terms = {
            'ru': {
                'сегодня': 0, 'завтра': 1, 'вчера': -1,
                'послезавтра': 2, 'позавчера': -2
            },
            'en': {
                'today': 0, 'tomorrow': 1, 'yesterday': -1,
                'day after tomorrow': 2, 'day before yesterday': -2
            },
            'es': {
                'hoy': 0, 'mañana': 1, 'ayer': -1,
                'pasado mañana': 2, 'anteayer': -2
            }
        }

        terms = relative_terms.get(self.language, relative_terms['ru'])
        term_lower = relative_term.lower().strip()

        if term_lower in terms:
            days_offset = terms[term_lower]
            return self.today + timedelta(days=days_offset)

        return None

    def parse_weekday(self, weekday_name: str) -> Optional[Tuple[date, str]]:
        """
        Парсит день недели и возвращает ближайшую БУДУЩУЮ дату

        Args:
            weekday_name: Название дня недели

        Returns:
            Optional[Tuple[date, str]]: (дата, день_недели) или None
        """
        weekdays = self.WEEKDAY_NAMES.get(self.language, self.WEEKDAY_NAMES['ru'])
        weekday_name_lower = weekday_name.lower().strip()

        if weekday_name_lower in weekdays:
            target_weekday = weekdays[weekday_name_lower]
            # Получаем ближайший БУДУЩИЙ день недели
            target_date = self._get_next_weekday_date(target_weekday)
            return target_date, target_weekday

        return None

    def _get_next_weekday_date(self, target_weekday: str) -> date:
        """
        Получает ближайшую БУДУЩУЮ дату для указанного дня недели

        Args:
            target_weekday: День недели ('monday', 'tuesday', etc.)

        Returns:
            date: Ближайшая будущая дата для этого дня недели
        """
        # Маппинг дней недели в числа (0 = понедельник, 6 = воскресенье)
        weekday_to_num = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }

        target_num = weekday_to_num.get(target_weekday, 0)
        current_weekday = self.today.weekday()

        # Вычисляем количество дней до следующего вхождения этого дня недели
        days_ahead = target_num - current_weekday

        # Если это текущий день недели или прошедший день, берем следующую неделю
        if days_ahead <= 0:
            days_ahead += 7

        return self.today + timedelta(days=days_ahead)

    def parse_absolute_date(self, date_str: str) -> Optional[date]:
        """
        Парсит абсолютные даты в форматах "28 мая", "28.05"

        Args:
            date_str: Строка с датой

        Returns:
            Optional[date]: Дата или None

        Raises:
            DateParsingError: При некорректной дате
        """
        date_str = date_str.strip()
        current_year = self.today.year

        # Паттерн для "28 мая"
        month_pattern = r'(\d{1,2})\s+([а-яё]+)'
        match = re.match(month_pattern, date_str, re.IGNORECASE)

        if match:
            day = int(match.group(1))
            month_name = match.group(2).lower()

            months = self.MONTH_NAMES.get(self.language, self.MONTH_NAMES['ru'])
            if month_name in months:
                month = months[month_name]
                return self._validate_and_create_date(current_year, month, day)

        # Паттерн для "28.05" или "28/05"
        numeric_pattern = r'(\d{1,2})[./](\d{1,2})'
        match = re.match(numeric_pattern, date_str)

        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            return self._validate_and_create_date(current_year, month, day)

        return None

    def _validate_and_create_date(self, year: int, month: int, day: int) -> date:
        """
        Валидирует и создает дату

        Args:
            year: Год
            month: Месяц
            day: День

        Returns:
            date: Валидная дата

        Raises:
            DateParsingError: При некорректной дате
        """
        try:
            # Проверяем валидность даты
            if month < 1 or month > 12:
                raise DateParsingError(f"Некорректный месяц: {month}")

            # Проверяем количество дней в месяце
            max_days = calendar.monthrange(year, month)[1]
            if day < 1 or day > max_days:
                raise DateParsingError(
                    f"В {calendar.month_name[month]} {year} года {max_days} дней, а указан {day} день")

            return date(year, month, day)

        except ValueError as e:
            raise DateParsingError(f"Некорректная дата {day}.{month}.{year}: {str(e)}")

