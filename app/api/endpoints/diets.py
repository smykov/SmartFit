from fastapi import APIRouter, Depends, HTTPException, Path, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, date, timedelta
import pytz
import json

from config import settings
from app.db.firebase import firebase_client
from app.services.openai_service import openai_service
from app.services.whatsapp_service import whatsapp_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{user_id}/generate")
async def generate_diet_plan(
    background_tasks: BackgroundTasks,
    user_id: str = Path(..., description="ID пользователя"),
    days: int = Query(7, description="Количество дней для плана"),
    notify_user: bool = Query(True, description="Уведомить пользователя о создании плана")
):
    """Генерирует план диеты для пользователя"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Добавляем задачу генерации диеты в фоновый режим
        background_tasks.add_task(
            _generate_diet_plan_task,
            user_id=user_id,
            user_data=user,
            days=days,
            notify_user=notify_user
        )
        
        return {
            "message": "Diet plan generation started",
            "user_id": user_id,
            "days": days
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error starting diet plan generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/{user_id}/current")
async def get_current_diet_plan(user_id: str = Path(..., description="ID пользователя")):
    """Получает текущий план диеты пользователя"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
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
        
        if not current_plan:
            return {"message": "No current diet plan found"}
        
        return current_plan
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving current diet plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/{user_id}/all")
async def get_all_diet_plans(user_id: str = Path(..., description="ID пользователя")):
    """Получает все планы диеты пользователя"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Получаем все планы диеты пользователя
        diet_plans = firebase_client.query_documents("diet_plans", "user_id", "==", user_id)
        
        return diet_plans
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving all diet plans: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.delete("/{plan_id}")
async def delete_diet_plan(plan_id: str = Path(..., description="ID плана диеты")):
    """Удаляет план диеты"""
    try:
        # Проверяем существование плана
        plan = firebase_client.get_document("diet_plans", plan_id)
        
        if not plan:
            raise HTTPException(status_code=404, detail="Diet plan not found")
        
        # Удаляем план
        success = firebase_client.delete_document("diet_plans", plan_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete diet plan")
        
        return {"message": "Diet plan successfully deleted"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting diet plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/{plan_id}/shopping-list")
async def generate_shopping_list(
    plan_id: str = Path(..., description="ID плана диеты")
):
    """Генерирует список покупок на основе плана диеты"""
    try:
        # Проверяем существование плана
        plan = firebase_client.get_document("diet_plans", plan_id)
        
        if not plan:
            raise HTTPException(status_code=404, detail="Diet plan not found")
        
        # Генерируем список покупок
        shopping_list = await openai_service.create_shopping_list(plan)
        
        if not shopping_list:
            raise HTTPException(status_code=500, detail="Failed to generate shopping list")
        
        # Сохраняем список покупок
        shopping_list_data = {
            "user_id": plan.get("user_id"),
            "diet_plan_id": plan_id,
            "items": shopping_list,
            "created_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
            "updated_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat(),
            "total_estimated_price": sum([item.get("estimated_price", 0) for item in shopping_list if item.get("estimated_price")])
        }
        
        list_id = firebase_client.add_document("shopping_lists", shopping_list_data)
        
        if not list_id:
            raise HTTPException(status_code=500, detail="Failed to save shopping list")
        
        # Добавляем ID в данные
        shopping_list_data["id"] = list_id
        
        return shopping_list_data
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error generating shopping list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/{user_id}/shopping-lists")
async def get_user_shopping_lists(user_id: str = Path(..., description="ID пользователя")):
    """Получает все списки покупок пользователя"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Получаем все списки покупок пользователя
        shopping_lists = firebase_client.query_documents("shopping_lists", "user_id", "==", user_id)
        
        return shopping_lists
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving shopping lists: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# --- Вспомогательные функции ---

async def _generate_diet_plan_task(user_id: str, user_data: Dict[str, Any], days: int, notify_user: bool):
    """Фоновая задача для генерации плана диеты"""
    try:
        logger.info(f"Starting diet plan generation for user {user_id}")
        
        # Получаем список доступных продуктов
        products = firebase_client.get_all_documents("products")
        
        # Генерируем план диеты
        diet_plan = await openai_service.generate_diet_plan(user_data, days, products)
        
        if not diet_plan or "error" in diet_plan:
            logger.error(f"Failed to generate diet plan: {diet_plan.get('error', 'Unknown error')}")
            
            if notify_user and "phone_number" in user_data:
                await whatsapp_service.send_message(
                    user_data["phone_number"],
                    "К сожалению, не удалось создать план диеты. Попробуйте позже или обратитесь в поддержку."
                )
            return
        
        # Добавляем ID пользователя, если его нет
        if "user_id" not in diet_plan:
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
            
            if notify_user and "phone_number" in user_data:
                await whatsapp_service.send_message(
                    user_data["phone_number"],
                    "К сожалению, не удалось сохранить план диеты. Попробуйте позже или обратитесь в поддержку."
                )
            return
        
        logger.info(f"Diet plan successfully generated and saved with ID {plan_id}")
        
        # Уведомляем пользователя, если нужно
        if notify_user and "phone_number" in user_data:
            await whatsapp_service.send_template_message(
                user_data["phone_number"],
                "diet_created"
            )
            
            # Отправляем краткое описание плана
            summary = _create_diet_plan_summary(diet_plan)
            await whatsapp_service.send_message(
                user_data["phone_number"],
                summary
            )
        
    except Exception as e:
        logger.error(f"Error in diet plan generation task: {str(e)}")
        
        # Уведомляем пользователя об ошибке
        if notify_user and "phone_number" in user_data:
            await whatsapp_service.send_message(
                user_data["phone_number"],
                "К сожалению, произошла ошибка при создании плана диеты. Попробуйте позже или обратитесь в поддержку."
            )

def _create_diet_plan_summary(diet_plan: Dict[str, Any]) -> str:
    """Создает краткое описание плана диеты для отправки пользователю"""
    try:
        summary = "📋 Краткое описание плана питания:\n\n"
        
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
            
            summary += f"🍽️ *Пример меню на {first_day.get('date', 'первый день')}:*\n"
            
            if "meals" in first_day:
                for meal in first_day["meals"]:
                    meal_type = meal.get("type", "").capitalize()
                    title = meal.get("title", "")
                    calories = meal.get("calories", "")
                    
                    summary += f"- {meal_type}: {title}"
                    if calories:
                        summary += f" (~{calories} ккал)"
                    summary += "\n"
        
        summary += "\nПолный план доступен через меню. Напишите 'план' для получения подробной информации."
        
        return summary
        
    except Exception as e:
        logger.error(f"Error creating diet plan summary: {str(e)}")
        return "План питания создан. Напишите 'план' для получения подробной информации."
