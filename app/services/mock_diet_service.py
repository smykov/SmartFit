"""
Заглушка для генерации планов диеты без использования OpenAI API.
Используется для тестирования и разработки без расходования квоты API.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
import pytz
import uuid
import random

from config import settings

logger = logging.getLogger(__name__)


class MockDietService:
    """Сервис-заглушка для генерации планов диеты"""

    async def generate_diet_plan(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Генерирует план диеты для пользователя (заглушка)

        Args:
            user_id: ID пользователя
            days: Количество дней для плана

        Returns:
            Dict[str, Any]: План диеты
        """
        try:
            logger.info(f"Запущена заглушка генерации диеты для пользователя {user_id}")

            # Корректное получение информации о пользователе
            user_data = None
            if isinstance(user_id, str):
                # Если передан ID как строка
                from app.db.firebase import firebase_client
                user_data = firebase_client.get_document("users", user_id)
            elif isinstance(user_id, dict) and "id" in user_id:
                # Если передан словарь с данными пользователя
                user_data = user_id
                user_id = user_data["id"]

            if not user_data:
                return {"error": "Пользователь не найден"}

            # Генерируем план на указанное количество дней
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()
            start_date = today.isoformat()
            end_date = (today + timedelta(days=days - 1)).isoformat()

            # Примеры местных продуктов и блюд Гватемалы
            local_foods = [
                "Frijoles negros", "Maíz", "Arroz", "Aguacate", "Plátano", "Pollo",
                "Carne de res", "Tomate", "Cebolla", "Chile", "Queso fresco", "Huevos",
                "Papaya", "Piña", "Tortillas de maíz", "Chicharrones", "Mango"
            ]

            # Создаем ежедневные планы
            daily_plans = {}
            for i in range(days):
                day_date = (today + timedelta(days=i)).isoformat()

                # Создаем приемы пищи
                meals = [
                    self._generate_meal("breakfast", local_foods),
                    self._generate_meal("lunch", local_foods),
                    self._generate_meal("dinner", local_foods),
                    self._generate_meal("snack", local_foods)
                ]

                # Рассчитываем дневные тотальные значения
                total_calories = sum(meal["calories"] for meal in meals)
                total_proteins = sum(meal["proteins"] for meal in meals)
                total_fats = sum(meal["fats"] for meal in meals)
                total_carbs = sum(meal["carbs"] for meal in meals)
                total_price = sum(meal["estimated_price"] for meal in meals)

                # Создаем план на день
                daily_plans[day_date] = {
                    "date": day_date,
                    "meals": meals,
                    "total_calories": total_calories,
                    "total_proteins": total_proteins,
                    "total_fats": total_fats,
                    "total_carbs": total_carbs,
                    "estimated_total_price": total_price,
                    "tips": self._get_random_tip()
                }

            # Формируем финальный план
            diet_plan = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date,
                "daily_plans": daily_plans,
                "general_recommendations": self._get_general_recommendations(user_data),
                "estimated_weekly_price": sum(day["estimated_total_price"] for day in daily_plans.values()),
                "created_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
                "ai_generated": True,
                "dietitian_approved": False
            }

            # Сохраняем план в базу данных
            from app.db.firebase import firebase_client
            plan_id = firebase_client.add_document("diet_plans", diet_plan)

            if plan_id:
                diet_plan["id"] = plan_id
                logger.info(f"Успешно создан тестовый план диеты с ID {plan_id}")
            else:
                logger.error("Не удалось сохранить план диеты в базе данных")

            return diet_plan

        except Exception as e:
            logger.error(f"Ошибка при генерации тестового плана диеты: {str(e)}")
            return {"error": str(e)}

    async def generate_shopping_list(self, diet_plan_id: str) -> Dict[str, Any]:
        """
        Создает список покупок на основе плана диеты (заглушка)

        Args:
            diet_plan_id: ID плана диеты

        Returns:
            Dict[str, Any]: Список покупок
        """
        try:
            logger.info(f"Запущена заглушка генерации списка покупок для плана {diet_plan_id}")

            # Получаем план диеты, если передан его ID
            from app.db.firebase import firebase_client
            diet_plan = None

            if isinstance(diet_plan_id, str):
                diet_plan = firebase_client.get_document("diet_plans", diet_plan_id)
            else:
                # Если передан сам план диеты
                diet_plan = diet_plan_id

            if not diet_plan:
                return {"error": "План диеты не найден"}

            # Собираем все продукты из плана
            all_products = []
            for day_data in diet_plan.get("daily_plans", {}).values():
                for meal in day_data.get("meals", []):
                    for product in meal.get("products", []):
                        all_products.append(product)

            # Объединяем одинаковые продукты
            combined_products = {}
            for product in all_products:
                name = product.get("name", "")
                quantity = product.get("quantity", 0)
                unit = product.get("unit", "")

                if name not in combined_products:
                    combined_products[name] = {
                        "name": name,
                        "quantity": quantity,
                        "unit": unit,
                        "estimated_price": random.uniform(5, 30)
                    }
                else:
                    combined_products[name]["quantity"] += quantity

            # Создаем список покупок
            shopping_list = {
                "id": str(uuid.uuid4()),
                "user_id": diet_plan.get("user_id", ""),
                "diet_plan_id": diet_plan_id if isinstance(diet_plan_id, str) else diet_plan.get("id", ""),
                "items": list(combined_products.values()),
                "created_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
                "updated_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
                "total_estimated_price": sum(item["estimated_price"] for item in combined_products.values())
            }

            # Сохраняем список в базу данных
            list_id = firebase_client.add_document("shopping_lists", shopping_list)

            if list_id:
                shopping_list["id"] = list_id
                logger.info(f"Успешно создан тестовый список покупок с ID {list_id}")
            else:
                logger.error("Не удалось сохранить список покупок в базе данных")

            return shopping_list

        except Exception as e:
            logger.error(f"Ошибка при генерации тестового списка покупок: {str(e)}")
            return {"error": str(e)}

    def get_diet_summary(self, diet_plan: Dict[str, Any]) -> Tuple[str, str]:
        """
        Создает сводку плана диеты для отправки пользователю

        Args:
            diet_plan: План диеты

        Returns:
            str: Текстовая сводка плана
        """
        commands_message = "*📱 Команды для взаимодействия с планом:*\n"
        commands_message += "• Напиши 'полный план' для просмотра плана на всю неделю\n"
        commands_message += "• Напиши 'план на сегодня' или 'меню на сегодня' для детального плана на сегодня\n"
        commands_message += "• Напиши 'список покупок' для получения списка продуктов\n"
        commands_message += "• Напиши 'выполнено завтрак/обед/ужин/перекус' для отметки о соблюдении плана\n"
        try:

            summary = "📋 *План питания* (тестовый режим)\n\n"

            # Общие рекомендации
            if "general_recommendations" in diet_plan and diet_plan["general_recommendations"]:
                summary += f"📝 *Общие рекомендации:*\n{diet_plan['general_recommendations']}\n\n"

            # Информация о стоимости
            if "estimated_weekly_price" in diet_plan and diet_plan["estimated_weekly_price"]:
                summary += f"💰 *Примерная стоимость:* {diet_plan['estimated_weekly_price']:.2f} кетцалей в неделю\n\n"

            # Пример меню на первый день
            if "daily_plans" in diet_plan and diet_plan["daily_plans"]:
                first_day_key = next(iter(diet_plan["daily_plans"]))
                first_day = diet_plan["daily_plans"][first_day_key]

                summary += f"🍽️ *Пример меню на день:*\n"

                if "meals" in first_day:
                    for meal in first_day["meals"]:
                        meal_type = meal.get("type", "").capitalize()
                        title = meal.get("title", "")
                        calories = meal.get("calories", "")

                        summary += f"- {meal_type}: {title}"
                        if calories:
                            summary += f" (~{calories} ккал)"
                        summary += "\n"

            summary += "\nℹ️ *Примечание:* Сейчас используется тестовый режим генерации диет. Реальный план будет доступен после обновления API ключа."

            return summary, commands_message

        except Exception as e:
            logger.error(f"Ошибка при создании сводки диеты: {str(e)}")
            return "План питания создан в тестовом режиме. Напишите 'план' для деталей.", commands_message

    def _generate_meal(self, meal_type: str, local_foods: List[str]) -> Dict[str, Any]:
        """Генерирует один прием пищи"""

        # Случайные названия блюд по типу приема пищи
        meal_titles = {
            "breakfast": [
                "Huevos rancheros con tortillas", "Desayuno chapín", "Plátanos fritos con crema",
                "Panqueques de maíz", "Huevos revueltos con frijoles"
            ],
            "lunch": [
                "Pepián de pollo", "Carne asada con arroz", "Jocon de pollo", "Pollo en crema",
                "Hilachas con arroz", "Caldo de res"
            ],
            "dinner": [
                "Frijoles con queso y tortillas", "Enchiladas guatemaltecas", "Pollo a la plancha",
                "Sopa de verduras", "Tacos de res"
            ],
            "snack": [
                "Frutas tropicales", "Tortillas con aguacate", "Plátano con miel",
                "Tostadas con frijol", "Atol de elote"
            ]
        }

        # Выбираем случайное название блюда
        title = random.choice(meal_titles.get(meal_type, ["Plato típico"]))

        # Выбираем случайные продукты для блюда
        num_products = random.randint(3, 6)
        products = []
        for _ in range(num_products):
            product = {
                "name": random.choice(local_foods),
                "quantity": round(random.uniform(50, 500), 0),
                "unit": random.choice(["g", "ml", "шт", "порция"])
            }
            products.append(product)

        # Генерируем случайные значения для пищевой ценности
        calories = round(random.uniform(200, 800), 0)
        proteins = round(random.uniform(10, 40), 1)
        fats = round(random.uniform(5, 30), 1)
        carbs = round(random.uniform(20, 80), 1)
        price = round(random.uniform(10, 50), 2)

        return {
            "type": meal_type,
            "title": title,
            "description": f"Традиционное блюдо гватемальской кухни на основе {products[0]['name']}.",
            "products": products,
            "preparation": "Смешайте все ингредиенты и готовьте на среднем огне 15-20 минут.",
            "calories": calories,
            "proteins": proteins,
            "fats": fats,
            "carbs": carbs,
            "estimated_price": price,
            "local_products_percentage": random.randint(60, 90)
        }

    def _get_random_tip(self) -> str:
        """Возвращает случайный совет по питанию"""
        tips = [
            "Пейте больше воды в течение дня для улучшения метаболизма.",
            "Старайтесь есть больше свежих фруктов и овощей.",
            "Уменьшите потребление соли и сахара для общего оздоровления.",
            "Не пропускайте приемы пищи, это поможет контролировать аппетит.",
            "Добавляйте белок в каждый прием пищи для поддержания мышечной массы.",
            "Выбирайте цельнозерновые продукты вместо рафинированных.",
            "Следите за размером порций, даже при здоровом питании.",
            "Ешьте медленно и слушайте сигналы своего тела о насыщении."
        ]
        return random.choice(tips)

    def _get_general_recommendations(self, user_data: Dict[str, Any]) -> str:
        """Создает общие рекомендации на основе данных пользователя"""

        gender = user_data.get("gender", "other")
        age = user_data.get("age", 30)
        weight_goal = user_data.get("weight_goal", "lose")
        activity_level = user_data.get("activity_level", "moderate")

        recs = "Рекомендации для вашего плана питания:\n\n"

        # Рекомендации по весу
        if weight_goal == "lose":
            recs += "• Для снижения веса важно создать умеренный дефицит калорий. Этот план создан с учетом ежедневного дефицита в 300-500 калорий.\n"
        elif weight_goal == "gain":
            recs += "• Для набора веса план питания включает избыток калорий. Старайтесь также включать силовые тренировки для набора мышечной массы.\n"
        else:
            recs += "• Для поддержания веса важно баланс калорий. План составлен так, чтобы вы получали адекватное количество калорий для вашего уровня активности.\n"

        # Рекомендации по активности
        if activity_level in ["sedentary", "light"]:
            recs += "• При низкой физической активности рекомендуется выполнять хотя бы 30 минут ходьбы в день для поддержания здоровья.\n"
        elif activity_level in ["moderate"]:
            recs += "• Ваш уровень активности способствует хорошему метаболизму. Старайтесь поддерживать регулярность физической активности.\n"
        else:
            recs += "• При высокой физической активности важно обеспечивать организм достаточным количеством белка и углеводов для восстановления.\n"

        # Общие рекомендации
        recs += "• Пейте не менее 2 литров воды в день.\n"
        recs += "• Старайтесь есть небольшими порциями каждые 3-4 часа.\n"
        recs += "• Включайте в рацион разнообразные фрукты и овощи для получения необходимых витаминов и минералов.\n"
        recs += "• Отдавайте предпочтение местным продуктам Гватемалы - они более доступны, свежи и питательны."

        return recs


# Создаем экземпляр сервиса-заглушки
mock_diet_service = MockDietService()