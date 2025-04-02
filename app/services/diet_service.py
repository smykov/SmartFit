import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import pytz
import json

from config import settings
from app.db.firebase import firebase_client
from app.services.openai_service import openai_service
from app.models.diet import DietPlan, DailyDiet, Meal, Product, ShoppingList, ShoppingListItem

logger = logging.getLogger(__name__)

class DietService:
    """Сервис для работы с диетами"""
    
    async def generate_diet_plan(self, user_id: str, days: int = 7) -> Optional[Dict[str, Any]]:
        """
        Генерирует план диеты для пользователя
        
        Args:
            user_id: ID пользователя
            days: Количество дней для плана
            
        Returns:
            Optional[Dict[str, Any]]: План диеты или None в случае ошибки
        """
        try:
            # Получаем данные пользователя
            user_data = firebase_client.get_document("users", user_id)
            
            if not user_data:
                logger.error(f"User {user_id} not found")
                return None
            
            # Получаем список доступных продуктов
            products = firebase_client.get_all_documents("products")
            
            # Генерируем план диеты через OpenAI
            diet_plan = await openai_service.generate_diet_plan(user_data, days, products)
            
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
                diet_plan["end_date"] = (start_date + timedelta(days=days-1)).isoformat()
            
            # Сохраняем план в базу данных
            plan_id = firebase_client.add_document("diet_plans", diet_plan)
            
            if not plan_id:
                logger.error("Failed to save diet plan to database")
                return None
            
            # Добавляем ID в план
            diet_plan["id"] = plan_id
            
            return diet_plan
            
        except Exception as e:
            logger.error(f"Error generating diet plan: {str(e)}")
            return None
    
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
    
    async def generate_shopping_list(self, diet_plan_id: str) -> Optional[List[Dict[str, Any]]]:
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
            
            # Генерируем список покупок через OpenAI
            shopping_list = await openai_service.create_shopping_list(diet_plan)
            
            if not shopping_list:
                logger.error("Failed to generate shopping list")
                return None
            
            # Сохраняем список покупок
            shopping_list_data = {
                "user_id": diet_plan.get("user_id"),
                "diet_plan_id": diet_plan_id,
                "items": shopping_list,
                "created_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
                "updated_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
                "total_estimated_price": sum([item.get("estimated_price", 0) for item in shopping_list if item.get("estimated_price")])
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
            return None
    
    def get_diet_summary(self, diet_plan: Dict[str, Any]) -> str:
        """
        Создает сводку плана диеты для отправки пользователю
        
        Args:
            diet_plan: План диеты
            
        Returns:
            str: Текстовая сводка плана
        """
        try:
            summary = "📋 *План питания*\n\n"
            
            # Общие рекомендации
            if "general_recommendations" in diet_plan and diet_plan["general_recommendations"]:
                summary += f"📝 *Общие рекомендации:*\n{diet_plan['general_recommendations']}\n\n"
            
            # Информация о стоимости
            if "estimated_weekly_price" in diet_plan and diet_plan["estimated_weekly_price"]:
                summary += f"💰 *Примерная стоимость:* {diet_plan['estimated_weekly_price']} кетцалей в неделю\n\n"
            
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
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating diet summary: {str(e)}")
            return "План питания создан. Напишите 'план' для получения подробной информации."

# Создаем экземпляр сервиса для диет
diet_service = DietService()
