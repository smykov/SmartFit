# app/utils/date_helper.py
from datetime import datetime, date, timedelta
import pytz
import logging

from config import settings


class DateHelper:
    """Класс-помощник для работы с датами и днями недели"""

    # Словарь для преобразования названия дня недели в число (0 - понедельник, 6 - воскресенье)
    WEEKDAY_MAPPING = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    # Обратное отображение
    WEEKDAY_REVERSE_MAPPING = {
        0: "monday",
        1: "tuesday",
        2: "wednesday",
        3: "thursday",
        4: "friday",
        5: "saturday",
        6: "sunday"
    }

    @staticmethod
    def get_current_date() -> date:
        """
        Получает текущую дату с учетом временной зоны настроек

        Returns:
            date: Текущая дата
        """
        return datetime.now(pytz.timezone(settings.TIMEZONE)).date()

    @staticmethod
    def get_current_datetime() -> datetime:
        """
        Получает текущее время с учетом временной зоны настроек

        Returns:
            datetime: Текущие дата и время
        """
        return datetime.now(pytz.timezone(settings.TIMEZONE))

    @classmethod
    def get_day_of_week(cls, date_val: date = None) -> str:
        """
        Возвращает день недели для указанной даты в формате 'monday', 'tuesday' и т.д.

        Args:
            date_val: Дата (по умолчанию сегодня)

        Returns:
            str: День недели
        """
        if not date_val:
            date_val = cls.get_current_date()

        # Получаем номер дня недели (0 - понедельник, 6 - воскресенье)
        weekday = date_val.weekday()

        # Преобразуем в строковое представление
        return cls.WEEKDAY_REVERSE_MAPPING[weekday]

    @classmethod
    def get_nearest_date_for_weekday(cls, weekday_name: str) -> date:
        """
        Преобразует название дня недели в дату ближайшего такого дня недели

        Args:
            weekday_name: Название дня недели на английском (monday, tuesday и т.д.)

        Returns:
            date: Дата ближайшего дня недели
        """
        # Получаем текущую дату
        today = cls.get_current_date()

        # Получаем номер текущего дня недели (0 - понедельник, 6 - воскресенье)
        today_weekday = today.weekday()

        # Получаем номер целевого дня недели
        target_weekday = cls.WEEKDAY_MAPPING.get(weekday_name.lower())

        if target_weekday is None:
            # Если передано некорректное название дня недели, возвращаем текущую дату
            return today

        # Вычисляем разницу в днях
        days_diff = (target_weekday - today_weekday) % 7

        # Если разница 0 (тот же день) и нужен следующий такой день, добавляем 7 дней
        if days_diff == 0:
            days_diff = 7

        # Вычисляем дату ближайшего дня недели
        nearest_date = today + timedelta(days=days_diff)

        return nearest_date

    @staticmethod
    def format_date(date_value: date, format_str: str) -> str:
        """
        Форматирует дату согласно заданному формату

        Args:
            date_value: Дата для форматирования
            format_str: Строка формата даты

        Returns:
            str: Отформатированная дата
        """
        try:
            # Добавить проверку и логирование формата
            if not format_str or format_str == "common.day_format":
                # Если получен ключ локализации вместо формата, используем стандартный формат
                return date_value.strftime("%d.%m.%Y")
            return date_value.strftime(format_str)
        except Exception as e:
            # В случае ошибки используем стандартный формат
            logging.error(f"Error formatting date with format '{format_str}': {e}")
            return date_value.strftime("%d.%m.%Y")

    @staticmethod
    def parse_date_string(date_string: str, format_string: str = "%Y-%m-%d") -> date:
        """
        Преобразует строку даты в объект date

        Args:
            date_string: Строка с датой
            format_string: Формат даты в строке (по умолчанию '%Y-%m-%d')

        Returns:
            date: Объект date, представляющий указанную дату

        Raises:
            ValueError: Если строка имеет неверный формат
        """
        return datetime.strptime(date_string, format_string).date()

    @staticmethod
    def get_tracking_date(current_datetime=None):
        """
        Определяет дату для записи трекинга с учетом времени суток.
        Если время от 00:00 до 5:00, возвращает предыдущий день.

        Args:
            current_datetime: Текущая дата и время (если None, используется текущее время)

        Returns:
            date: Дата для записи трекинга
        """
        if current_datetime is None:
            current_datetime = datetime.now(pytz.timezone(settings.TIMEZONE))

        # Если время от 00:00 до 5:00, возвращаем предыдущий день
        if current_datetime.hour < 5:
            return (current_datetime - timedelta(days=1)).date()
        else:
            return current_datetime.date()