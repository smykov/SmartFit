# app/db/repositories/compliance_repository.py
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date

import pytz

from app.db.interfaces.compliance_repository_interface import IComplianceRepository
from app.models.tracking import MealComplianceStatus
from app.utils.date_helper import DateHelper
from config import settings


class FirebaseComplianceRepository(IComplianceRepository):
    """
    Репозиторий для работы с записями соблюдения плана питания через Firebase
    """

    def __init__(self, firebase_client, diet_plan_repository=None):
        """
        Инициализация репозитория записей соблюдения плана питания

        Args:
            firebase_client: Клиент Firebase для работы с базой данных
            diet_plan_repository: Репозиторий плана диеты (опционально)
        """
        self.firebase_client = firebase_client
        self.diet_plan_repository = diet_plan_repository
        self.logger = logging.getLogger(self.__class__.__name__)

    async def add_meal_compliance(self, user_id: str, date_value: date, meal_type: str,
                                  status: str, notes: str = None,
                                  alternative_meal: str = None,
                                  calories_consumed: float = None,
                                  proteins_consumed: float = None,
                                  fats_consumed: float = None,
                                  carbs_consumed: float = None,
                                  adherence_data: Dict[str, float] = None) -> Optional[str]:
        """
        Добавляет запись о соблюдении приема пищи

        Args:
            user_id: ID пользователя
            date_value: Дата
            meal_type: Тип приема пищи (breakfast, lunch, dinner, snack)
            status: Статус соблюдения (followed, partially, substituted, skipped)
            notes: Дополнительные заметки (текстовый отчёт пользователя)
            alternative_meal: Альтернативное блюдо (если status=substituted)
            calories_consumed: Фактически потреблённые калории
            proteins_consumed: Потреблённые белки
            fats_consumed: Потреблённые жиры
            carbs_consumed: Потреблённые углеводы
            adherence_data: Словарь с процентами соответствия по нутриентам
        Returns:
            Optional[str]: ID созданной записи или None в случае ошибки
        """
        try:
            # Формируем дату в формате строки
            date_str = date_value.isoformat() if isinstance(date_value, date) else date_value

            # Создаем запись о соблюдении режима
            compliance_data = {
                "user_id": user_id,
                "date": date_str,
                "meal_type": meal_type,
                "status": status,
                "notes": notes,
                "alternative_meal": alternative_meal,
                "created_at": DateHelper.get_current_datetime().isoformat(),

                # Добавляем данные о фактическом потреблении
                "calories_consumed": calories_consumed,
                "proteins_consumed": proteins_consumed,
                "fats_consumed": fats_consumed,
                "carbs_consumed": carbs_consumed,
            }

            # Добавляем данные о соответствии плану, если они предоставлены
            if adherence_data:
                for key, value in adherence_data.items():
                    compliance_data[key] = value

            # Сохраняем в базу данных
            compliance_id = await self.firebase_client.add_document("meal_compliance", compliance_data)

            if not compliance_id:
                self.logger.error(f"Failed to save meal compliance for user {user_id}")
                return None

            # Обновление данных в daily_compliance
            # Получаем текущий документ daily_compliance
            daily_compliance = await self.get_daily_compliance(user_id, date_value)

            if daily_compliance:
                # Инициализируем meals, если его нет
                if "meals" not in daily_compliance:
                    daily_compliance["meals"] = {}

                # Обновляем информацию о конкретном приеме пищи
                daily_compliance["meals"][meal_type] = {
                    "status": status,
                    "notes": notes,
                    "calories_consumed": calories_consumed,
                    "proteins_consumed": proteins_consumed,
                    "fats_consumed": fats_consumed,
                    "carbs_consumed": carbs_consumed
                }

                # Добавляем данные о соответствии, если они есть
                if adherence_data:
                    for key, value in adherence_data.items():
                        daily_compliance["meals"][meal_type][key] = value

                # Сохраняем обновленный документ
                result_data = await self._save_daily_compliance(daily_compliance)
                self.logger.info(f"Daily compliance after update: {result_data}")

            return compliance_id

        except Exception as e:
            self.logger.error(f"Error adding meal compliance: {str(e)}")
            return None

    async def get_daily_compliance(self, user_id: str, date_value: date) -> Optional[Dict[str, Any]]:
        """
        Получает статистику соблюдения плана питания за день

        Args:
            user_id: ID пользователя
            date_value: Дата

        Returns:
            Optional[Dict[str, Any]]: Статистика соблюдения или None
        """
        try:

            # Формируем дату в формате строки
            date_str = date_value.isoformat() if isinstance(date_value, date) else date_value

            # Получаем записи о соблюдении
            compliance_entries = await self.firebase_client.query_documents(
                "daily_compliance",
                "user_id",
                "==",
                user_id
            )

            # Фильтруем по дате
            daily_compliance = [c for c in compliance_entries if c.get("date") == date_str]

            if not daily_compliance:
                # Если записи нет, создаем пустую запись
                empty_compliance = {
                    "user_id": user_id,
                    "date": date_str,
                    "meals": {},
                    "overall_score": 0,
                    "created_at": DateHelper.get_current_datetime().isoformat(),
                    "updated_at": DateHelper.get_current_datetime().isoformat(),
                }
                return empty_compliance

            return daily_compliance[0]

        except Exception as e:
            self.logger.error(f"Error getting daily compliance: {str(e)}")
            return None

    async def update_daily_compliance(self, user_id: str, date_value: date) -> bool:
        """
        Обновляет данные о соблюдении плана питания на день с учетом калорий и макронутриентов

        Args:
            user_id: ID пользователя
            date_value: Дата

        Returns:
            bool: Результат операции
        """
        try:
            self.logger.info(f"Updating daily compliance for user {user_id}, date {date_value}")
            # Получаем текущие данные о соблюдении или создаем новую запись
            compliance_data = await self.get_daily_compliance(user_id, date_value)

            # Получаем приемы пищи за день
            meals_data = compliance_data.get("meals", {})

            # Проверим, нет ли проблем с структурой meals_data
            self.logger.info(f"Meals data for user {user_id}, date {date_value}: {meals_data}")

            # Получаем все запланированные приемы пищи на этот день
            day_plan = await self._get_day_plan_from_diet_service(user_id, date_value)
            planned_meals = []
            if day_plan and "meals" in day_plan:
                planned_meals = [meal["type"] for meal in day_plan["meals"] if "type" in meal]

            # Логируем для отладки
            self.logger.info(f"Planned meals for user {user_id}, date {date_value}: {planned_meals}")

            # Используем все возможные типы приемов пищи, если запланированных нет
            if not planned_meals:
                planned_meals = ["breakfast", "lunch", "dinner", "snack"]

            # Если после этого все еще нет приемов пищи, используем отмеченные
            total_meals = len(planned_meals) if planned_meals else len(meals_data)

            # Проверка на деление на ноль
            if total_meals == 0:
                self.logger.warning(f"No meals found for user {user_id}, date {date_value}")
                compliance_data["overall_score"] = 0.0
                # Сохраняем результат
                return await self._save_daily_compliance(compliance_data)

            # 1. Расчет на основе статусов приемов пищи (базовый вес)
            status_score = 0.0

            for meal_type in planned_meals:
                meal_status = meals_data.get(meal_type, {}).get("status", MealComplianceStatus.NOT_RECORDED.value)

                # Определяем вес статуса
                status_weight = 0.0
                if meal_status == MealComplianceStatus.FOLLOWED.value:
                    status_weight = 1.0
                elif meal_status == MealComplianceStatus.PARTIALLY.value:
                    status_weight = 0.75
                elif meal_status == MealComplianceStatus.SUBSTITUTED.value:
                    status_weight = 0.7
                elif meal_status == MealComplianceStatus.SKIPPED.value:
                    status_weight = 0.1

                status_score += status_weight

            status_percentage = (status_score / total_meals) * 100

            # 2. Расчет на основе соответствия калорий и нутриентов
            nutrients_score = 0.0
            nutrients_count = 0

            # Весовые коэффициенты для разных нутриентов
            # TODO сделать распределение важности в зависимости от цели (если цель похудеть, то жиры более важные, если набрать вес, то протеины важны, если поддерживать, то одинкавая важность)
            nutrient_weights = {
                "calories": 0.4,  # 40% важности
                "proteins": 0.25,  # 25% важности
                "fats": 0.25,  # 25% важности
                "carbs": 0.1  # 10% важности
            }

            for meal_type in planned_meals:
                meal_data = meals_data.get(meal_type, {})

                # Пропускаем, если нет данных или прием пищи пропущен
                if not meal_data or meal_data.get("status") == MealComplianceStatus.SKIPPED.value:
                    continue

                # Находим запланированный прием пищи для сравнения
                planned_meal = None
                if day_plan and "meals" in day_plan:
                    for meal in day_plan["meals"]:
                        if meal.get("type") == meal_type:
                            planned_meal = meal
                            break

                if not planned_meal:
                    continue

                # Рассчитываем соответствие по каждому нутриенту
                for nutrient, weight in nutrient_weights.items():
                    # Получаем запланированное и фактическое значение
                    planned_value = planned_meal.get(nutrient, 0)
                    consumed_key = f"{nutrient}_consumed"
                    consumed_value = meal_data.get(consumed_key, 0)

                    if consumed_value is None:
                        consumed_value = 0

                    if planned_value <= 0:
                        continue

                    # Рассчитываем соответствие в процентах
                    adherence = consumed_value / planned_value

                    # Добавляем к общему счету с учетом весового коэффициента
                    # Если потребление в пределах 80-120% - считаем как полное соответствие
                    if 0.8 <= adherence <= 1.2:
                        nutrient_score = 1.0 * weight
                    # Если потребление в пределах 60-130% - считаем как частичное соответствие
                    elif 0.6 <= adherence <= 1.3:
                        nutrient_score = 0.7 * weight
                    # Если слишком мало или слишком много - минимальное соответствие
                    else:
                        nutrient_score = 0.3 * weight

                    nutrients_score += nutrient_score
                    nutrients_count += weight

            # Если есть данные о нутриентах, рассчитываем процент соответствия
            nutrients_percentage = 0.0
            if nutrients_count > 0:
                nutrients_percentage = (nutrients_score / nutrients_count) * 100

            # 3. Комбинированный расчет с учетом как статуса, так и нутриентов
            # Если данных о нутриентах нет, используем только статус
            if nutrients_count == 0:
                overall_score = status_percentage
            else:
                # Если есть данные о нутриентах, используем взвешенную комбинацию
                # 30% вес статуса, 70% вес соответствия нутриентов
                overall_score = status_percentage * 0.3 + nutrients_percentage * 0.7

            # Сохраняем результаты в данные соблюдения
            compliance_data["overall_score"] = round(overall_score, 1)
            compliance_data["status_score"] = round(status_percentage, 1)
            compliance_data["nutrients_score"] = round(nutrients_percentage, 1)
            compliance_data["updated_at"] = DateHelper.get_current_datetime().isoformat()

            self.logger.info(
                f"Status score: {status_percentage}, nutrients score: {nutrients_percentage}, overall score: {overall_score}")

            # Сохраняем обновленные данные
            result = await self._save_daily_compliance(compliance_data)
            self.logger.info(f"Daily compliance updated: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Error updating daily compliance: {str(e)}", exc_info=True)
            return False

    async def _save_daily_compliance(self, compliance_data):
        """
        Сохраняет данные о соблюдении плана
        """
        # Проверяем, существует ли уже запись в БД (есть ли id)
        compliance_id = compliance_data.get("id")
        collection_name = "daily_compliance"

        if compliance_id:
            # Если запись существует, обновляем её
            result = await self.firebase_client.update_document(collection_name, compliance_id, compliance_data)
        else:
            # Если записи нет, создаем новую
            compliance_id = await self.firebase_client.add_document(collection_name, compliance_data)
            result = bool(compliance_id)

        return result

    async def _get_day_plan_from_diet_service(self, user_id, date_value):
        """
        Получает план на день из сервиса диет
        """
        try:
            if self.diet_plan_repository:
                # Получаем текущий план диеты
                diet_plan = await self.diet_plan_repository.get_current_diet(user_id)
                if not diet_plan:
                    self.logger.warning(f"No diet plan found for user {user_id}")
                    return None

                # Определяем день недели
                day_of_week = self._get_day_of_week(date_value)

                # Получаем план на день по дате или дню недели
                date_str = date_value.isoformat()

                # Проверяем по дате
                daily_plans = diet_plan.get("daily_plans", {})

                # Логируем для отладки
                self.logger.info(f"Daily plans keys: {daily_plans.keys()}")

                if date_str in daily_plans:
                    return daily_plans[date_str]

                # Проверяем по дню недели
                if day_of_week in daily_plans:
                    return daily_plans[day_of_week]

                # Если не найдено, проверим другие форматы дат
                for day_key in daily_plans.keys():
                    if day_key.startswith(date_str) or date_str.startswith(day_key):
                        return daily_plans[day_key]
        except Exception as e:
            self.logger.error(f"Error getting day plan: {str(e)}")

        return None

    def _get_day_of_week(self, date_val: date) -> str:
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

    # Метод для получения всех запланированных приемов пищи на день
    async def get_planned_meals_for_day(self, user_id: str, date_value: date) -> List[str]:
        """
        Получает список всех запланированных приемов пищи на день

        Args:
            user_id: ID пользователя
            date_value: Дата

        Returns:
            List[str]: Список типов приемов пищи
        """
        try:
            # Получаем план диеты
            diet_plan = await self.diet_plan_repository.get_current_diet(user_id)
            if not diet_plan:
                return []

            # Определяем день недели
            day_of_week = self._get_day_of_week(date_value)

            # Получаем план на день
            daily_plan = diet_plan.get("daily_plans", {}).get(day_of_week, {})

            # Получаем все типы приемов пищи из плана
            meals = daily_plan.get("meals", [])
            meal_types = [meal.get("type") for meal in meals if meal.get("type")]

            return meal_types

        except Exception as e:
            self.logger.error(f"Error getting planned meals for day: {str(e)}")
            return []

    async def get_compliance_by_period(self, user_id: str, start_date: date,
                                       end_date: date) -> List[Dict[str, Any]]:
        """
        Получает статистику соблюдения плана питания за период

        Args:
            user_id: ID пользователя
            start_date: Начальная дата периода
            end_date: Конечная дата периода

        Returns:
            List[Dict[str, Any]]: Список статистик соблюдения по дням
        """
        try:
            # Преобразуем даты в строки
            start_str = start_date.isoformat() if isinstance(start_date, date) else start_date
            end_str = end_date.isoformat() if isinstance(end_date, date) else end_date

            # Получаем все записи о соблюдении
            compliance_entries = await self.firebase_client.query_documents(
                "daily_compliance",
                "user_id",
                "==",
                user_id
            )

            # Фильтруем по дате
            filtered_entries = []
            for entry in compliance_entries:
                entry_date = entry.get("date", "")
                if start_str <= entry_date <= end_str:
                    # Пытаемся добавить информацию о приемах пищи с нутриентами
                    await self._enrich_compliance_data(entry)
                    filtered_entries.append(entry)

            return filtered_entries

        except Exception as e:
            self.logger.error(f"Error getting compliance by period: {str(e)}")
            return []

    async def _enrich_compliance_data(self, compliance_data: Dict[str, Any]) -> None:
        """
        Обогащает данные о соблюдении информацией о нутриентах

        Args:
            compliance_data: Данные о соблюдении
        """
        try:
            self.logger.info(f"Enriching compliance data: {compliance_data}")
            # Если в данных уже есть информация о приемах пищи с нутриентами, пропускаем
            if "meals" in compliance_data and any(
                    "calories_consumed" in meal for meal in compliance_data["meals"].values()):
                return

            # Получаем все записи о соблюдении для этого дня
            user_id = compliance_data.get("user_id")
            date_str = compliance_data.get("date")

            if not user_id or not date_str:
                return

            # Получаем записи о соблюдении
            compliance_entries = await self.firebase_client.query_documents(
                "meal_compliance",
                "user_id",
                "==",
                user_id
            )

            # Фильтруем по дате
            day_entries = [entry for entry in compliance_entries if entry.get("date") == date_str]

            # Группируем по типу приема пищи
            meals_data = {}
            for entry in day_entries:
                meal_type = entry.get("meal_type")
                if meal_type:
                    meals_data[meal_type] = {
                        "status": entry.get("status"),
                        "notes": entry.get("notes"),
                        "calories_consumed": entry.get("calories_consumed"),
                        "proteins_consumed": entry.get("proteins_consumed"),
                        "fats_consumed": entry.get("fats_consumed"),
                        "carbs_consumed": entry.get("carbs_consumed"),
                        "calories_adherence": entry.get("calories_adherence"),
                        "proteins_adherence": entry.get("proteins_adherence"),
                        "fats_adherence": entry.get("fats_adherence"),
                        "carbs_adherence": entry.get("carbs_adherence")
                    }

            # Обновляем данные
            if meals_data:
                compliance_data["meals"] = meals_data

        except Exception as e:
            self.logger.error(f"Error enriching compliance data: {str(e)}")

    async def delete_compliance(self, compliance_id: str) -> bool:
        """
        Удаляет запись о соблюдении плана питания

        Args:
            compliance_id: ID записи

        Returns:
            bool: Результат удаления
        """
        try:
            return await self.firebase_client.delete_document(
                "meal_compliance",
                compliance_id
            )
        except Exception as e:
            self.logger.error(f"Error deleting compliance: {str(e)}")
            return False
