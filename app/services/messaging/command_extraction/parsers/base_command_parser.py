# app/services/messaging/command_extraction/parsers/base_command_parser.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.models.command import Command


class BaseCommandParser(ABC):
    """
    Базовый класс для парсеров команд.
    Следует принципам SOLID: SRP, OCP
    """

    @abstractmethod
    def parse(self, message: str, context: Dict[str, Any] = None) -> Optional[Command]:
        """
        Парсит сообщение и возвращает команду если найдена

        Args:
            message: Текст сообщения
            context: Контекст пользователя

        Returns:
            Optional[Command]: Команда или None если не найдена
        """
        pass

    @abstractmethod
    def get_command_type(self) -> str:
        """Возвращает тип команды который обрабатывает этот парсер"""
        pass