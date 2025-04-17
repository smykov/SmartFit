# app/db/repositories/postgres/base_repository.py
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, TypeVar, Generic

from app.db.postgres import PostgresClient

T = TypeVar('T')


class PostgresBaseRepository(Generic[T]):
    """
    Базовый класс для всех PostgreSQL репозиториев
    """

    def __init__(self, postgres_client: PostgresClient, collection: str):
        """
        Инициализация базового репозитория

        Args:
            postgres_client: Клиент PostgreSQL
            collection: Название таблицы в базе данных
        """
        self.client = postgres_client
        self.collection = collection

    def _prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Подготовка данных для сохранения в базе данных

        Args:
            data: Исходные данные

        Returns:
            Dict[str, Any]: Подготовленные данные
        """
        prepared_data = data.copy()

        # Генерируем UUID, если не предоставлен
        if "id" not in prepared_data:
            prepared_data["id"] = str(uuid.uuid4())

        # Преобразуем списки и словари в JSON
        for key, value in prepared_data.items():
            if isinstance(value, (dict, list)):
                prepared_data[key] = json.dumps(value)

        # Добавляем временные метки, если их нет
        now = datetime.now().isoformat()
        if "created_at" not in prepared_data:
            prepared_data["created_at"] = now
        if "updated_at" not in prepared_data:
            prepared_data["updated_at"] = now

        return prepared_data

    def _parse_data(self, data: Dict[str, Any], json_fields: List[str]) -> Dict[str, Any]:
        """
        Парсинг данных из базы данных

        Args:
            data: Данные из базы данных
            json_fields: Список полей, которые нужно преобразовать из JSON

        Returns:
            Dict[str, Any]: Преобразованные данные
        """
        if not data:
            return data

        parsed_data = data.copy()

        # Преобразуем JSON строки обратно в структуры данных
        for key in json_fields:
            if key in parsed_data and parsed_data[key]:
                try:
                    parsed_data[key] = json.loads(parsed_data[key]) if isinstance(parsed_data[key], str) else \
                    parsed_data[key]
                except (json.JSONDecodeError, TypeError):
                    if isinstance(parsed_data[key], str) and parsed_data[key].strip() in ('[]', '{}', ''):
                        parsed_data[key] = [] if parsed_data[key].strip() == '[]' else {}
                    else:
                        parsed_data[key] = parsed_data[key]

        return parsed_data