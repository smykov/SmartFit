# app/services/messaging/command_extraction/cached_command_extractor.py
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import logging

from app.models.command import CommandExtractionResult
from app.services.messaging.command_extraction.command_extraction_interface import ICommandExtractor


class CachedCommandExtractor(ICommandExtractor):
    """Декоратор для кэширования результатов экстракции команд"""

    def __init__(self,
                 command_extractor: ICommandExtractor,
                 cache_ttl_minutes: int = 30,
                 min_confidence_for_cache: float = 0.7):
        """
        Инициализация кэширующего экстрактора

        Args:
            command_extractor: Базовый экстрактор команд
            cache_ttl_minutes: Время жизни кэша в минутах
            min_confidence_for_cache: Минимальная уверенность для кэширования
        """
        self.command_extractor = command_extractor
        self.cache: Dict[str, Tuple[CommandExtractionResult, datetime]] = {}
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.min_confidence = min_confidence_for_cache
        self.logger = logging.getLogger(self.__class__.__name__)

    async def extract_commands(self, message: str, user_id: str,
                               context: Dict[str, Any] = None) -> CommandExtractionResult:
        """
        Извлекает команды из текстового сообщения, используя кэш

        Args:
            message: Текст сообщения
            user_id: ID пользователя
            context: Контекст пользователя и разговора

        Returns:
            CommandExtractionResult: Результат извлечения
        """
        # Создаем хеш запроса
        request_hash = self._get_request_hash(message, user_id, context)

        # Проверяем кэш
        if request_hash in self.cache:
            cached_result, cache_time = self.cache[request_hash]

            # Проверяем не устарел ли кэш
            if datetime.now() - cache_time < self.cache_ttl:
                self.logger.info(f"Cache hit for request hash: {request_hash[:8]}...")
                return cached_result

        # Если кэш отсутствует или устарел, выполняем запрос
        result = await self.command_extractor.extract_commands(message, user_id, context)

        # Кэшируем только если уверенность высокая
        if not result.fallback_to_ai and all(cmd.confidence >= self.min_confidence for cmd in result.commands):
            self.cache[request_hash] = (result, datetime.now())
            self.logger.info(f"Cached result for request hash: {request_hash[:8]}...")

            # Очистка старых записей кэша
            self._clean_cache()

        return result

    def _get_request_hash(self, message: str, user_id: str, context: Optional[Dict[str, Any]]) -> str:
        """
        Создает хеш запроса

        Args:
            message: Текст сообщения
            user_id: ID пользователя
            context: Контекст пользователя и разговора

        Returns:
            str: Хеш запроса
        """
        # Нормализуем сообщение (удаляем лишние пробелы, приводим к нижнему регистру)
        message_normalized = message.lower().strip()

        # Извлекаем только значимые части контекста
        context_hash = ""
        if context:
            relevant_keys = ["last_action", "diet_plan_shown", "diet_plan_id"]
            relevant_context = {k: context.get(k) for k in relevant_keys if k in context}
            context_hash = str(relevant_context)

        # Создаем хеш из сообщения, ID пользователя и контекста
        return hashlib.md5(f"{message_normalized}|{user_id}|{context_hash}".encode()).hexdigest()

    def _clean_cache(self):
        """Очищает устаревшие записи кэша"""
        now = datetime.now()
        expired_keys = [k for k, (_, t) in self.cache.items() if now - t > self.cache_ttl]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            self.logger.info(f"Cleaned {len(expired_keys)} expired cache entries")