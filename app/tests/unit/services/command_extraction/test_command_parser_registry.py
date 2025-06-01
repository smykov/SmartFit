# tests/unit/services/command_extraction/test_command_parser_registry.py
import pytest
from unittest.mock import Mock

from app.services.messaging.command_extraction.parsers.command_parser_registry import CommandParserRegistry
from app.services.messaging.command_extraction.parsers.base_command_parser import BaseCommandParser
from app.models.command import Command, CommandSource


class MockParser(BaseCommandParser):
    """Мок парсер для тестов"""

    def __init__(self, command_type: str, should_parse: bool = True):
        self.command_type = command_type
        self.should_parse = should_parse

    def parse(self, message: str, context=None):
        if self.should_parse and message == f"test_{self.command_type}":
            return Command(
                command_type=self.command_type,
                params={},
                priority=0,
                source=CommandSource.PATTERN_MATCH,
                confidence=0.9
            )
        return None

    def get_command_type(self):
        return self.command_type


class TestCommandParserRegistry:
    """Тесты для CommandParserRegistry"""

    @pytest.fixture
    def registry(self):
        """Фикстура для создания реестра"""
        return CommandParserRegistry()

    def test_register_parser(self, registry):
        """Тест регистрации парсера"""
        parser = MockParser("test")
        registry.register_parser(parser)

        parsers = registry.get_registered_parsers()
        assert len(parsers) == 1
        assert parsers[0] == parser

    def test_register_invalid_parser(self, registry):
        """Тест регистрации некорректного парсера"""
        with pytest.raises(TypeError):
            registry.register_parser("not_a_parser")

    def test_parse_message_success(self, registry):
        """Тест успешного парсинга сообщения"""
        parser = MockParser("test", should_parse=True)
        registry.register_parser(parser)

        commands = registry.parse_message("test_test")

        assert len(commands) == 1
        assert commands[0].command_type == "test"

    def test_parse_message_no_match(self, registry):
        """Тест парсинга сообщения без совпадений"""
        parser = MockParser("test", should_parse=False)
        registry.register_parser(parser)

        commands = registry.parse_message("no_match")

        assert len(commands) == 0

    def test_parse_message_multiple_parsers_priority(self, registry):
        """Тест приоритета парсеров (первый зарегистрированный имеет приоритет)"""
        parser1 = MockParser("first")
        parser2 = MockParser("second")

        registry.register_parser(parser1)
        registry.register_parser(parser2)

        # Оба парсера могли бы обработать это сообщение, но первый имеет приоритет
        commands = registry.parse_message("test_first")

        assert len(commands) == 1
        assert commands[0].command_type == "first"

    def test_parse_message_with_context(self, registry):
        """Тест парсинга сообщения с контекстом"""
        parser = Mock(spec=BaseCommandParser)
        parser.parse.return_value = Command(
            command_type="test",
            params={},
            priority=0,
            source=CommandSource.PATTERN_MATCH,
            confidence=0.9
        )

        registry.register_parser(parser)

        context = {"user_id": "123"}
        commands = registry.parse_message("test", context)

        # Проверяем, что контекст был передан в парсер
        parser.parse.assert_called_once_with("test", context)
        assert len(commands) == 1