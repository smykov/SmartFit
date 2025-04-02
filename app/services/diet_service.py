import logging
from typing import Dict, Any, List, Optional, Coroutine, Tuple
from datetime import datetime, date, timedelta
import pytz
import json
from app.services.mock_diet_service import mock_diet_service

from config import settings
from app.db.firebase import firebase_client
from app.services.llm import llm_service
from app.templates.formatting_helpers import (
    format_diet_message_for_whatsapp,
    create_meal_emoji,
    get_relevance_stars,
    translate_day_name,
    translate_meal_type
)

from app.models.diet import DietPlan, DailyDiet, Meal, Product, ShoppingList, ShoppingListItem

logger = logging.getLogger(__name__)

class DietService:
    """Сервис для работы с диетами"""

    async def generate_diet_plan(self, user_id: str, days: int = 7) -> Optional[Dict[str, Any]]:
        """
        Генерирует план диеты для пользователя

        Args:
            user_id: ID пользователя
            days: Количество дней для плана (по умолчанию 7)

        Returns:
            Optional[Dict[str, Any]]: План диеты или None в случае ошибки
        """
        try:
            logger.info(f"Запуск генерации персонализированной диеты для пользователя {user_id}")

            # Используем заглушку вместо OpenAI API
            if settings.USE_MOCK_SERVICES:
                # Используем заглушку
                diet_plan = await mock_diet_service.generate_diet_plan(user_id, days)
            else:
                # Получаем данные пользователя
                user_data = firebase_client.get_document("users", user_id)

                if not user_data:
                    logger.error(f"User {user_id} not found")
                    return None

                # Получаем список доступных продуктов
                products = firebase_client.get_all_documents("products")

                # Генерируем план диеты через LLM
                diet_plan = await llm_service.generate_diet_plan(user_data, days, products)

                if not diet_plan or "error" in diet_plan:
                    logger.error(f"Failed to generate diet plan: {diet_plan.get('error', 'Unknown error')}")
                    return None

                # Добавляем ID пользователя
                diet_plan["user_id"] = user_id

                # Проверяем наличие дат начала и окончания
                if "start_date" not in diet_plan:
                    diet_plan["start_date"] = datetime.now(pytz.timezone(settings.TIMEZONE)).date().isoformat()

                if "end_date" not in diet_plan:
                    start_date = datetime.strptime(diet_plan["start_date"], "%Y-%m-%d").date()
                    diet_plan["end_date"] = (start_date + timedelta(days=days - 1)).isoformat()

                # Сохраняем план в базу данных
                plan_id = firebase_client.add_document("diet_plans", diet_plan)

                if not plan_id:
                    logger.error("Failed to save diet plan to database")
                    return None

                # Добавляем ID в план
                diet_plan["id"] = plan_id

            # Выполняем постобработку для улучшения пользовательского опыта
            await self._post_process_diet_plan(diet_plan)

            return diet_plan

        except Exception as e:
            logger.error(f"Error generating diet plan: {str(e)}")
            return {"error": str(e)}

    async def _post_process_diet_plan(self, diet_plan: Dict[str, Any]) -> None:
        """
        Выполняет постобработку плана диеты для улучшения пользовательского опыта

        Args:
            diet_plan: План диеты
        """
        try:
            # Убедимся, что у всех блюд есть релевантность, если её нет
            if "daily_plans" in diet_plan:
                for date_key, day_plan in diet_plan["daily_plans"].items():
                    if "meals" in day_plan:
                        for i, meal in enumerate(day_plan["meals"]):
                            # Добавим значение релевантности, если оно отсутствует
                            if "relevance_score" not in meal or not meal["relevance_score"]:
                                meal["relevance_score"] = 7  # Значение по умолчанию

                            # Добавим объяснение, почему блюдо рекомендовано, если оно отсутствует
                            if "why_recommended" not in meal or not meal["why_recommended"]:
                                meal[
                                    "why_recommended"] = "Это блюдо соответствует вашим целям по питанию и калорийности."

                            # Обновим блюдо в плане
                            day_plan["meals"][i] = meal

            # Убедимся, что есть персонализированное обращение
            if "personalized_note" not in diet_plan or not diet_plan["personalized_note"]:
                # Получим данные пользователя
                user_id = diet_plan.get("user_id")
                if user_id:
                    user_data = firebase_client.get_document("users", user_id)
                    if user_data:
                        name = user_data.get("name", "")
                        target_weight = user_data.get("target_weight", "")
                        current_weight = user_data.get("current_weight", "")

                        # Создадим базовое персонализированное обращение
                        if name and target_weight and current_weight:
                            weight_diff = float(current_weight) - float(target_weight)
                            diet_plan["personalized_note"] = (
                                f"Привет, {name}! Этот план питания создан специально для тебя, "
                                f"чтобы помочь достичь твоей цели веса в {target_weight} кг. "
                                f"При текущем весе {current_weight} кг тебе нужно {'снизить вес на' if weight_diff > 0 else 'набрать'} "
                                f"{abs(weight_diff):.1f} кг. План учитывает твои предпочтения и обеспечивает "
                                f"необходимый {'дефицит' if weight_diff > 0 else 'профицит'} калорий."
                            )
        except Exception as e:
            logger.error(f"Error in post-processing diet plan: {str(e)}")

    async def update_diet_plan_partially(self, diet_plan_id: str, updated_days: Dict[str, Any], comment: str = None) -> \
    Tuple[bool, Dict[str, Any]]:
        """
        Обновляет частично план питания, изменяя только указанные дни

        Args:
            diet_plan_id: ID плана диеты
            updated_days: Словарь {дата: данные на день}
            comment: Комментарий по изменению

        Returns:
            Tuple[bool, Dict[str, Any]]: (успех, обновленный план)
        """
        try:
            # Получаем план диеты
            diet_plan = firebase_client.get_document("diet_plans", diet_plan_id)

            if not diet_plan:
                logger.error(f"План с ID {diet_plan_id} не найден")
                return False, {"error": "План питания не найден"}

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
            success = firebase_client.update_document(
                "diet_plans",
                diet_plan_id,
                {
                    "daily_plans": diet_plan["daily_plans"],
                    "modifications_history": diet_plan.get("modifications_history", [])
                }
            )

            if success:
                logger.info(f"План питания {diet_plan_id} успешно обновлен")
                return True, diet_plan
            else:
                logger.error(f"Не удалось обновить план питания {diet_plan_id}")
                return False, {"error": "Не удалось обновить план питания"}

        except Exception as e:
            logger.error(f"Ошибка при обновлении плана диеты: {str(e)}")
            return False, {"error": str(e)}

    async def get_current_diet(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает текущий план диеты пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Текущий план диеты или None, если план не найден
        """
        try:
            # Получаем текущую дату
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Ищем план диеты, который включает текущую дату
            diet_plans = firebase_client.query_documents("diet_plans", "user_id", "==", user_id)

            current_plan = None
            for plan in diet_plans:
                start_date = datetime.strptime(plan.get("start_date", "2000-01-01"), "%Y-%m-%d").date()
                end_date = datetime.strptime(plan.get("end_date", "2000-01-01"), "%Y-%m-%d").date()

                if start_date <= today <= end_date:
                    current_plan = plan
                    break

            return current_plan

        except Exception as e:
            logger.error(f"Error getting current diet: {str(e)}")
            return None

    async def get_diet_for_day(self, user_id: str, day_date: date = None) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты на конкретный день

        Args:
            user_id: ID пользователя
            day_date: Дата, на которую нужен план (по умолчанию сегодня)

        Returns:
            Optional[Dict[str, Any]]: План на день или None, если план не найден
        """
        try:
            # Если дата не указана, используем сегодняшнюю
            if not day_date:
                day_date = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Получаем текущий план диеты
            current_plan = await self.get_current_diet(user_id)

            if not current_plan:
                return None

            # Получаем план на конкретный день
            daily_plans = current_plan.get("daily_plans", {})
            day_str = day_date.isoformat()

            # Если плана на указанный день нет, возвращаем None
            if day_str not in daily_plans:
                return None

            return daily_plans[day_str]

        except Exception as e:
            logger.error(f"Error getting diet for day: {str(e)}")
            return None

    async def generate_shopping_list(self, diet_plan_id: str) -> dict[str, str] | dict[
        str, str | int | Any] | None | Any:
        """
        Создает список покупок на основе плана диеты

        Args:
            diet_plan_id: ID плана диеты

        Returns:
            Optional[List[Dict[str, Any]]]: Список покупок или None в случае ошибки
        """
        try:
            # Получаем план диеты
            diet_plan = firebase_client.get_document("diet_plans", diet_plan_id)

            if not diet_plan:
                logger.error(f"Diet plan {diet_plan_id} not found")
                return None

            # Проверяем наличие существующего списка покупок для этого плана
            existing_lists = firebase_client.query_documents("shopping_lists", "diet_plan_id", "==", diet_plan_id)

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
                    logger.info(f"Using existing shopping list for diet plan {diet_plan_id}")
                    return latest_list

            # Если существующего списка нет или план был изменен, создаем новый список

            # Используем заглушку вместо OpenAI API
            if settings.USE_MOCK_SERVICES:
                return await mock_diet_service.generate_shopping_list(diet_plan_id)
            else:
                # Генерируем список покупок через OpenAI
                shopping_list = await llm_service.create_shopping_list(diet_plan)

                if not shopping_list:
                    logger.error("Failed to generate shopping list")
                    return None

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

                # Сохраняем список покупок
                shopping_list_data = {
                    "user_id": diet_plan.get("user_id"),
                    "diet_plan_id": diet_plan_id,
                    "items": shopping_list,
                    "created_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
                    "updated_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
                    "total_estimated_price": sum(
                        [item.get("estimated_price", 0) for item in shopping_list if item.get("estimated_price")])
                }

                list_id = firebase_client.add_document("shopping_lists", shopping_list_data)

                if not list_id:
                    logger.error("Failed to save shopping list to database")
                    return None

                # Добавляем ID в список
                shopping_list_data["id"] = list_id

                return shopping_list_data

        except Exception as e:
            logger.error(f"Error generating shopping list: {str(e)}")
            return {"error": str(e)}

    def get_diet_summary(self, diet_plan: Dict[str, Any]) -> Tuple[str, str]:
        """
        Создает сводку плана диеты и отдельное сообщение с командами

        Args:
            diet_plan: План диеты

        Returns:
            Tuple[str, str]: (сводка плана, команды для взаимодействия)
        """
        commands_message = "*📱 Команды для взаимодействия с планом:*\n"
        commands_message += "• Напиши 'полный план' для просмотра плана на всю неделю\n"
        commands_message += "• Напиши 'план на сегодня' или 'меню на сегодня' для детального плана на сегодня\n"
        commands_message += "• Напиши 'список покупок' для получения списка продуктов\n"
        commands_message += "• Напиши 'выполнено/частично/заменил/пропустил завтрак/обед/ужин/перекус' для отметки о соблюдении плана\n"

        try:
            # Используем заглушку вместо OpenAI API
            if settings.USE_MOCK_SERVICES:
                return mock_diet_service.get_diet_summary(diet_plan)
            else:
                # Получаем персонализированное обращение
                personalized_note = diet_plan.get("personalized_note", "")

                summary = f"*📋 ПЕРСОНАЛЬНЫЙ ПЛАН ПИТАНИЯ*\n\n"

                # Добавляем персонализированное обращение
                if personalized_note:
                    summary += f"{personalized_note}\n\n"

                # Информация о калорийном дефиците
                if "caloric_deficit" in diet_plan and diet_plan["caloric_deficit"]:
                    summary += f"🔥 *Расчетный дефицит калорий:* \n{diet_plan['caloric_deficit']}\n\n"

                # Информация о калорийном профиците
                if "caloric_proficit" in diet_plan and diet_plan["caloric_proficit"]:
                    summary += f"🔥 *Расчетный профицит калорий:* \n{diet_plan['caloric_proficit']}\n\n"

                # Общие рекомендации
                if "general_recommendations" in diet_plan and diet_plan["general_recommendations"]:
                    summary += f"📝 *Общие рекомендации:* \n{diet_plan['general_recommendations']}\n\n"

                # Информация о стоимости
                if "estimated_weekly_price" in diet_plan and diet_plan["estimated_weekly_price"]:
                    summary += f"💰 *Примерная стоимость:* \n{diet_plan['estimated_weekly_price']} кетцалей в неделю\n\n"

                # Примеры приемов пищи на сегодня или первый день
                today = datetime.now(pytz.timezone(settings.TIMEZONE)).date().isoformat()

                if "daily_plans" in diet_plan and diet_plan["daily_plans"]:
                    # Используем сегодняшний день или первый доступный
                    day_key = today if today in diet_plan["daily_plans"] else next(iter(diet_plan["daily_plans"]))
                    day_plan = diet_plan["daily_plans"][day_key]

                    # Получаем день недели и форматируем дату
                    day_date = datetime.strptime(day_key, "%Y-%m-%d").date()
                    day_name = translate_day_name(day_date.strftime("%A"))
                    date_formatted = day_date.strftime("%d.%m.%Y")

                    summary += f"📅 *Пример меню на {day_name}, {date_formatted}:*\n"

                    if "meals" in day_plan:
                        for meal in day_plan["meals"]:
                            meal_type = translate_meal_type(meal.get("type", ""))
                            title = meal.get("title", "")
                            calories = meal.get("calories", "")
                            relevance = get_relevance_stars(meal.get("relevance_score", 0))
                            emoji = create_meal_emoji(meal.get("type", ""))

                            summary += f"{emoji} *{meal_type}*: \n{title} {relevance}\n"

                            if calories:
                                summary += f"  Калории: {calories} ккал\n"

                            # Добавляем объяснение, почему блюдо рекомендовано
                            why_recommended = meal.get("why_recommended", "")
                            if why_recommended:
                                summary += f"  _Почему рекомендуем: {why_recommended}_\n"

                return format_diet_message_for_whatsapp(summary), format_diet_message_for_whatsapp(commands_message)

        except Exception as e:
            logger.error(f"Error creating diet summary: {str(e)}")
            return format_diet_message_for_whatsapp("План питания создан. Напишите 'план' для получения подробной информации."), format_diet_message_for_whatsapp(commands_message),

    def get_full_diet_plan(self, diet_plan: Dict[str, Any]) -> List[str]:
        """
        Создает полный план диеты на все дни для отправки пользователю.
        Возвращает список сообщений из-за ограничений длины в WhatsApp.

        Args:
            diet_plan: План диеты

        Returns:
            List[str]: Список сообщений с планом диеты
        """
        try:
            messages = []
            summary = ""

            # Получаем персонализированное обращение для первого сообщения
            intro_message = f"*📋 ПОЛНЫЙ ПЛАН ПИТАНИЯ НА НЕДЕЛЮ*\n\n"

            # Добавляем персонализированное обращение
            personalized_note = diet_plan.get("personalized_note", "")
            if personalized_note:
                intro_message += f"{personalized_note}\n\n"

            # Общие рекомендации
            if "general_recommendations" in diet_plan and diet_plan["general_recommendations"]:
                intro_message += f"📝 *Общие рекомендации:*\n{diet_plan['general_recommendations']}\n\n"

            # Информация о калорийном дефиците
            if "caloric_deficit" in diet_plan and diet_plan["caloric_deficit"]:
                intro_message += f"🔥 *Расчетный дефицит калорий:* {diet_plan['caloric_deficit']}\n\n"
            # Информация о калорийном профиците
            if "caloric_proficit" in diet_plan and diet_plan["caloric_proficit"]:
                summary += f"🔥 *Расчетный профицит калорий:* \n{diet_plan['caloric_proficit']}\n\n"

            # Информация о стоимости
            if "estimated_weekly_price" in diet_plan and diet_plan["estimated_weekly_price"]:
                intro_message += f"💰 *Примерная стоимость:* {diet_plan['estimated_weekly_price']} кетцалей в неделю\n\n"

            messages.append(format_diet_message_for_whatsapp(intro_message))

            # Создаем отдельное сообщение для каждого дня
            if "daily_plans" in diet_plan and diet_plan["daily_plans"]:
                # Сортируем даты
                sorted_dates = sorted(diet_plan["daily_plans"].keys())

                for day_key in sorted_dates:
                    day_plan = diet_plan["daily_plans"][day_key]

                    # Получаем день недели и форматируем дату
                    day_date = datetime.strptime(day_key, "%Y-%m-%d").date()
                    day_name = translate_day_name(day_date.strftime("%A"))
                    date_formatted = day_date.strftime("%d.%m.%Y")

                    day_message = f"*📅 {day_name}, {date_formatted}*\n"

                    # Добавляем информацию о калориях и макронутриентах
                    if "total_calories" in day_plan:
                        day_message += f"Всего калорий: {day_plan['total_calories']} ккал\n"

                    if "macros_ratio" in day_plan and day_plan["macros_ratio"]:
                        day_message += f"Соотношение БЖУ: {day_plan['macros_ratio']}\n"
                    elif "total_proteins" in day_plan and "total_fats" in day_plan and "total_carbs" in day_plan:
                        day_message += f"Белки: {day_plan['total_proteins']}г, Жиры: {day_plan['total_fats']}г, Углеводы: {day_plan['total_carbs']}г\n"

                    day_message += "\n"

                    # Добавляем приемы пищи
                    if "meals" in day_plan:
                        for meal in day_plan["meals"]:
                            meal_type = translate_meal_type(meal.get("type", ""))
                            title = meal.get("title", "")
                            calories = meal.get("calories", "")
                            relevance = get_relevance_stars(meal.get("relevance_score", 0))
                            emoji = create_meal_emoji(meal.get("type", ""))

                            day_message += f"{emoji} *{meal_type}*: {title} {relevance}\n"

                            # Добавляем информацию о калориях и макронутриентах
                            nutrients_info = []
                            if calories:
                                nutrients_info.append(f"{calories} ккал")
                            if meal.get("proteins"):
                                nutrients_info.append(f"Б: {meal['proteins']}г")
                            if meal.get("fats"):
                                nutrients_info.append(f"Ж: {meal['fats']}г")
                            if meal.get("carbs"):
                                nutrients_info.append(f"У: {meal['carbs']}г")

                            if nutrients_info:
                                day_message += f"  {', '.join(nutrients_info)}\n"

                            # Добавляем объяснение, почему блюдо рекомендовано
                            why_recommended = meal.get("why_recommended", "")
                            if why_recommended:
                                day_message += f"  _Почему: {why_recommended}_\n"

                            day_message += "\n"

                    # Добавляем советы на день, если они есть
                    if "tips" in day_plan and day_plan["tips"]:
                        day_message += f"💡 *Совет дня:* {day_plan['tips']}\n"

                    messages.append(format_diet_message_for_whatsapp(day_message))

            return messages

        except Exception as e:
            logger.error(f"Error creating full diet plan: {str(e)}")
            return ["Ошибка при создании полного плана питания. Попробуйте позже."]

    def get_day_diet_plan(self, diet_plan: Dict[str, Any], day_date: date = None) -> str:
        """
        Создает детальный план диеты на конкретный день

        Args:
            diet_plan: План диеты
            day_date: Дата, на которую нужен план (по умолчанию сегодня)

        Returns:
            str: Сообщение с планом на день
        """
        try:
            # Если дата не указана, используем сегодняшнюю
            if not day_date:
                day_date = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Преобразуем в строку
            day_key = day_date.isoformat()

            # Проверяем, есть ли план на указанный день
            if "daily_plans" not in diet_plan or day_key not in diet_plan["daily_plans"]:
                return "К сожалению, на указанную дату нет плана питания."

            day_plan = diet_plan["daily_plans"][day_key]

            # Получаем день недели и форматируем дату
            day_name = translate_day_name(day_date.strftime("%A"))
            date_formatted = day_date.strftime("%d.%m.%Y")

            message = f"*📅 ПЛАН ПИТАНИЯ НА {day_name.upper()}, {date_formatted}*\n\n"

            # Добавляем информацию о калориях и макронутриентах
            if "total_calories" in day_plan:
                message += f"*Всего калорий:* {day_plan['total_calories']} ккал\n"

            if "macros_ratio" in day_plan and day_plan["macros_ratio"]:
                message += f"*Соотношение БЖУ:* {day_plan['macros_ratio']}\n"
            elif "total_proteins" in day_plan and "total_fats" in day_plan and "total_carbs" in day_plan:
                message += f"*Макронутриенты:* Белки: {day_plan['total_proteins']}г, Жиры: {day_plan['total_fats']}г, Углеводы: {day_plan['total_carbs']}г\n"

            message += "\n"

            # Добавляем приемы пищи
            if "meals" in day_plan:
                for meal in day_plan["meals"]:
                    meal_type = translate_meal_type(meal.get("type", ""))
                    title = meal.get("title", "")
                    description = meal.get("description", "")
                    relevance = get_relevance_stars(meal.get("relevance_score", 0))
                    emoji = create_meal_emoji(meal.get("type", ""))

                    message += f"{emoji} *{meal_type}*: {title} {relevance}\n"

                    if description:
                        message += f"{description}\n"

                    # Добавляем информацию о продуктах
                    if "products" in meal and meal["products"]:
                        message += "  *Ингредиенты:*\n"
                        for product in meal["products"]:
                            name = product.get("name", "")
                            quantity = product.get("quantity", "")
                            unit = product.get("unit", "")

                            message += f"  • {name}: {quantity} {unit}\n"

                    # Добавляем информацию о калориях и макронутриентах
                    message += "  *Пищевая ценность:*\n"
                    if meal.get("calories"):
                        message += f"  • Калории: {meal['calories']} ккал\n"
                    if meal.get("proteins"):
                        message += f"  • Белки: {meal['proteins']}г\n"
                    if meal.get("fats"):
                        message += f"  • Жиры: {meal['fats']}г\n"
                    if meal.get("carbs"):
                        message += f"  • Углеводы: {meal['carbs']}г\n"
                    if meal.get("fiber"):
                        message += f"  • Клетчатка: {meal['fiber']}г\n"

                    # Добавляем объяснение, почему блюдо рекомендовано
                    why_recommended = meal.get("why_recommended", "")
                    if why_recommended:
                        message += f"  *Почему рекомендуем:*\n  _{why_recommended}_\n"

                    # Добавляем инструкцию по приготовлению
                    preparation = meal.get("preparation", "")
                    if preparation:
                        message += f"  *Способ приготовления:*\n  {preparation}\n"

                    message += "\n"

            # Добавляем советы на день, если они есть
            if "tips" in day_plan and day_plan["tips"]:
                message += f"💡 *Совет дня:* {day_plan['tips']}\n\n"

            # Добавляем инструкции для отметки о соблюдении
            message += "*📱 Отметьте выполнение плана:*\n"
            message += "• Напишите 'выполнено завтрак/обед/ужин/перекус' для отметки о соблюдении\n"
            message += "• Напишите 'частично завтрак/обед/ужин/перекус' если следовали плану частично\n"
            message += "• Напишите 'заменил завтрак/обед/ужин/перекус' если заменили блюдо\n"
            message += "• Напишите 'пропустил завтрак/обед/ужин/перекус' если пропустили прием пищи\n"

            return format_diet_message_for_whatsapp(message)

        except Exception as e:
            logger.error(f"Error creating day diet plan: {str(e)}")
            return "Ошибка при создании плана питания на день. Попробуйте позже."

    def format_shopping_list(self, shopping_list_data: Dict[str, Any]) -> str:
        """
        Форматирует список покупок для отправки пользователю

        Args:
            shopping_list_data: Данные списка покупок

        Returns:
            str: Отформатированный список покупок
        """
        try:
            message = f"*🛒 СПИСОК ПОКУПОК*\n\n"

            # Группируем продукты по категориям
            categories = {
                "Фрукты и овощи": [],
                "Мясо и рыба": [],
                "Молочные продукты": [],
                "Хлеб и крупы": [],
                "Специи и приправы": [],
                "Напитки": [],
                "Другое": []
            }

            # Простая категоризация продуктов
            def categorize_product(product_name: str) -> str:
                name_lower = product_name.lower()
                if any(item in name_lower for item in
                       ["фрукт", "овощ", "ягод", "банан", "яблок", "морковь", "картофель", "помидор", "огурец"]):
                    return "Фрукты и овощи"
                elif any(item in name_lower for item in
                         ["мясо", "рыба", "курица", "говядина", "свинина", "филе", "фарш"]):
                    return "Мясо и рыба"
                elif any(item in name_lower for item in ["молоко", "сыр", "творог", "йогурт", "кефир", "сметана"]):
                    return "Молочные продукты"
                elif any(item in name_lower for item in
                         ["хлеб", "крупа", "рис", "овсянка", "мука", "макароны", "паста"]):
                    return "Хлеб и крупы"
                elif any(item in name_lower for item in ["специя", "соль", "перец", "приправа", "соус"]):
                    return "Специи и приправы"
                elif any(item in name_lower for item in ["напиток", "вода", "сок", "чай", "кофе"]):
                    return "Напитки"
                else:
                    return "Другое"

            # Распределяем продукты по категориям
            for item in shopping_list_data.get("items", []):
                name = item.get("name", "")
                quantity = item.get("quantity", "")
                unit = item.get("unit", "")
                price = item.get("estimated_price", "")

                # Определяем категорию
                category = categorize_product(name)

                # Форматируем элемент списка
                item_text = f"{name}: {quantity} {unit}"
                if price:
                    item_text += f" (~{price} к.)"

                categories[category].append(item_text)

            # Формируем сообщение по категориям
            for category, items in categories.items():
                if items:
                    message += f"*{category}:*\n"
                    for item in items:
                        message += f"• {item}\n"
                    message += "\n"

            # Добавляем общую стоимость
            if "total_estimated_price" in shopping_list_data and shopping_list_data["total_estimated_price"]:
                message += f"*Общая стоимость:* ~{shopping_list_data['total_estimated_price']} кетцалей\n\n"

            # Добавляем инструкции
            message += "Отправьте 'купил [название продукта]' чтобы отметить покупку.\n"

            return format_diet_message_for_whatsapp(message)

        except Exception as e:
            logger.error(f"Error formatting shopping list: {str(e)}")
            return "Ошибка при форматировании списка покупок. Попробуйте позже."


async def notify_shopping_list_generation(self, user_id: str) -> None:
    """
    Отправляет пользователю уведомление о начале формирования списка покупок

    Args:
        user_id: ID пользователя
    """
    try:
        # Получаем пользователя
        user = firebase_client.get_document("users", user_id)
        if not user or "phone_number" not in user:
            logger.error(f"Не удалось найти пользователя с ID {user_id} или у него нет номера телефона")
            return

        phone_number = user["phone_number"]

        # Импортируем WhatsApp сервис
        from app.services.whatsapp_service import whatsapp_service

        # Отправляем уведомление
        await whatsapp_service.send_message(
            phone_number,
            "🛒 Начинаю формирование списка покупок на основе вашего плана питания. Это займет несколько секунд..."
        )

    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления о генерации списка покупок: {str(e)}")

# Создаем экземпляр сервиса для диет
diet_service = DietService()