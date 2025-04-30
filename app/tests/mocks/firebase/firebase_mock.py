# tests/mocks/firebase/firebase_mock.py
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime


class FirebaseMock:
    """Мок для клиента Firebase с имитацией in-memory хранилища."""

    def __init__(self):
        """Инициализация in-memory хранилища."""
        self.db = {
            "users": {},
            "diet_plans": {},
            "shopping_lists": {},
            "weight_entries": {},
            "water_entries": {},
            "messages": {},
            "reminders": {},
            "compliance": {}
        }

    async def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Получение документа из коллекции."""
        if collection in self.db and document_id in self.db[collection]:
            return self.db[collection][document_id]
        return None

    async def add_document(self, collection: str, data: Dict[str, Any]) -> str:
        """Добавление документа в коллекцию."""
        if collection not in self.db:
            self.db[collection] = {}

        document_id = str(uuid.uuid4())
        self.db[collection][document_id] = {"id": document_id, **data}
        return document_id

    async def set_document(self, collection: str, document_id: str, data: Dict[str, Any], merge: bool = True) -> bool:
        """Создание или обновление документа с указанным ID."""
        if collection not in self.db:
            self.db[collection] = {}

        if merge and document_id in self.db[collection]:
            # Обновляем существующий документ
            self.db[collection][document_id].update(data)
        else:
            # Создаем новый документ
            self.db[collection][document_id] = {"id": document_id, **data}

        return True

    async def update_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Обновление существующего документа."""
        if collection in self.db and document_id in self.db[collection]:
            self.db[collection][document_id].update(data)
            return True
        return False

    async def delete_document(self, collection: str, document_id: str) -> bool:
        """Удаление документа."""
        if collection in self.db and document_id in self.db[collection]:
            del self.db[collection][document_id]
            return True
        return False

    async def query_documents(self, collection: str, field: str, operator: str, value: Any) -> List[Dict[str, Any]]:
        """Запрос документов по условию."""
        results = []

        if collection not in self.db:
            return results

        for doc_id, doc_data in self.db[collection].items():
            if field in doc_data:
                if operator == "==":
                    if doc_data[field] == value:
                        results.append(doc_data)
                elif operator == ">":
                    if doc_data[field] > value:
                        results.append(doc_data)
                elif operator == "<":
                    if doc_data[field] < value:
                        results.append(doc_data)
                elif operator == ">=":
                    if doc_data[field] >= value:
                        results.append(doc_data)
                elif operator == "<=":
                    if doc_data[field] <= value:
                        results.append(doc_data)
                # Другие операторы по необходимости

        return results

    async def get_all_documents(self, collection: str) -> List[Dict[str, Any]]:
        """Получение всех документов из коллекции."""
        if collection in self.db:
            return list(self.db[collection].values())
        return []