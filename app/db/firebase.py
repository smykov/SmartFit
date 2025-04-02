import firebase_admin
from firebase_admin import credentials, firestore, auth
import logging
from typing import Dict, Any, List, Optional

from config import settings

logger = logging.getLogger(__name__)


class FirebaseClient:
    """Клиент для работы с Firebase (Firestore и Authentication)"""

    _instance = None

    def __new__(cls):
        """Singleton паттерн для создания единственного экземпляра клиента"""
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Инициализация клиента Firebase"""
        if self._initialized:
            return

        try:
            # Инициализация Firebase с помощью учетных данных из файла
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
            firebase_admin.initialize_app(cred, {
                'databaseURL': settings.FIREBASE_DATABASE_URL
            })

            # Получение экземпляра Firestore
            self.db = firestore.client()
            logger.info("Firebase Firestore успешно инициализирован")

            self._initialized = True
        except Exception as e:
            logger.error(f"Ошибка инициализации Firebase: {str(e)}")
            raise e

    # --- Методы для работы с Firestore (база данных) ---

    def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Получение документа из коллекции по ID"""
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                # ИСПРАВЛЕНИЕ: Добавляем ID в данные
                data["id"] = document_id
                return data
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении документа {document_id} из {collection}: {str(e)}")
            return None

    def add_document(self, collection: str, data: Dict[str, Any]) -> Optional[str]:
        """Добавление нового документа в коллекцию с автогенерируемым ID"""
        try:
            # ИСПРАВЛЕНИЕ: Обработка случая, если в данных уже есть 'id'
            if 'id' in data:
                temp_id = data['id']
                data_copy = data.copy()
                del data_copy['id']
                result = self.set_document(collection, temp_id, data_copy)
                return temp_id if result else None

            # Добавляем документ с автогенерируемым ID
            doc_ref = self.db.collection(collection).add(data)
            document_id = doc_ref[1].id

            # ИСПРАВЛЕНИЕ: После добавления, обновляем документ, добавляя id в данные
            self.update_document(collection, document_id, {"id": document_id})

            return document_id
        except Exception as e:
            logger.error(f"Ошибка при добавлении документа в {collection}: {str(e)}")
            return None

    def set_document(self, collection: str, document_id: str, data: Dict[str, Any], merge: bool = True) -> bool:
        """Создание или обновление документа с указанным ID"""
        try:
            # ИСПРАВЛЕНИЕ: Обеспечиваем, что у документа есть поле id соответствующее его ID
            if 'id' not in data or data['id'] != document_id:
                data_copy = data.copy()
                data_copy['id'] = document_id
                self.db.collection(collection).document(document_id).set(data_copy, merge=merge)
            else:
                self.db.collection(collection).document(document_id).set(data, merge=merge)
            return True
        except Exception as e:
            logger.error(f"Ошибка при установке документа {document_id} в {collection}: {str(e)}")
            return False

    def update_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Обновление существующего документа"""
        try:
            # ИСПРАВЛЕНИЕ: Проверяем существование документа перед обновлением
            doc_ref = self.db.collection(collection).document(document_id)
            doc = doc_ref.get()

            if not doc.exists:
                logger.error(f"Документ {document_id} не существует в коллекции {collection}")
                return False

            doc_ref.update(data)
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении документа {document_id} в {collection}: {str(e)}")
            return False

    def delete_document(self, collection: str, document_id: str) -> bool:
        """Удаление документа"""
        try:
            self.db.collection(collection).document(document_id).delete()
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении документа {document_id} из {collection}: {str(e)}")
            return False

    def query_documents(self, collection: str, field: str, operator: str, value: Any) -> List[Dict[str, Any]]:
        """Запрос документов по условию"""
        try:
            # ИСПРАВЛЕНИЕ: Использование современного синтаксиса для фильтрации
            query = self.db.collection(collection).where(filter=firestore.FieldFilter(field, operator, value))
            docs = query.get()

            # ИСПРАВЛЕНИЕ: Добавляем ID в данные
            result = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                result.append(data)

            return result
        except Exception as e:
            logger.error(f"Ошибка при запросе документов из {collection}: {str(e)}")
            return []

    def get_all_documents(self, collection: str) -> List[Dict[str, Any]]:
        """Получение всех документов из коллекции"""
        try:
            docs = self.db.collection(collection).get()

            # ИСПРАВЛЕНИЕ: Добавляем ID в данные
            result = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                result.append(data)

            return result
        except Exception as e:
            logger.error(f"Ошибка при получении всех документов из {collection}: {str(e)}")
            return []

    # --- Методы для работы с Authentication ---

    def create_user(self, email: str, password: str, display_name: str = None) -> Optional[str]:
        """Создание нового пользователя в Firebase Authentication"""
        try:
            user_data = {
                'email': email,
                'password': password,
                'email_verified': False,
            }

            if display_name:
                user_data['display_name'] = display_name

            user = auth.create_user(**user_data)
            return user.uid
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя: {str(e)}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Получение пользователя по email"""
        try:
            user = auth.get_user_by_email(email)
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'phone_number': user.phone_number
            }
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя по email {email}: {str(e)}")
            return None

    def get_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Получение пользователя по номеру телефона"""
        try:
            user = auth.get_user_by_phone_number(phone)
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'phone_number': user.phone_number
            }
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя по телефону {phone}: {str(e)}")
            return None


# Создаем экземпляр клиента Firebase
firebase_client = FirebaseClient()