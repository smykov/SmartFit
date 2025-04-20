import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
import datetime
import pytz
from typing import Dict, Any, List, Optional

from app.db.firebase import FirebaseClient


class FirebaseInMemoryStorage:
    """In-memory реализация хранилища данных для тестирования."""

    def __init__(self):
        self.collections = {
            "users": {},
            "diet_plans": {},
            "shopping_lists": {},
            "weight_entries": {},
            "water_entries": {},
            "messages": {},
            "reminders": {},
            "compliance": {}
        }


@pytest.fixture
def firebase_storage():
    """Создает in-memory хранилище для тестов."""
    return FirebaseInMemoryStorage()


@pytest.fixture
def firebase_mock(firebase_storage):
    """Возвращает мок для FirebaseClient с in-memory хранилищем."""
    mock = MagicMock(spec=FirebaseClient)
    storage = firebase_storage

    # Методы для работы с документами
    async def get_document(collection, document_id):
        if collection in storage.collections and document_id in storage.collections[collection]:
            return storage.collections[collection][document_id]
        return None

    async def add_document(collection, data):
        if collection not in storage.collections:
            storage.collections[collection] = {}

        document_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now(pytz.UTC).isoformat()

        # Добавляем метаданные
        doc_data = {
            **data,
            "id": document_id,
            "created_at": data.get("created_at", timestamp),
            "updated_at": timestamp
        }

        storage.collections[collection][document_id] = doc_data
        return document_id

    async def set_document(collection, document_id, data, merge=True):
        if collection not in storage.collections:
            storage.collections[collection] = {}

        if merge and document_id in storage.collections[collection]:
            storage.collections[collection][document_id].update(data)
            storage.collections[collection][document_id]["updated_at"] = datetime.datetime.now(pytz.UTC).isoformat()
        else:
            timestamp = datetime.datetime.now(pytz.UTC).isoformat()
            storage.collections[collection][document_id] = {
                **data,
                "id": document_id,
                "created_at": data.get("created_at", timestamp),
                "updated_at": timestamp
            }

        return True

    async def update_document(collection, document_id, data):
        if collection in storage.collections and document_id in storage.collections[collection]:
            storage.collections[collection][document_id].update(data)
            storage.collections[collection][document_id]["updated_at"] = datetime.datetime.now(pytz.UTC).isoformat()
            return True
        return False

    async def delete_document(collection, document_id):
        if collection in storage.collections and document_id in storage.collections[collection]:
            del storage.collections[collection][document_id]
            return True
        return False

    async def query_documents(collection, field, operator, value):
        result = []
        if collection in storage.collections:
            for doc_id, doc_data in storage.collections[collection].items():
                if field in doc_data:
                    if operator == "==":
                        if doc_data[field] == value:
                            result.append(doc_data)
                    elif operator == ">":
                        if doc_data[field] > value:
                            result.append(doc_data)
                    elif operator == "<":
                        if doc_data[field] < value:
                            result.append(doc_data)
                    elif operator == ">=":
                        if doc_data[field] >= value:
                            result.append(doc_data)
                    elif operator == "<=":
                        if doc_data[field] <= value:
                            result.append(doc_data)
                    # Другие операторы по необходимости
        return result

    async def get_all_documents(collection):
        if collection in storage.collections:
            return list(storage.collections[collection].values())
        return []

    # Привязываем методы к моку
    mock.get_document = AsyncMock(side_effect=get_document)
    mock.add_document = AsyncMock(side_effect=add_document)
    mock.set_document = AsyncMock(side_effect=set_document)
    mock.update_document = AsyncMock(side_effect=update_document)
    mock.delete_document = AsyncMock(side_effect=delete_document)
    mock.query_documents = AsyncMock(side_effect=query_documents)
    mock.get_all_documents = AsyncMock(side_effect=get_all_documents)

    return mock


@pytest.fixture
def firebase_repositories(firebase_mock):
    """Создает набор репозиториев, использующих мок FirebaseClient."""
    from app.db.repositories.user_repository import FirebaseUserRepository
    from app.db.repositories.diet_plan_repository import FirebaseDietPlanRepository
    from app.db.repositories.product_repository import FirebaseProductRepository
    from app.db.repositories.shopping_list_repository import FirebaseShoppingListRepository
    from app.db.repositories.message_repository import FirebaseMessageRepository
    from app.db.repositories.reminder_repository import FirebaseReminderRepository
    from app.db.repositories.weight_entry_repository import FirebaseWeightEntryRepository
    from app.db.repositories.water_entry_repository import FirebaseWaterEntryRepository
    from app.db.repositories.compliance_repository import FirebaseComplianceRepository

    return {
        "user_repository": FirebaseUserRepository(firebase_mock),
        "diet_plan_repository": FirebaseDietPlanRepository(firebase_mock),
        "product_repository": FirebaseProductRepository(firebase_mock),
        "shopping_list_repository": FirebaseShoppingListRepository(firebase_mock),
        "message_repository": FirebaseMessageRepository(firebase_mock),
        "reminder_repository": FirebaseReminderRepository(firebase_mock),
        "weight_entry_repository": FirebaseWeightEntryRepository(firebase_mock),
        "water_entry_repository": FirebaseWaterEntryRepository(firebase_mock),
        "compliance_repository": FirebaseComplianceRepository(firebase_mock)
    }