# app/services/messaging/command_extraction/parsers/command_parser_registry.py
from typing import Dict, List, Optional
from app.models.command import Command
from app.services.messaging.command_extraction.parsers.base_command_parser import BaseCommandParser
import logging


class CommandParserRegistry:
    """
    Реестр парсеров команд.
    Следует принципам SOLID: SRP, OCP (можно добавлять новые парсеры без изменения существующего кода)
    """

    def __init__(self):
        """Инициализация реестра"""
        self._parsers: List[BaseCommandParser] = []
        self.logger = logging.getLogger(self.__class__.__name__)

    def register_parser(self, parser: BaseCommandParser) -> None:
        """
        Регистрирует новый парсер команд

        Args:
            parser: Парсер команд
        """
        if not isinstance(parser, BaseCommandParser):
            raise TypeError("Parser must implement BaseCommandParser interface")

        self._parsers.append(parser)
        self.logger.debug(f"Registered parser for command type: {parser.get_command_type()}")

    def parse_message(self, message: str, context: Dict = None) -> List[Command]:
        """
        Пытается распарсить сообщение всеми зарегистрированными парсерами

        Args:
            message: Текст сообщения
            context: Контекст пользователя

        Returns:
            List[Command]: Список найденных команд (обычно 0-1 команда)
        """
        commands = []

        for parser in self._parsers:
            try:
                command = parser.parse(message, context)
                if command:
                    commands.append(command)
                    self.logger.debug(f"Command {command.command_type} parsed by {parser.__class__.__name__}")
                    # Возвращаем первую найденную команду (приоритет по порядку регистрации)
                    break

            except Exception as e:
                self.logger.error(f"Error in parser {parser.__class__.__name__}: {str(e)}")
                continue

        return commands

    def get_registered_parsers(self) -> List[BaseCommandParser]:
        """Возвращает список зарегистрированных парсеров"""
        return self._parsers.copy()

