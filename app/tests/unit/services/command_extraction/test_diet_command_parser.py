# tests/unit/services/command_extraction/test_diet_command_parser.py
import pytest
from unittest.mock import Mock, patch
from datetime import date

from app.services.messaging.command_extraction.parsers.diet_command_parser import DietCommandParser
from app.models.command import Command, CommandSource


class TestDietCommandParser:
    """Тесты для DietCommandParser"""

    @pytest.fixture
    def mock_localization_service(self):
        """Мок сервиса локализации"""
        mock = Mock()
        return mock

    @pytest.fixture
    def diet_parser(self, mock_localization_service):
        """Фикстура для создания DietCommandParser"""
        return DietCommandParser(mock_localization_service)

    @pytest.fixture
    def context(self):
        """Контекст пользователя для тестов"""
        return {
            'language': 'ru',
            'timezone': 'Europe/Moscow'
        }

    def test_parse_simple_diet_request(self, diet_parser, context):
        """Тест парсинга простого запроса 'план'"""
        result = diet_parser.parse('план', context)

        assert result is not None
        assert result.command_type == 'show_diet_plan'
        assert result.params == {}
        assert result.confidence == 0.95

    def test_parse_simple_diet_request_variations(self, diet_parser, context):
        """Тест парсинга различных вариантов простого запроса"""
        variations = ['план', 'диета', 'меню', 'план питания', 'рацион']

        for variation in variations:
            result = diet_parser.parse(variation, context)
            assert result is not None
            assert result.command_type == 'show_diet_plan'

    def test_parse_full_diet_request(self, diet_parser, context):
        """Тест парсинга запроса полного плана"""
        variations = ['полный план', 'план на неделю', 'недельный план']

        for variation in variations:
            result = diet_parser.parse(variation, context)
            assert result is not None
            assert result.command_type == 'show_diet_plan'
            assert result.params.get('full') is True

    @patch('app.services.messaging.command_extraction.parsers.date_parser.DateParser')
    def test_parse_diet_with_weekday(self, mock_date_parser_class, diet_parser, context):
        """Тест парсинга 'план на понедельник'"""
        # Настраиваем мок DateParser
        mock_date_parser = mock_date_parser_class.return_value
        mock_date_parser.parse_relative_date.return_value = None
        mock_date_parser.parse_weekday.return_value = (date(2024, 5, 20), 'monday')
        mock_date_parser.parse_absolute_date.return_value = None

        result = diet_parser.parse('план на понедельник', context)

        assert result is not None
        assert result.command_type == 'show_diet_plan'
        assert result.params.get('day') == 'monday'

    @patch('app.services.messaging.command_extraction.parsers.date_parser.DateParser')
    def test_parse_diet_with_relative_date(self, mock_date_parser_class, diet_parser, context):
        """Тест парсинга 'план на завтра'"""
        # Настраиваем мок DateParser
        mock_date_parser = mock_date_parser_class.return_value
        mock_date_parser.parse_relative_date.return_value = date(2025, 5, 16)

        result = diet_parser.parse('план на завтра', context)

        assert result is not None
        assert result.command_type == 'show_diet_plan'
        assert result.params.get('day') == '2025-05-16'

    @patch('app.services.messaging.command_extraction.parsers.date_parser.DateParser')
    def test_parse_diet_with_absolute_date(self, mock_date_parser_class, diet_parser, context):
        """Тест парсинга 'план на 28 мая'"""
        # Настраиваем мок DateParser
        mock_date_parser = mock_date_parser_class.return_value
        mock_date_parser.parse_relative_date.return_value = None
        mock_date_parser.parse_weekday.return_value = None
        mock_date_parser.parse_absolute_date.return_value = date(2025, 5, 28)

        result = diet_parser.parse('план на 28 мая', context)

        assert result is not None
        assert result.command_type == 'show_diet_plan'
        assert result.params.get('day') == '2025-05-28'

    def test_parse_invalid_message(self, diet_parser, context):
        """Тест парсинга невалидного сообщения"""
        result = diet_parser.parse('привет как дела', context)
        assert result is None

    def test_parse_empty_message(self, diet_parser, context):
        """Тест парсинга пустого сообщения"""
        result = diet_parser.parse('', context)
        assert result is None

    def test_parse_none_message(self, diet_parser, context):
        """Тест парсинга None сообщения"""
        result = diet_parser.parse(None, context)
        assert result is None

    @patch('app.services.messaging.command_extraction.parsers.date_parser.DateParser')
    def test_parse_diet_with_today(self, mock_date_parser_class, diet_parser, context):
        """Тест парсинга 'план на сегодня' (должен быть эквивалентен 'план')"""
        # Настраиваем мок DateParser
        mock_date_parser = mock_date_parser_class.return_value
        mock_date_parser.parse_relative_date.return_value = date(2024, 5, 15)  # Сегодня

        result = diet_parser.parse('план на сегодня', context)

        assert result is not None
        assert result.command_type == 'show_diet_plan'
        assert result.params == {}  # Без параметров, как простой "план"

    @patch('app.services.messaging.command_extraction.parsers.date_parser.DateParser')
    def test_parse_with_date_error_fallback_to_llm(self, mock_date_parser_class, diet_parser, context):
        """Тест обработки ошибки парсинга даты - должен возвращать None для fallback на LLM"""
        from app.services.messaging.command_extraction.parsers.date_parser import DateParsingError

        # Настраиваем мок DateParser для выброса исключения
        mock_date_parser = mock_date_parser_class.return_value
        mock_date_parser.parse_relative_date.return_value = None
        mock_date_parser.parse_weekday.return_value = None
        mock_date_parser.parse_absolute_date.side_effect = DateParsingError("Некорректная дата")

        result = diet_parser.parse('план на 30 февраля', context)

        assert result is not None
        assert result.command_type == 'diet_error'
        assert result.params == {'error_message': 'В February 2025 года 28 дней, а указан 30 день'}

    def test_get_command_type(self, diet_parser):
        """Тест получения типа команды"""
        assert diet_parser.get_command_type() == 'diet'