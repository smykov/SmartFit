import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple

import pytz

from app.db.firebase import firebase_client
from app.services.llm import llm_service
from app.services.mock_diet_service import mock_diet_service
from app.services.progressive_diet_generator import ProgressiveDietGenerator
from app.templates.formatting_helpers import (
    format_diet_message_for_whatsapp,
    create_meal_emoji,
    get_relevance_stars,
    translate_day_name,
    translate_meal_type
)
from app.templates.prompts import create_short_diet_system_prompt, create_short_diet_user_prompt
from config import settings

logger = logging.getLogger(__name__)


class DietService:
    """Сервис для работы с диетами"""

    async def generate_short_diet_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Генерирует краткую версию плана диеты для согласования

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Краткий план диеты или None в случае ошибки
        """
        try:
            logger.info(f"Генерация краткой версии плана для пользователя {user_id}")

            # Получаем данные пользователя
            user_data = firebase_client.get_document("users", user_id)
            if not user_data:
                logger.error(f"User {user_id} not found")
                return None

            # Используем LLM для генерации краткого плана
            if settings.USE_MOCK_SERVICES:
                # Используем заглушку для тестирования
                short_plan = await mock_diet_service.generate_short_diet_plan(user_data)
            else:
                # Получаем список доступных продуктов
                products = firebase_client.get_all_documents("products")

                # Создаем системный и пользовательский промпты для LLM
                system_prompt = create_short_diet_system_prompt(products)
                user_prompt = create_short_diet_user_prompt(user_data)

                # Используем LLM для генерации
                response = await llm_service.generate_completion(system_prompt, user_prompt)

                try:
                    short_plan = json.loads(response)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON from LLM response: {response}")
                    return None

            if not short_plan or "error" in short_plan:
                logger.error(f"Failed to generate short diet plan: {short_plan.get('error', 'Unknown error')}")
                return None

            # Добавляем метаданные
            short_plan["user_id"] = user_id
            short_plan["version"] = "short"
            short_plan["status"] = "pending"
            short_plan["created_at"] = DateHelper.get_current_datetime().isoformat()
            short_plan["updated_at"] = DateHelper.get_current_datetime().isoformat()

            # Проверяем структуру плана
            if "daily_plans" not in short_plan:
                short_plan["daily_plans"] = {}

            # Сохраняем план в базу данных
            plan_id = firebase_client.add_document("diet_plans", short_plan)
            if not plan_id:
                logger.error("Failed to save short diet plan to database")
                return None

            short_plan["id"] = plan_id
            # Выполняем постобработку для улучшения пользовательского опыта
            await self._post_process_diet_plan(short_plan)

            return short_plan

        except Exception as e:
            logger.error(f"Error generating short diet plan: {str(e)}")
            return {"error": str(e)}

    async def generate_full_diet_plan(self, short_plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Генерирует полную версию плана диеты на основе согласованного краткого плана

        Args:
            short_plan_id: ID краткого плана диеты

        Returns:
            Optional[Dict[str, Any]]: Полный план диеты или None в случае ошибки
        """
        try:
            # Получаем краткий план
            short_plan = firebase_client.get_document("diet_plans", short_plan_id)
            if not short_plan:
                logger.error(f"Short plan {short_plan_id} not found")
                return None

            # Проверяем, что план согласован
            if short_plan.get("status") != "approved":
                logger.error(f"Short plan {short_plan_id} is not approved yet")
                return {"error": "Short plan not approved yet"}

            # Получаем данные пользователя
            user_id = short_plan.get("user_id")
            user_data = firebase_client.get_document("users", user_id)
            if not user_data:
                logger.error(f"User {user_id} not found")
                return None

            # Генерируем полный план
            if settings.USE_MOCK_SERVICES:
                # Используем заглушку для тестирования
                return await mock_diet_service.generate_full_diet_plan(user_data, short_plan)


            # Используем прогрессивную генерацию плана
            progressive_generator = ProgressiveDietGenerator(
                llm_service=llm_service,
                short_plan_id=short_plan_id,
                user_data=user_data
            )

            # Запускаем генерацию
            full_plan = await progressive_generator.generate_full_plan()

            if not full_plan:
                logger.error("Failed to generate full diet plan")
                return None

            # Обновляем статус краткого плана после успешной генерации
            if all(day in full_plan["daily_plans"] for day in progressive_generator.DAYS_OF_WEEK):
                firebase_client.update_document(
                    "diet_plans",
                    short_plan_id,
                    {"status": "archived"}
                )

            # Выполняем постобработку для улучшения пользовательского опыта
            return full_plan

        except Exception as e:
            logger.error(f"Error generating full diet plan: {str(e)}")
            return {"error": str(e)}

    async def approve_short_diet_plan(self, plan_id: str) -> bool:
        """
        Отмечает краткий план диеты как согласованный пользователем

        Args:
            plan_id: ID плана диеты

        Returns:
            bool: Результат операции
        """
        try:
            # Получаем план
            plan = firebase_client.get_document("diet_plans", plan_id)
            if not plan:
                logger.error(f"Plan {plan_id} not found")
                return False

            # Проверяем, что это краткий план
            if plan.get("version") != "short":
                logger.error(f"Plan {plan_id} is not a short version")
                return False

            # Обновляем статус плана
            result = firebase_client.update_document(
                "diet_plans",
                plan_id,
                {
                    "status": "approved",
                    "updated_at": DateHelper.get_current_datetime().isoformat()
                }
            )

            return result

        except Exception as e:
            logger.error(f"Error approving short diet plan: {str(e)}")
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
            diet_plan = firebase_client.get_document("diet_plans", plan_id)

            if not diet_plan:
                logger.error(f"План с ID {plan_id} не найден")
                return False, {"error": "План питания не найден"}

            # Проверяем, что это краткая версия
            if diet_plan.get("version") != "short":
                logger.error(f"План {plan_id} не является краткой версией")
                return False, {"error": "План не является краткой версией"}

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
                    "timestamp": DateHelper.get_current_datetime().isoformat(),
                    "comment": comment
                }

                if "modifications_history" not in diet_plan:
                    diet_plan["modifications_history"] = []

                diet_plan["modifications_history"].append(last_modification)

            # Обновляем дату обновления
            diet_plan["updated_at"] = DateHelper.get_current_datetime().isoformat()

            # Обновляем план в базе данных
            success = firebase_client.update_document(
                "diet_plans",
                plan_id,
                {
                    "daily_plans": diet_plan["daily_plans"],
                    "modifications_history": diet_plan.get("modifications_history", []),
                    "updated_at": diet_plan["updated_at"]
                }
            )

            if success:
                logger.info(f"Краткий план питания {plan_id} успешно обновлен")
                return True, diet_plan
            else:
                logger.error(f"Не удалось обновить краткий план питания {plan_id}")
                return False, {"error": "Не удалось обновить план питания"}

        except Exception as e:
            logger.error(f"Ошибка при обновлении краткого плана диеты: {str(e)}")
            return False, {"error": str(e)}

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
                    "timestamp": DateHelper.get_current_datetime().isoformat(),
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
        Получает текущий активный план диеты пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Текущий план диеты или None, если план не найден
        """
        try:
            # Ищем активный план диеты
            diet_plans = firebase_client.query_documents("diet_plans", "user_id", "==", user_id)

            # Сначала ищем полную версию с активным статусом
            active_plans = [plan for plan in diet_plans if
                            plan.get("status") == "active" and plan.get("version") == "full"]

            if active_plans:
                # Сортируем по дате создания (от новых к старым)
                return sorted(active_plans, key=lambda p: p.get("created_at", ""), reverse=True)[0]

            # Если нет активных полных планов, ищем согласованный краткий план
            approved_plans = [plan for plan in diet_plans if
                              plan.get("status") == "approved" and plan.get("version") == "short"]

            if approved_plans:
                # Сортируем по дате создания (от новых к старым)
                return sorted(approved_plans, key=lambda p: p.get("created_at", ""), reverse=True)[0]

            # Если нет ни активных полных, ни согласованных кратких, возвращаем последний план в ожидании согласования
            pending_plans = [plan for plan in diet_plans if plan.get("status") == "pending"]

            if pending_plans:
                # Сортируем по дате создания (от новых к старым)
                return sorted(pending_plans, key=lambda p: p.get("created_at", ""), reverse=True)[0]

            return None

        except Exception as e:
            logger.error(f"Error getting current diet: {str(e)}")
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
            weekday = get_day_of_week(self, today)

            # Получаем план на текущий день недели
            return await get_diet_for_weekday(self, user_id, weekday)

        except Exception as e:
            logger.error(f"Error getting today's diet: {str(e)}")
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

    def get_short_diet_summary(self, diet_plan: Dict[str, Any]) -> str:
        """
        Создает сводку краткой версии плана диеты для согласования

        Args:
            diet_plan: План диеты

        Returns:
            str: Отформатированная сводка плана
        """
        try:
            summary = f"*📋 ПЛАН ПИТАНИЯ НА НЕДЕЛЮ (краткая версия)*\n\n"

            # Добавляем персонализированное обращение
            personalized_note = diet_plan.get("personalized_note", "")
            if personalized_note:
                summary += f"{personalized_note}\n\n"

            # Информация о плане
            summary += "Это краткая версия плана для согласования. После вашего подтверждения я подготовлю полную версию с подробными рецептами и списком покупок.\n\n"

            # Формируем план по дням недели
            weekday_names = {
                "monday": "Понедельник",
                "tuesday": "Вторник",
                "wednesday": "Среда",
                "thursday": "Четверг",
                "friday": "Пятница",
                "saturday": "Суббота",
                "sunday": "Воскресенье"
            }

            if "daily_plans" in diet_plan:
                for weekday, day_plan in diet_plan["daily_plans"].items():
                    weekday_name = weekday_names.get(weekday, weekday.capitalize())
                    summary += f"*📅 {weekday_name}*\n"

                    # Добавляем информацию о калориях
                    if "total_calories" in day_plan:
                        summary += f"Всего калорий: {day_plan['total_calories']} ккал\n"

                    # Добавляем приемы пищи
                    if "meals" in day_plan:
                        for meal in day_plan["meals"]:
                            meal_type = translate_meal_type(meal.get("type", ""))
                            title = meal.get("title", "")
                            calories = meal.get("calories", "")
                            emoji = create_meal_emoji(meal.get("type", ""))

                            summary += f"{emoji} *{meal_type}*: {title}"
                            if calories:
                                summary += f" ({calories} ккал)"
                            summary += "\n"

                    summary += "\n"

            # Добавляем информацию о следующих шагах
            summary += "*👆 Это краткая версия плана. В полной версии будут:*\n"
            summary += "• Подробные рецепты и инструкции по приготовлению\n"
            summary += "• Информация о питательных веществах для каждого блюда\n"
            summary += "• Объяснения, почему каждое блюдо рекомендовано именно вам\n"
            summary += "• Список покупок с учетом того, что у вас уже есть\n\n"

            summary += "Пожалуйста, подтвердите план или запросите изменения."

            return format_diet_message_for_whatsapp(summary)

        except Exception as e:
            logger.error(f"Error creating short diet summary: {str(e)}")
            return "План питания создан. Пожалуйста, подтвердите его или запросите изменения."

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
                    day_date = self.get_nearest_date_for_weekday(day_key)
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
            return format_diet_message_for_whatsapp(
                "План питания создан. Напишите 'план' для получения подробной информации."), format_diet_message_for_whatsapp(
                commands_message),

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

                    # Это день недели, получаем ближайшую дату
                    day_date = self.get_nearest_date_for_weekday(day_key)
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

    def get_nearest_date_for_weekday(self, weekday_name: str) -> date:
        """
        Преобразует название дня недели в дату ближайшего такого дня недели

        Args:
            weekday_name: Название дня недели на английском (monday, tuesday и т.д.)

        Returns:
            date: Дата ближайшего дня недели
        """
        # Словарь для преобразования названия дня недели в число (0 - понедельник, 6 - воскресенье)
        weekday_mapping = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6
        }

        # Получаем текущую дату
        today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

        # Получаем номер текущего дня недели (0 - понедельник, 6 - воскресенье)
        today_weekday = today.weekday()

        # Получаем номер целевого дня недели
        target_weekday = weekday_mapping.get(weekday_name.lower())

        if target_weekday is None:
            # Если передано некорректное название дня недели, возвращаем текущую дату
            return today

        # Вычисляем разницу в днях
        days_diff = (target_weekday - today_weekday) % 7

        # Если разница 0 (тот же день) и нужен следующий такой день, добавляем 7 дней
        if days_diff == 0:
            days_diff = 7

        # Вычисляем дату ближайшего дня недели
        nearest_date = today + timedelta(days=days_diff)

        return nearest_date

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
            day_key = get_day_of_week(self, day_date)

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


def get_day_of_week(self, date_val: date = None) -> str:
    """
    Возвращает день недели для указанной даты в формате 'monday', 'tuesday' и т.д.

    Args:
        date_val: Дата (по умолчанию сегодня)

    Returns:
        str: День недели
    """
    if not date_val:
        date_val = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

    # Получаем номер дня недели (0 - понедельник, 6 - воскресенье)
    weekday = date_val.weekday()

    # Преобразуем в строковое представление
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    return days[weekday]


async def get_diet_for_weekday(self, user_id: str, weekday: str = None) -> Optional[Dict[str, Any]]:
    """
    Получает план диеты на конкретный день недели

    Args:
        user_id: ID пользователя
        weekday: День недели ('monday', 'tuesday', и т.д., по умолчанию - сегодня)

    Returns:
        Optional[Dict[str, Any]]: План на день или None, если план не найден
    """
    try:
        # Если день недели не указан, используем сегодняшний
        if not weekday:
            weekday = get_day_of_week(self)

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
        logger.error(f"Error getting diet for weekday: {str(e)}")
        return None


# Создаем экземпляр сервиса для диет
diet_service = DietService()
