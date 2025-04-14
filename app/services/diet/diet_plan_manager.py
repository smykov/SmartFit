# app/services/diet/diet_plan_manager.py

import json
from datetime import datetime, date
from typing import Dict, Any, Optional, Tuple

import pytz

from app.constants.localization_keys import LocalizationKeys as LK
from app.db.interfaces.diet_plan_repository_interface import IDietPlanRepository
from app.db.interfaces.product_repository_interface import IProductRepository
from app.db.interfaces.user_repository_interface import IUserRepository

from app.services.diet.base_service import BaseDietService
from app.services.localization.localization_interface import ILocalizationService
from app.templates.prompts import (
    create_diet_system_prompt,
    create_short_diet_system_prompt,
    create_short_diet_user_prompt,
    update_diet_user_prompt,
    update_short_diet_user_prompt
)
from config import settings


class DietPlanManager(BaseDietService):
    """Класс для создания и управления планами диет"""

    def __init__(
            self,
            llm_service,
            diet_plan_repository: IDietPlanRepository,
            product_repository: IProductRepository,
            user_repository: IUserRepository,
            localization_service: ILocalizationService = None
    ):
        """
        Инициализация менеджера планов диет

        Args:
            llm_service: Сервис LLM для генерации планов диет
            diet_plan_repository: Репозиторий для работы с планами диет
            product_repository: Репозиторий для работы с продуктами
            user_repository: Репозиторий для работы с пользователями
            localization_service: Сервис локализации
        """
        super().__init__()
        self.llm_service = llm_service
        self.diet_plan_repository = diet_plan_repository
        self.product_repository = product_repository
        self.user_repository = user_repository
        self.localization_service = localization_service

    def get_localized_message(self, key: str, lang: Optional[str] = None, **params) -> str:
        """
        Получает локализованное сообщение

        Args:
            key: Ключ сообщения
            lang: Код языка
            **params: Параметры для форматирования

        Returns:
            str: Локализованное сообщение
        """
        if hasattr(self, 'localization_service') and self.localization_service:
            return self.localization_service.get_message(key, lang, **params)
        return key

    async def generate_short_diet_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Генерирует краткую версию плана диеты для согласования

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Краткий план диеты или None в случае ошибки
        """
        try:
            self.logger.info(f"Генерация краткой версии плана для пользователя {user_id}")

            # Получаем данные пользователя
            user_data = await self.user_repository.get_by_id(user_id)
            if not user_data:
                self.logger.error(f"User {user_id} not found")
                return None

            # Получаем список доступных продуктов
            products = await self.product_repository.get_all()

            # Создаем системный и пользовательский промпты для LLM
            system_prompt = create_short_diet_system_prompt(products)
            user_prompt = create_short_diet_user_prompt(user_data)

            # Используем LLM для генерации
            response = await self.llm_service.generate_completion(system_prompt, user_prompt)

            try:
                short_plan = json.loads(response)
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse JSON from LLM response: {response}")
                return None

            if not short_plan:
                self.logger.error("Empty response from LLM")
                return None

            # Добавляем метаданные
            short_plan["user_id"] = user_id
            short_plan["version"] = "short"
            short_plan["status"] = "pending"

            # Проверяем структуру плана
            if "daily_plans" not in short_plan:
                short_plan["daily_plans"] = {}

            # Сохраняем план в базу данных
            plan_id = self.diet_plan_repository.create(short_plan)
            if not plan_id:
                self.logger.error("Failed to save short diet plan to database")
                return None

            short_plan["id"] = plan_id

            return short_plan

        except Exception as e:
            self.logger.error(f"Error generating short diet plan: {str(e)}")
            return None

    async def approve_short_diet_plan(self, plan_id: str) -> bool:
        """
        Отмечает краткий план диеты как согласованный пользователем

        Args:
            plan_id: ID плана диеты

        Returns:
            bool: Результат операции
        """
        try:
            # Получаем план через репозиторий
            plan = await self.diet_plan_repository.get_by_id(plan_id)
            if not plan:
                self.logger.error(f"Plan {plan_id} not found")
                return False

            # Проверяем, что это краткий план
            if plan.get("version") != "short":
                self.logger.error(f"Plan {plan_id} is not a short version")
                return False

            # Обновляем статус плана через репозиторий
            result = await self.diet_plan_repository.update(
                plan_id,
                {
                    "status": "approved",
                    "updated_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"Error approving short diet plan: {str(e)}")
            return False

    async def update_short_diet_plan(self, plan_id: str, updated_days: Dict[str, Any], comment: str = None) -> Tuple[
        bool, Dict[str, Any]]:
        """
        Обновляет краткую версию плана питания на основе запроса пользователя

        Args:
            plan_id: ID плана диеты
            updated_days: Словарь {день_недели: данные_на_день}
            comment: Комментарий по изменению

        Returns:
            Tuple[bool, Dict[str, Any]]: (успех, обновленный план)
        """
        try:
            # Получаем план диеты
            diet_plan = await self.diet_plan_repository.get_by_id(plan_id)

            # Получаем язык пользователя
            lang = None
            user_id = diet_plan.get("user_id") if diet_plan else None
            if hasattr(self, 'localization_service') and self.localization_service and user_id:
                lang = await self.localization_service.get_user_language(user_id)

            if not diet_plan:
                self.logger.error(f"План с ID {plan_id} не найден")
                return False, {"error": self.get_localized_message(LK.Diet.Short.NO_PLAN, lang)}

            # Проверяем, что это краткая версия
            if diet_plan.get("version") != "short":
                self.logger.error(f"План {plan_id} не является краткой версией")
                return False, {"error": self.get_localized_message(LK.Diet.Short.INVALID_VERSION, lang)}

            # Обновляем только указанные дни недели
            if "daily_plans" not in diet_plan:
                diet_plan["daily_plans"] = {}

            for weekday, day_data in updated_days.items():
                diet_plan["daily_plans"][weekday] = day_data

                # Для краткой версии достаточно обновить total_calories, если его нет
                if "meals" in day_data and "total_calories" not in day_data:
                    total_calories = sum(meal.get("calories", 0) for meal in day_data["meals"])
                    diet_plan["daily_plans"][weekday]["total_calories"] = total_calories

            # Сохраняем комментарий к изменению
            if comment:
                last_modification = {
                    "timestamp": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
                    "comment": comment
                }

                if "modifications_history" not in diet_plan:
                    diet_plan["modifications_history"] = []

                diet_plan["modifications_history"].append(last_modification)

            # Обновляем дату обновления
            diet_plan["updated_at"] = datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()

            # Обновляем план в базе данных
            success = await self.diet_plan_repository.update(
                plan_id,
                {
                    "daily_plans": diet_plan["daily_plans"],
                    "modifications_history": diet_plan.get("modifications_history", []),
                    "updated_at": diet_plan["updated_at"]
                }
            )
            if success:
                self.logger.info(f"Краткий план питания {plan_id} успешно обновлен")
                return True, diet_plan
            else:
                self.logger.error(f"Не удалось обновить краткий план питания {plan_id}")
                return False, {"error": self.get_localized_message(LK.Diet.Short.UPDATE_FAILED, lang)}

        except Exception as e:
            self.logger.error(f"Ошибка при обновлении краткого плана диеты: {str(e)}")
            return False, {"error": str(e)}

    async def update_diet_plan_partially(self, plan_id: str, updated_days: Dict[str, Any],
                                         comment: str = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Обновляет частично план питания, изменяя только указанные дни

        Args:
            plan_id: ID плана диеты
            updated_days: Словарь {дата: данные на день}
            comment: Комментарий по изменению

        Returns:
            Tuple[bool, Dict[str, Any]]: (успех, обновленный план)
        """
        try:
            # Получаем план диеты
            diet_plan = await self.diet_plan_repository.get_by_id(plan_id)

            # Получаем язык пользователя
            lang = None
            user_id = diet_plan.get("user_id") if diet_plan else None
            if hasattr(self, 'localization_service') and self.localization_service and user_id:
                lang = await self.localization_service.get_user_language(user_id)

            if not diet_plan:
                self.logger.error(f"План с ID {plan_id} не найден")
                return False, {"error": self.get_localized_message(LK.Diet.Full.NO_PLAN, lang)}

            # Обновляем только указанные дни
            if "daily_plans" not in diet_plan:
                diet_plan["daily_plans"] = {}

            for date_str, day_data in updated_days.items():
                diet_plan["daily_plans"][date_str] = day_data

                # Пересчитываем общие показатели для дня, если это необходимо
                if "meals" in day_data and "total_calories" not in day_data:
                    total_calories = sum(meal.get("calories", 0) for meal in day_data["meals"])
                    total_proteins = sum(meal.get("proteins", 0) for meal in day_data["meals"])
                    total_fats = sum(meal.get("fats", 0) for meal in day_data["meals"])
                    total_carbs = sum(meal.get("carbs", 0) for meal in day_data["meals"])
                    total_price = sum(meal.get("estimated_price", 0) for meal in day_data["meals"])

                    diet_plan["daily_plans"][date_str]["total_calories"] = total_calories
                    diet_plan["daily_plans"][date_str]["total_proteins"] = total_proteins
                    diet_plan["daily_plans"][date_str]["total_fats"] = total_fats
                    diet_plan["daily_plans"][date_str]["total_carbs"] = total_carbs
                    diet_plan["daily_plans"][date_str]["estimated_total_price"] = total_price

            # Сохраняем комментарий к изменению
            if comment:
                last_modification = {
                    "timestamp": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
                    "comment": comment
                }

                if "modifications_history" not in diet_plan:
                    diet_plan["modifications_history"] = []

                diet_plan["modifications_history"].append(last_modification)

            # Обновляем план в базе данных
            success = await self.diet_plan_repository.update(
                plan_id,
                {
                    "daily_plans": diet_plan["daily_plans"],
                    "modifications_history": diet_plan.get("modifications_history", [])
                }
            )
            if success:
                self.logger.info(f"План питания {plan_id} успешно обновлен")
                return True, diet_plan
            else:
                self.logger.error(f"Не удалось обновить план питания {plan_id}")
                return False, {"error": self.get_localized_message(LK.Diet.Full.UPDATE_FAILED, lang)}

        except Exception as e:
            self.logger.error(f"Ошибка при обновлении плана диеты: {str(e)}")
            return False, {"error": str(e)}

    async def get_diet_plan_by_id(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты по его ID

        Args:
            plan_id: ID плана диеты

        Returns:
            Optional[Dict[str, Any]]: План диеты или None, если план не найден
        """
        try:
            # Получаем план из базы данных
            diet_plan = await self.diet_plan_repository.get_by_id(plan_id)

            if not diet_plan:
                self.logger.error(f"План диеты с ID {plan_id} не найден")
                return None

            return diet_plan

        except Exception as e:
            self.logger.error(f"Ошибка при получении плана диеты по ID: {str(e)}")
            return None

    async def get_current_diet(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает текущий активный план диеты пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Текущий план диеты или None, если план не найден
        """
        try:
            # Используем метод репозитория
            return await self.diet_plan_repository.get_current_diet(user_id)
        except Exception as e:
            self.logger.error(f"Error getting current diet: {str(e)}")
            return None

    async def get_diet_for_day(self, user_id: str, day_date: date) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты на конкретный день

        Args:
            user_id: ID пользователя
            day_date: Дата, на которую нужен план

        Returns:
            Optional[Dict[str, Any]]: План на день или None, если план не найден
        """
        try:
            # Получаем текущий план диеты
            diet_plan = await self.get_current_diet(user_id)
            if not diet_plan:
                return None

            # Преобразуем дату в день недели
            weekday = self.get_day_of_week(day_date)

            # Получаем план на конкретный день недели
            if "daily_plans" not in diet_plan or weekday not in diet_plan["daily_plans"]:
                return None

            return diet_plan["daily_plans"][weekday]

        except Exception as e:
            self.logger.error(f"Error getting diet for day: {str(e)}")
            return None

    async def get_today_diet(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты на сегодняшний день

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: План на сегодня или None, если план не найден
        """
        try:
            # Определяем текущий день недели
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Получаем план на текущий день
            return await self.get_diet_for_day(user_id, today)

        except Exception as e:
            self.logger.error(f"Error getting today's diet: {str(e)}")
            return None

    async def get_diet_for_weekday(self, user_id: str, weekday: str) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты на конкретный день недели

        Args:
            user_id: ID пользователя
            weekday: День недели ('monday', 'tuesday', и т.д.)

        Returns:
            Optional[Dict[str, Any]]: План на день или None, если план не найден
        """
        try:
            # Получаем текущий активный план диеты
            current_plan = await self.get_current_diet(user_id)

            if not current_plan:
                return None

            # Получаем план на конкретный день недели
            daily_plans = current_plan.get("daily_plans", {})

            # Если плана на указанный день нет, возвращаем None
            if weekday not in daily_plans:
                return None

            return daily_plans[weekday]

        except Exception as e:
            self.logger.error(f"Error getting diet for weekday: {str(e)}")
            return None

    async def update_diet_plan(self, plan_id: str, update_request: str) -> Dict[str, Any]:
        """
        Обновляет план диеты на основе запроса пользователя

        Args:
            plan_id: ID плана диеты
            update_request: Текст запроса пользователя на изменение

        Returns:
            Dict[str, Any]: Результат обновления
        """
        try:
            # Получаем план диеты
            diet_plan = await self.diet_plan_repository.get_by_id(plan_id)

            # Получаем язык пользователя
            lang = None
            user_id = diet_plan.get("user_id") if diet_plan else None
            if hasattr(self, 'localization_service') and self.localization_service and user_id:
                lang = await self.localization_service.get_user_language(user_id)

            if not diet_plan:
                return {"error": self.get_localized_message(LK.Diet.Full.NO_PLAN, lang)}

            # Создаем промпт для обновления
            user_prompt = update_diet_user_prompt(update_request)

            # Получаем исторические данные для LLM
            system_prompt = create_diet_system_prompt()

            # Передаем запрос в LLM
            response = await self.llm_service.generate_completion(system_prompt, user_prompt)

            # Парсим результат
            try:
                updates = json.loads(response)
            except json.JSONDecodeError:
                self.logger.error(f"Не удалось распарсить ответ LLM: {response}")
                return {"error": self.get_localized_message(LK.Diet.Update.PARSING_ERROR, lang)}

            # Проверяем структуру ответа
            if "updated_days" not in updates:
                return {"error": self.get_localized_message(LK.Diet.Update.INVALID_FORMAT, lang)}

            # Обновляем план
            success, updated_plan = await self.update_diet_plan_partially(
                plan_id,
                updates["updated_days"],
                updates.get("comment", self.get_localized_message(LK.Diet.Update.DEFAULT_COMMENT, lang))
            )

            if success:
                return {
                    "success": True,
                    "plan": updated_plan,
                    "comment": updates.get("comment", self.get_localized_message(LK.Diet.Update.DEFAULT_COMMENT, lang)),
                    "updated_days": updates.get("updated_days", {})
                }
            else:
                return {"error": self.get_localized_message(LK.Diet.Update.UPDATE_FAILED, lang)}

        except Exception as e:
            self.logger.error(f"Ошибка при обновлении плана диеты: {str(e)}")
            return {"error": str(e)}

    async def update_short_diet_plan_by_request(self, plan_id: str, update_request: str) -> Dict[str, Any]:
        """
        Обновляет краткий план диеты на основе запроса пользователя

        Args:
            plan_id: ID плана диеты
            update_request: Текст запроса пользователя на изменение

        Returns:
            Dict[str, Any]: Результат обновления
        """
        try:
            # Получаем план диеты
            diet_plan = await self.diet_plan_repository.get_by_id(plan_id)

            # Получаем язык пользователя
            lang = None
            user_id = diet_plan.get("user_id") if diet_plan else None
            if hasattr(self, 'localization_service') and self.localization_service and user_id:
                lang = await self.localization_service.get_user_language(user_id)

            if not diet_plan:
                return {"error": self.get_localized_message(LK.Diet.Short.NO_PLAN, lang)}

            # Создаем промпт для обновления краткого плана
            user_prompt = update_short_diet_user_prompt(update_request, diet_plan)
            system_prompt = create_short_diet_system_prompt()

            # Передаем запрос в LLM
            response = await self.llm_service.generate_completion(system_prompt, user_prompt)

            # Парсим результат
            try:
                updates = json.loads(response)
            except json.JSONDecodeError:
                self.logger.error(f"Не удалось распарсить ответ LLM: {response}")
                return {"error": self.get_localized_message(LK.Diet.Update.PARSING_ERROR, lang)}

            # Проверяем структуру ответа
            if "updated_days" not in updates:
                return {"error": self.get_localized_message(LK.Diet.Update.INVALID_FORMAT, lang)}

            # Обновляем план
            success, updated_plan = await self.update_short_diet_plan(
                plan_id,
                updates["updated_days"],
                updates.get("comment", self.get_localized_message(LK.Diet.Update.DEFAULT_COMMENT, lang))
            )

            if success:
                return {
                    "success": True,
                    "plan": updated_plan,
                    "comment": updates.get("comment", self.get_localized_message(LK.Diet.Update.DEFAULT_COMMENT, lang)),
                    "updated_days": updates.get("updated_days", {})
                }
            else:
                return {"error": self.get_localized_message(LK.Diet.Short.UPDATE_FAILED, lang)}

        except Exception as e:
            self.logger.error(f"Ошибка при обновлении краткого плана диеты: {str(e)}")
            return {"error": str(e)}

        # Вспомогательные методы

    def get_day_of_week(self, date_val: date) -> str:
        """
        Возвращает день недели для указанной даты в формате 'monday', 'tuesday' и т.д.

        Args:
            date_val: Дата

        Returns:
            str: День недели
        """
        # Получаем номер дня недели (0 - понедельник, 6 - воскресенье)
        weekday = date_val.weekday()

        # Преобразуем в строковое представление
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        return days[weekday]

    async def get_pending_diet_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты, ожидающий согласования пользователем

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: План диеты или None, если такого плана нет
        """
        try:
            # Получаем все планы диеты пользователя
            diet_plans = await self.diet_plan_repository.get_user_plans(user_id)

            pending_plans = [
                plan for plan in diet_plans
                if plan.get("user_id") == "user_id" and plan.get("version") == "short"
            ]

            if not pending_plans:
                return None

            # Возвращаем самый новый ожидающий план
            return sorted(
                pending_plans,
                key=lambda p: p.get("created_at", ""),
                reverse=True
            )[0]

        except Exception as e:
            self.logger.error(f"Ошибка при получении ожидающего плана диеты: {str(e)}")
            return None
