from fastapi import APIRouter, Depends, HTTPException, Path, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, date, timedelta
import pytz

from config import settings
from app.db.firebase import firebase_client
from app.models.tracking import WeightEntry, WaterIntakeEntry, DailyTrackingStatus, WeightGoalProgress
from app.services.whatsapp_service import whatsapp_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{user_id}/weight")
async def record_weight(
    weight_data: WeightEntry,
    user_id: str = Path(..., description="ID пользователя")
):
    """Записывает вес пользователя"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Получаем текущую дату в формате ISO
        today = datetime.now(pytz.timezone(settings.TIMEZONE)).date().isoformat()
        
        # Обновляем текущий вес пользователя
        firebase_client.update_document("users", user_id, {"current_weight": weight_data.weight})
        
        # Добавляем запись в историю веса
        weight_history = user.get("weight_history", {})
        weight_history[today] = weight_data.weight
        
        firebase_client.update_document("users", user_id, {"weight_history": weight_history})
        
        # Создаем запись в коллекции weight_entries для аналитики (опционально)
        entry_data = {
            "user_id": user_id,
            "weight": weight_data.weight,
            "date": today,
            "notes": weight_data.notes
        }
        
        firebase_client.add_document("weight_entries", entry_data)
        
        # Проверяем прогресс к цели, если она установлена
        if "target_weight" in user and user["target_weight"]:
            progress = _calculate_weight_progress(user, weight_data.weight)
            
            # Если прогресс существенный, можно отправить уведомление
            if _check_significant_progress(progress):
                await _notify_weight_milestone(user, progress)
        
        return {"message": "Weight recorded successfully", "weight": weight_data.weight, "date": today}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error recording weight: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/{user_id}/water")
async def record_water_intake(
    water_data: WaterIntakeEntry,
    user_id: str = Path(..., description="ID пользователя")
):
    """Записывает потребление воды"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Получаем текущую дату в формате ISO
        today = datetime.now(pytz.timezone(settings.TIMEZONE)).date().isoformat()
        
        # Добавляем запись в историю потребления воды
        water_history = user.get("water_intake_history", {})
        
        # Если на сегодня уже есть запись, добавляем к ней
        if today in water_history:
            water_history[today] += water_data.amount
        else:
            water_history[today] = water_data.amount
        
        firebase_client.update_document("users", user_id, {"water_intake_history": water_history})
        
        # Создаем запись в коллекции water_entries для аналитики (опционально)
        entry_data = {
            "user_id": user_id,
            "amount": water_data.amount,
            "date": today,
            "time": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
        }
        
        firebase_client.add_document("water_entries", entry_data)
        
        # Проверяем достижение цели по воде
        daily_goal = 2000  # 2 литра (в мл) по умолчанию
        if water_history[today] >= daily_goal and water_history[today] - water_data.amount < daily_goal:
            await _notify_water_goal_reached(user)
        
        return {
            "message": "Water intake recorded successfully", 
            "amount": water_data.amount, 
            "total_today": water_history[today],
            "date": today
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error recording water intake: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/{user_id}/weight-history")
async def get_weight_history(
    user_id: str = Path(..., description="ID пользователя"),
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)")
):
    """Получает историю веса пользователя"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Получаем историю веса
        weight_history = user.get("weight_history", {})
        
        # Если указаны даты, фильтруем по ним
        if start_date or end_date:
            filtered_history = {}
            
            start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else date(1900, 1, 1)
            end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else date(2100, 12, 31)
            
            for date_str, weight in weight_history.items():
                entry_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if start <= entry_date <= end:
                    filtered_history[date_str] = weight
            
            return {"user_id": user_id, "weight_history": filtered_history}
        
        return {"user_id": user_id, "weight_history": weight_history}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving weight history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/{user_id}/water-history")
async def get_water_history(
    user_id: str = Path(..., description="ID пользователя"),
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)")
):
    """Получает историю потребления воды"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Получаем историю потребления воды
        water_history = user.get("water_intake_history", {})
        
        # Если указаны даты, фильтруем по ним
        if start_date or end_date:
            filtered_history = {}
            
            start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else date(1900, 1, 1)
            end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else date(2100, 12, 31)
            
            for date_str, amount in water_history.items():
                entry_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if start <= entry_date <= end:
                    filtered_history[date_str] = amount
            
            return {"user_id": user_id, "water_history": filtered_history}
        
        return {"user_id": user_id, "water_history": water_history}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving water history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/{user_id}/status/today")
async def get_today_status(user_id: str = Path(..., description="ID пользователя")):
    """Получает статус трекинга на сегодня"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Получаем текущую дату в формате ISO
        today = datetime.now(pytz.timezone(settings.TIMEZONE)).date().isoformat()
        
        # Проверяем, записан ли сегодня вес
        weight_history = user.get("weight_history", {})
        weight_recorded = today in weight_history
        
        # Получаем сегодняшнее потребление воды
        water_history = user.get("water_intake_history", {})
        current_water_intake = water_history.get(today, 0)
        
        # Целевое потребление воды (2 литра по умолчанию)
        water_goal = 2000  # в мл
        
        # Рассчитываем процент выполнения цели по воде
        water_percentage = min(100, (current_water_intake / water_goal) * 100) if water_goal > 0 else 0
        
        # Создаем объект статуса
        status = {
            "user_id": user_id,
            "date": today,
            "weight_recorded": weight_recorded,
            "current_water_intake": current_water_intake,
            "water_goal": water_goal,
            "water_percentage": water_percentage
        }
        
        return status
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving today's tracking status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/{user_id}/progress")
async def get_weight_progress(user_id: str = Path(..., description="ID пользователя")):
    """Получает прогресс в достижении цели по весу"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Проверяем наличие целевого веса
        if "target_weight" not in user or not user["target_weight"]:
            raise HTTPException(status_code=400, detail="Target weight not set")
        
        # Проверяем наличие текущего веса
        if "current_weight" not in user or not user["current_weight"]:
            raise HTTPException(status_code=400, detail="Current weight not set")
        
        # Получаем историю веса
        weight_history = user.get("weight_history", {})
        
        # Определяем начальный вес
        start_weight = None
        if weight_history:
            # Находим самую раннюю запись
            earliest_date = min(weight_history.keys())
            start_weight = weight_history[earliest_date]
        
        if not start_weight:
            # Если нет истории, используем текущий вес как начальный
            start_weight = user["current_weight"]
        
        # Рассчитываем прогресс
        progress = _calculate_weight_progress(user, user["current_weight"], start_weight)
        
        return progress.dict()
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error calculating weight progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/{user_id}/reminders/setup")
async def setup_reminders(
    background_tasks: BackgroundTasks,
    user_id: str = Path(..., description="ID пользователя"),
    weight_reminder: bool = Query(True, description="Напоминание о весе"),
    water_reminder: bool = Query(True, description="Напоминание о воде"),
    weekly_report: bool = Query(True, description="Еженедельный отчет")
):
    """Настраивает напоминания для пользователя"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Сохраняем настройки напоминаний
        reminders = {
            "weight_reminder": weight_reminder,
            "water_reminder": water_reminder,
            "weekly_report": weekly_report,
            "updated_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
        }
        
        firebase_client.update_document("users", user_id, {"reminders": reminders})
        
        # В реальном проекте здесь бы настраивались планировщики задач
        # Для MVP просто возвращаем успешный результат
        
        return {
            "message": "Reminders setup successfully",
            "reminders": reminders
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error setting up reminders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# --- Вспомогательные функции ---

def _calculate_weight_progress(user: Dict[str, Any], current_weight: float, start_weight: float = None) -> WeightGoalProgress:
    """Рассчитывает прогресс в достижении цели по весу"""
    
    # Если начальный вес не указан, берем из пользователя
    if not start_weight and "weight_history" in user and user["weight_history"]:
        # Находим самую раннюю запись
        earliest_date = min(user["weight_history"].keys())
        start_weight = user["weight_history"][earliest_date]
    
    # Если всё еще нет начального веса, используем текущий
    if not start_weight:
        start_weight = current_weight
    
    target_weight = user.get("target_weight", current_weight)
    
    return WeightGoalProgress.calculate(
        user_id=user.get("id", ""),
        start_weight=start_weight,
        current_weight=current_weight,
        target_weight=target_weight
    )

def _check_significant_progress(progress: WeightGoalProgress) -> bool:
    """Проверяет, достигнут ли значительный прогресс"""
    # Например, каждые 10% прогресса или 5% от начального веса
    return (progress.goal_completion_percentage % 10 < 1 and progress.goal_completion_percentage > 0) or \
           (abs(progress.weight_change_percentage) >= 5)

async def _notify_weight_milestone(user: Dict[str, Any], progress: WeightGoalProgress):
    """Отправляет уведомление о достижении вехи прогресса по весу"""
    if "phone_number" not in user:
        return
    
    # Форматируем сообщение
    message = f"🎉 Поздравляем! Ты достиг новой вехи в своем прогрессе!\n\n"
    
    if progress.total_weight_change < 0:
        message += f"✅ Ты уже сбросил {abs(progress.total_weight_change):.1f} кг "
    else:
        message += f"✅ Ты уже набрал {progress.total_weight_change:.1f} кг "
    
    message += f"({abs(progress.weight_change_percentage):.1f}% от начального веса)\n\n"
    
    message += f"📊 Ты выполнил {progress.goal_completion_percentage:.1f}% своей цели!\n"
    message += f"🎯 Осталось еще {abs(progress.remaining_to_goal):.1f} кг до целевого веса {progress.target_weight} кг.\n\n"
    
    message += "Продолжай в том же духе! 💪"
    
    await whatsapp_service.send_message(user["phone_number"], message)

async def _notify_water_goal_reached(user: Dict[str, Any]):
    """Отправляет уведомление о достижении цели по воде"""
    if "phone_number" not in user:
        return
    
    message = "💧 Поздравляем! Ты достиг сегодняшней цели по потреблению воды!\n\n"
    message += "Продолжай пить воду в течение дня для поддержания гидратации. Это помогает с чувством сытости и общим здоровьем."
    
    await whatsapp_service.send_message(user["phone_number"], message)
