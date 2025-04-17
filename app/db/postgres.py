# app/db/postgres.py
import logging
from typing import Dict, Any, List, Optional

import asyncpg

from config import settings

logger = logging.getLogger(__name__)


class PostgresClient:
    """Клиент для работы с PostgreSQL"""

    _instance = None

    def __new__(cls):
        """Singleton паттерн для создания единственного экземпляра клиента"""
        if cls._instance is None:
            cls._instance = super(PostgresClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Инициализация клиента PostgreSQL"""
        if self._initialized:
            return

        self.pool = None
        self._initialized = True
        self.logger = logging.getLogger(self.__class__.__name__)

    async def initialize(self):
        """Асинхронная инициализация пула подключений"""
        try:
            self.pool = await asyncpg.create_pool(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DATABASE,
                min_size=settings.POSTGRES_MIN_CONN or 5,
                max_size=settings.POSTGRES_MAX_CONN or 20
            )
            self.logger.info("PostgreSQL успешно инициализирован")
        except Exception as e:
            self.logger.error(f"Ошибка инициализации PostgreSQL: {str(e)}")
            raise e

    async def close(self):
        """Закрытие пула подключений"""
        if self.pool:
            await self.pool.close()

    async def execute(self, query: str, *args, timeout: float = None) -> str:
        """Выполнение SQL запроса, возвращающего одно значение"""
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args, timeout=timeout)

    async def fetch(self, query: str, *args, timeout: float = None) -> List[Dict[str, Any]]:
        """Получение списка записей из базы данных"""
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(query, *args, timeout=timeout)
            return [dict(row) for row in rows]

    async def fetchrow(self, query: str, *args, timeout: float = None) -> Optional[Dict[str, Any]]:
        """Получение одной записи из базы данных"""
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(query, *args, timeout=timeout)
            return dict(row) if row else None

    async def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Получение документа из таблицы по ID (имитация Firestore)"""
        try:
            query = f"""
                SELECT * FROM {collection} 
                WHERE id = $1
            """
            document = await self.fetchrow(query, document_id)
            return document
        except Exception as e:
            self.logger.error(f"Ошибка при получении документа {document_id} из {collection}: {str(e)}")
            return None

    async def add_document(self, collection: str, data: Dict[str, Any]) -> Optional[str]:
        """Добавление нового документа в таблицу с автогенерируемым ID"""
        try:
            # Получаем колонки и значения
            columns = list(data.keys())
            values = list(data.values())
            placeholders = [f"${i + 1}" for i in range(len(values))]

            # Формируем SQL запрос с RETURNING id
            query = f"""
                INSERT INTO {collection} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING id
            """

            result = await self.fetchrow(query, *values)
            document_id = result.get('id') if result else None

            return document_id
        except Exception as e:
            self.logger.error(f"Ошибка при добавлении документа в {collection}: {str(e)}")
            return None

    async def set_document(self, collection: str, document_id: str, data: Dict[str, Any], merge: bool = True) -> bool:
        """Создание или обновление документа с указанным ID"""
        try:
            if merge:
                # При объединении обновляем только переданные поля
                updates = []
                values = []

                for i, (key, value) in enumerate(data.items()):
                    if key != 'id':  # Исключаем поле id из обновления
                        updates.append(f"{key} = ${i + 2}")
                        values.append(value)

                # Если есть поля для обновления
                if updates:
                    query = f"""
                        UPDATE {collection}
                        SET {', '.join(updates)}
                        WHERE id = $1
                    """

                    # Проверяем, существует ли запись
                    check_query = f"SELECT EXISTS(SELECT 1 FROM {collection} WHERE id = $1)"
                    exists = await self.fetchrow(check_query, document_id)

                    if exists and exists.get('exists'):
                        # Обновляем существующую запись
                        await self.execute(query, document_id, *values)
                    else:
                        # Создаем новую запись
                        full_data = data.copy()
                        full_data['id'] = document_id
                        await self.add_document(collection, full_data)

                    return True
            else:
                # Удаляем и создаем заново (replace)
                await self.delete_document(collection, document_id)

                # Создаем новую запись
                full_data = data.copy()
                full_data['id'] = document_id
                await self.add_document(collection, full_data)

                return True

            return False
        except Exception as e:
            self.logger.error(f"Ошибка при установке документа {document_id} в {collection}: {str(e)}")
            return False

    async def update_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Обновление существующего документа"""
        try:
            updates = []
            values = []

            for i, (key, value) in enumerate(data.items()):
                if key != 'id':  # Исключаем поле id из обновления
                    updates.append(f"{key} = ${i + 2}")
                    values.append(value)

            if not updates:
                return True  # Нет данных для обновления

            query = f"""
                UPDATE {collection}
                SET {', '.join(updates)}
                WHERE id = $1
            """

            await self.execute(query, document_id, *values)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении документа {document_id} в {collection}: {str(e)}")
            return False

    async def delete_document(self, collection: str, document_id: str) -> bool:
        """Удаление документа"""
        try:
            query = f"""
                DELETE FROM {collection}
                WHERE id = $1
            """

            await self.execute(query, document_id)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка при удалении документа {document_id} из {collection}: {str(e)}")
            return False

    async def query_documents(self, collection: str, field: str, operator: str, value: Any) -> List[Dict[str, Any]]:
        """Запрос документов по условию"""
        try:
            # Преобразуем оператор Firestore в оператор SQL
            operator_map = {
                "==": "=",
                "<": "<",
                "<=": "<=",
                ">": ">",
                ">=": ">=",
                "!=": "!="
            }

            sql_operator = operator_map.get(operator, "=")

            query = f"""
                SELECT * FROM {collection}
                WHERE {field} {sql_operator} $1
            """

            return await self.fetch(query, value)
        except Exception as e:
            self.logger.error(f"Ошибка при запросе документов из {collection}: {str(e)}")
            return []

    async def get_all_documents(self, collection: str) -> List[Dict[str, Any]]:
        """Получение всех документов из коллекции"""
        try:
            query = f"SELECT * FROM {collection}"
            return await self.fetch(query)
        except Exception as e:
            self.logger.error(f"Ошибка при получении всех документов из {collection}: {str(e)}")
            return []