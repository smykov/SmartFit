# app/services/messaging/command_extraction/parsers/simple_command_parser.py
import re
from typing import Optional, Dict, Any
from app.models.command import Command, CommandSource
from app.services.messaging.command_extraction.parsers.base_command_parser import BaseCommandParser


class SimpleCommandParser(BaseCommandParser):
    """
    Парсер для простых команд (вес, вода, помощь, статистика).
    Следует принципу SRP - только простые паттерны.
    """

    def __init__(self):
        """Инициализация парсера простых команд"""
        self.patterns = {
            "weight": re.compile(r'^вес\s+(\d+[.,]?\d*)$', re.IGNORECASE),
            "water": re.compile(r'^вода\s+(\d+[.,]?\d*)$', re.IGNORECASE),
            "help": re.compile(r'^(помощь|справка|команды|help)$', re.IGNORECASE),
            "shopping_list": re.compile(r'^список покупок$', re.IGNORECASE),
            "stats": re.compile(r'^(статистика|прогресс)$', re.IGNORECASE),
        }

    def parse(self, message: str, context: Dict[str, Any] = None) -> Optional[Command]:
        """Парсит простые команды"""
        if not message:
            return None

        message = message.strip()

        for cmd_type, pattern in self.patterns.items():
            match = pattern.match(message)
            if match:
                # Создаем параметры на основе групп захвата
                params = {}
                if match.groups():
                    params["params"] = match.groups()

                return Command(
                    command_type=cmd_type,
                    params=params,
                    priority=0,
                    source=CommandSource.PATTERN_MATCH,
                    confidence=0.95
                )

        return None

    def get_command_type(self) -> str:
        """Возвращает тип команды (множественный)"""
        return "simple_commands"
