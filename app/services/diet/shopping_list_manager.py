# app/services/diet/shopping_list_manager.py

import json
from datetime import datetime
from typing import Dict, Any

import pytz

from app.constants.localization_keys import LocalizationKeys as LK
from app.db.interfaces.diet_plan_repository_interface import IDietPlanRepository
from app.db.interfaces.shopping_list_repository_interface import IShoppingListRepository
from app.services.diet.base_service import BaseDietService
from app.services.localization.localization_interface import ILocalizationService
from app.templates.prompts import create_shopping_list_system_prompt, create_shopping_list_user_prompt
from config import settings


class ShoppingListManager(BaseDietService):
    """Класс для управления списками покупок"""

    def __init__(
            self,
            llm_service,
            diet_plan_repository: IDietPlanRepository,
            shopping_list_repository: IShoppingListRepository,
            localization_service: ILocalizationService
    ):
        """
        Инициализация менеджера списков покупок

        Args:
            llm_service: Сервис LLM для генерации списков покупок
            diet_plan_repository: Репозиторий для работы с планами диет
            shopping_list_repository: Репозиторий для работы со списками покупок
            localization_service: Сервис локализации
        """
        super().__init__()
        self.llm_service = llm_service
        self.diet_plan_repository = diet_plan_repository
        self.shopping_list_repository = shopping_list_repository
        self.localization_service = localization_service

    def get_localized_message(self, key: str, lang: str = None, **params) -> str:
        """
        Получает локализованное сообщение

        Args:
            key: Ключ сообщения
            lang: Код языка (опционально)
            **params: Параметры для подстановки

        Returns:
            str: Локализованное сообщение
        """
        if hasattr(self, 'localization_service') and self.localization_service:
            return self.localization_service.get_message(key, lang, **params)
        return key

    async def generate_shopping_list(self, diet_plan_id: str, lang: str = None) -> Dict[str, Any]:
        """
        Создает список покупок на основе плана диеты

        Args:
            diet_plan_id: ID плана диеты
            lang: Код языка (опционально)

        Returns:
            Dict[str, Any]: Список покупок или словарь с ошибкой
        """
        try:
            # Получаем план диеты
            diet_plan = await self.diet_plan_repository.get_by_id(diet_plan_id)

            if not diet_plan:
                self.logger.error(f"Diet plan {diet_plan_id} not found")
                return {"error": self.get_localized_message(LK.Shopping.DIET_PLAN_NOT_FOUND, lang)}

            # Проверяем наличие существующего списка покупок для этого плана
            existing_lists = await self.shopping_list_repository.get_by_diet_plan(diet_plan_id)

            # Находим самый последний список покупок
            if existing_lists:
                latest_list = max(existing_lists, key=lambda x: x.get("created_at", ""))

                # Проверяем, не было ли изменений в плане диеты с момента создания списка покупок
                list_timestamp = datetime.fromisoformat(latest_list.get("created_at", "2000-01-01T00:00:00"))

                # Проверяем наличие изменений в плане
                modifications_history = diet_plan.get("modifications_history", [])

                # Если нет истории изменений или последнее изменение было до создания списка покупок,
                # возвращаем существующий список
                if not modifications_history or all(
                        datetime.fromisoformat(mod.get("timestamp", "2000-01-01T00:00:00")) < list_timestamp
                        for mod in modifications_history
                ):
                    self.logger.info(f"Using existing shopping list for diet plan {diet_plan_id}")
                    return latest_list

            # Генерируем промпты для списка покупок
            system_prompt = create_shopping_list_system_prompt()
            user_prompt = create_shopping_list_user_prompt(diet_plan)

            # Генерируем список покупок через LLM
            response = await self.llm_service.generate_completion(system_prompt, user_prompt)

            try:
                # Парсим JSON-ответ
                shopping_list = json.loads(response)
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse JSON response for shopping list: {response}")
                return {"error": self.get_localized_message(LK.Shopping.PARSING_ERROR, lang)}

            # Если был найден предыдущий список покупок, переносим информацию о покупках в новый список
            if existing_lists:
                latest_list = max(existing_lists, key=lambda x: x.get("created_at", ""))

                # Создаем словарь покупок из предыдущего списка
                purchased_items = {}
                for item in latest_list.get("items", []):
                    if item.get("is_purchased", False):
                        purchased_items[item.get("name", "").lower()] = True

                # Переносим статус покупки в новый список
                for item in shopping_list:
                    item_name = item.get("name", "").lower()
                    if item_name in purchased_items:
                        item["is_purchased"] = True

            # Вычисляем общую стоимость
            total_estimated_price = sum(
                [item.get("estimated_price", 0) for item in shopping_list if item.get("estimated_price")]
            )

            # Сохраняем список покупок
            shopping_list_data = {
                "user_id": diet_plan.get("user_id"),
                "diet_plan_id": diet_plan_id,
                "items": shopping_list,
                "created_at": DateHelper.get_current_datetime().isoformat(),
                "updated_at": DateHelper.get_current_datetime().isoformat(),
                "total_estimated_price": total_estimated_price
            }

            list_id = await self.shopping_list_repository.create(shopping_list_data)

            if not list_id:
                self.logger.error("Failed to save shopping list to database")
                return {"error": self.get_localized_message(LK.Shopping.SAVE_FAILED, lang)}

            # Добавляем ID в список
            shopping_list_data["id"] = list_id

            return shopping_list_data

        except Exception as e:
            self.logger.error(f"Error generating shopping list: {str(e)}")
            return {"error": self.get_localized_message(LK.Shopping.GENERATING_ERROR, lang)}

    async def mark_product_as_purchased(self, user_id: str, product_name: str, lang: str = None) -> Dict[str, Any]:
        """
        Отмечает продукт как купленный в списке покупок

        Args:
            user_id: ID пользователя
            product_name: Название продукта
            lang: Код языка (опционально)

        Returns:
            Dict[str, Any]: Результат операции
        """
        try:
            # Получаем текущий план диеты пользователя через репозиторий
            current_plan = await self.diet_plan_repository.get_current_diet(user_id)
            if not current_plan:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Shopping.NO_DIET_PLAN, lang)
                }

            # Получаем список покупок для текущего плана через репозиторий
            shopping_lists = await self.shopping_list_repository.get_by_diet_plan(current_plan["id"])

            if not shopping_lists:
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Shopping.NO_LIST, lang)
                }

            # Берем последний список покупок
            latest_list = max(shopping_lists, key=lambda x: x.get("created_at", ""))

            # Отмечаем продукт как купленный
            result = await self.shopping_list_repository.mark_item_as_purchased(
                latest_list["id"],
                product_name
            )

            if result:
                return {
                    "success": True,
                    "message": self.get_localized_message(
                        LK.Shopping.PRODUCT_MARKED,
                        lang,
                        product=product_name
                    )
                }
            else:
                return {
                    "success": False,
                    "message": self.get_localized_message(
                        LK.Shopping.PRODUCT_NOT_FOUND,
                        lang,
                        product=product_name
                    )
                }

        except Exception as e:
            self.logger.error(f"Error marking product as purchased: {str(e)}")
            return {
                "success": False,
                "message": self.get_localized_message(LK.Shopping.MARKING_ERROR, lang)
            }