# app/services/messaging/command_extraction/logging_command_extractor.py
import logging
import time
from typing import Dict, Any, Optional

from app.models.command import CommandExtractionResult
from app.services.messaging.command_extraction.command_extraction_interface import ICommandExtractor


class LoggingCommandExtractor(ICommandExtractor):
    """Декоратор для логирования вызовов экстрактора команд"""

    def __init__(self, command_extractor: ICommandExtractor):
        """
        Инициализация логирующего декоратора

        Args:
            command_extractor: Базовый экстрактор команд
        """
        self.command_extractor = command_extractor
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_commands(self, message: str, user_id: str,
                               context: Dict[str, Any] = None) -> CommandExtractionResult:
        """
        Логирует и вызывает базовый экстрактор команд

        Args:
            message: Текст сообщения
            user_id: ID пользователя
            context: Контекст пользователя и разговора

        Returns:
            CommandExtractionResult: Результат извлечения
        """
        start_time = time.time()

        # Логируем запрос
        self.logger.info(f"Command extraction started for user {user_id}: '{message[:50]}...' " if len(
            message) > 50 else f"'{message}'")

        try:
            # Вызываем базовый экстрактор
            result = await self.command_extractor.extract_commands(message, user_id, context)

            # Вычисляем время выполнения
            execution_time = time.time() - start_time

            # Логируем результат
            commands_info = ", ".join(
                [cmd.command_type for cmd in result.commands]) if result.commands else "No commands"
            self.logger.info(f"Command extraction completed in {execution_time:.3f}s for user {user_id}. "
                             f"Commands: [{commands_info}], Fallback: {result.fallback_to_ai}, "
                             f"Source: {result.source}, Execution required: {result.execution_required}")

            return result

        except Exception as e:
            # Вычисляем время до возникновения ошибки
            execution_time = time.time() - start_time

            # Логируем ошибку
            self.logger.error(f"Command extraction error in {execution_time:.3f}s for user {user_id}: {str(e)}",
                              exc_info=True)

            # Пробрасываем исключение дальше
            raise
