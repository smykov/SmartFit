# tests/unit/services/command_extraction/test_date_parser.py
import pytest
from datetime import date, timedelta
from unittest.mock import patch

from app.services.messaging.command_extraction.parsers.date_parser import DateParser, DateParsingError


class TestDateParser:
    """Тесты для DateParser"""

    @pytest.fixture
    def date_parser(self):
        """Фикстура для создания DateParser"""
        with patch('app.utils.date_helper.DateHelper.get_tracking_date') as mock_date:
            mock_date.return_value = date(2024, 5, 15)  # Среда
            return DateParser(user_timezone='Europe/Moscow', language='ru')

    def test_parse_relative_date_today(self, date_parser):
        """Тест парсинга 'сегодня'"""
        result = date_parser.parse_relative_date('сегодня')
        assert result == date(2024, 5, 15)

    def test_parse_relative_date_tomorrow(self, date_parser):
        """Тест парсинга 'завтра'"""
        result = date_parser.parse_relative_date('завтра')
        assert result == date(2024, 5, 16)

    def test_parse_relative_date_yesterday(self, date_parser):
        """Тест парсинга 'вчера'"""
        result = date_parser.parse_relative_date('вчера')
        assert result == date(2024, 5, 14)

    def test_parse_relative_date_invalid(self, date_parser):
        """Тест парсинга неизвестного относительного термина"""
        result = date_parser.parse_relative_date('послепослезавтра')
        assert result is None

    def test_parse_weekday_monday(self, date_parser):
        """Тест парсинга дня недели 'понедельник'"""
        with patch('app.utils.date_helper.DateHelper.get_nearest_date_for_weekday') as mock_nearest:
            mock_nearest.return_value = date(2024, 5, 20)  # Следующий понедельник
            result = date_parser.parse_weekday('понедельник')
            assert result == (date(2024, 5, 20), 'monday')

    def test_parse_weekday_invalid(self, date_parser):
        """Тест парсинга неизвестного дня недели"""
        result = date_parser.parse_weekday('несуществующийдень')
        assert result is None

    def test_parse_absolute_date_day_month(self, date_parser):
        """Тест парсинга даты вида '28 мая'"""
        result = date_parser.parse_absolute_date('28 мая')
        assert result == date(2024, 5, 28)

    def test_parse_absolute_date_numeric(self, date_parser):
        """Тест парсинга даты вида '28.05'"""
        result = date_parser.parse_absolute_date('28.05')
        assert result == date(2024, 5, 28)

    def test_parse_absolute_date_invalid_day(self, date_parser):
        """Тест парсинга некорректной даты"""
        with pytest.raises(DateParsingError) as exc_info:
            date_parser.parse_absolute_date('30 февраля')
        assert "В February 2024 года 29 дней, а указан 30 день" in str(exc_info.value)

    def test_parse_absolute_date_invalid_month(self, date_parser):
        """Тест парсинга некорректного месяца"""
        with pytest.raises(DateParsingError) as exc_info:
            date_parser.parse_absolute_date('15.13')
        assert "Некорректный месяц: 13" in str(exc_info.value)
