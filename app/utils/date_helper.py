# app/utils/date_helper.py
from datetime import datetime, date, timedelta
from typing import Optional
import pytz


class DateHelper:
    """Утилита для работы с датами с учетом часовых поясов пользователей"""

    # Граница "нового дня" для трекинга (6:00 утра)
    TRACKING_DAY_BOUNDARY_HOUR = 6
    # Словарь для преобразования названия дня недели в число (0 - понедельник, 6 - воскресенье)
    WEEKDAY_MAPPING = {
        0: "monday",
        1: "tuesday",
        2: "wednesday",
        3: "thursday",
        4: "friday",
        5: "saturday",
        6: "sunday"
    }

    @staticmethod
    def get_user_timezone(user_timezone: Optional[str] = None) -> pytz.BaseTzInfo:
        """
        Получает часовой пояс пользователя

        Args:
            user_timezone: Часовой пояс пользователя (например, 'Europe/Moscow')

        Returns:
            pytz.BaseTzInfo: Объект часового пояса
        """
        if user_timezone:
            try:
                return pytz.timezone(user_timezone)
            except pytz.UnknownTimeZoneError:
                # Если часовой пояс неизвестен, используем системный
                pass

        # Fallback на системный часовой пояс из настроек
        from config import settings
        return pytz.timezone(settings.TIMEZONE)

    @staticmethod
    def get_current_date(user_timezone: Optional[str] = None) -> date:
        """
        Получает текущую дату в часовом поясе пользователя

        Args:
            user_timezone: Часовой пояс пользователя

        Returns:
            date: Текущая дата
        """
        return DateHelper.get_current_datetime(user_timezone).date()

    @staticmethod
    def get_current_datetime(user_timezone: Optional[str] = None) -> datetime:
        """
        Получает текущее время в часовом поясе пользователя

        Args:
            user_timezone: Часовой пояс пользователя

        Returns:
            datetime: Текущее время с часовым поясом
        """
        tz = DateHelper.get_user_timezone(user_timezone)
        return datetime.now(tz)

    @staticmethod
    def get_day_of_week(target_date: date) -> str:
        """
        Получает день недели для указанной даты

        Args:
            target_date: Дата

        Returns:
            str: День недели ('monday', 'tuesday', etc.)
        """
        weekday = target_date.weekday()
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        return days[weekday]

    @staticmethod
    def get_nearest_date_for_weekday(weekday: str, user_timezone: Optional[str] = None) -> date:
        """
        Получает ближайшую дату для указанного дня недели

        Args:
            weekday: День недели ('monday', 'tuesday', etc.)
            user_timezone: Часовой пояс пользователя

        Returns:
            date: Ближайшая дата для этого дня недели
        """
        current_date = DateHelper.get_current_date(user_timezone)

        weekday_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }

        target_weekday = weekday_map.get(weekday.lower())
        if target_weekday is None:
            return current_date

        current_weekday = current_date.weekday()
        days_diff = target_weekday - current_weekday

        # Если это сегодня, возвращаем сегодня
        if days_diff == 0:
            return current_date

        # Если день уже прошел на этой неделе, берем следующую неделю
        if days_diff < 0:
            days_diff += 7

        return current_date + timedelta(days=days_diff)

    @staticmethod
    def format_date(target_date: date, format_string: str = "%d.%m.%Y") -> str:
        """
        Форматирует дату в строку

        Args:
            target_date: Дата для форматирования
            format_string: Формат даты

        Returns:
            str: Отформатированная дата
        """
        return target_date.strftime(format_string)

    @staticmethod
    def parse_date_string(date_str: str) -> date:
        """
        Парсит строку даты в объект date

        Args:
            date_str: Строка даты в формате YYYY-MM-DD

        Returns:
            date: Объект даты
        """
        return datetime.strptime(date_str, "%Y-%m-%d").date()

    @staticmethod
    def get_tracking_date(user_timezone: Optional[str] = None) -> date:
        """
        Получает "трекинговую дату" - с учетом того, что до 6 утра
        записи относятся к предыдущему дню

        Args:
            user_timezone: Часовой пояс пользователя

        Returns:
            date: Дата для трекинга
        """
        current_dt = DateHelper.get_current_datetime(user_timezone)

        # Если время до 6 утра, считаем это предыдущим днем
        if current_dt.hour < DateHelper.TRACKING_DAY_BOUNDARY_HOUR:
            return (current_dt - timedelta(days=1)).date()

        return current_dt.date()

    @staticmethod
    def get_day_name_localized(target_date: date, lang: str = 'ru') -> str:
        """
        Получает локализованное название дня недели

        Args:
            target_date: Дата
            lang: Код языка

        Returns:
            str: Локализованное название дня
        """
        # TODO переделать на локализацию
        day_names = {
            'ru': ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"],
            'en': ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        }

        weekday = target_date.weekday()
        return day_names.get(lang, day_names['en'])[weekday]

    @staticmethod
    def get_context_for_llm(user_timezone: Optional[str] = None) -> dict:
        """
        Создает контекст с датой и временем для LLM

        Args:
            user_timezone: Часовой пояс пользователя

        Returns:
            dict: Контекст с временной информацией
        """
        current_dt = DateHelper.get_current_datetime(user_timezone)
        current_date = current_dt.date()
        tracking_date = DateHelper.get_tracking_date(user_timezone)

        return {
            "current_datetime": current_dt.isoformat(),
            "current_date": current_date.isoformat(),
            "current_day_of_week": DateHelper.get_day_of_week(current_date),
            "tracking_date": tracking_date.isoformat(),
            "tracking_day_of_week": DateHelper.get_day_of_week(tracking_date),
            "current_time": current_dt.strftime("%H:%M"),
            "timezone": str(current_dt.tzinfo)
        }
