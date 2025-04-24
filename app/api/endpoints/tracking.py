import logging
from datetime import datetime, date
from typing import Dict, Any, Optional

import pytz
from app.services.tracking.tracking_service import tracking_service
from fastapi import APIRouter, HTTPException, Path, Query, BackgroundTasks

from app.db.firebase import firebase_client
from app.models.tracking import (
    WeightEntry, WaterIntakeEntry, WeightGoalProgress,
    MealCompliance
)
from app.services.whatsapp_service import whatsapp_service
from config import settings

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

        # Записываем вес
        result = await tracking_service.record_weight(user_id, weight_data.weight, weight_data.notes)

        if not result:
            raise HTTPException(status_code=500, detail="Failed to record weight")

        return {"message": "Weight recorded successfully", "weight": weight_data.weight}

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

        # Записываем потребление воды
        result = await tracking_service.record_water_intake(user_id, water_data.amount)

        if not result:
            raise HTTPException(status_code=500, detail="Failed to record water intake")

        return {
            "message": "Water intake recorded successfully",
            "amount": water_data.amount
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
        # Получаем статус через сервис
        status = await tracking_service.get_daily_status(user_id)

        if not status:
            raise HTTPException(status_code=404, detail="Failed to get status data")

        return status

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving today's tracking status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{user_id}/weekly-report")
async def generate_weekly_report(
        user_id: str = Path(..., description="ID пользователя"),
        send_whatsapp: bool = Query(False, description="Отправить отчет в WhatsApp")
):
    """Генерирует еженедельный отчет о прогрессе"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Генерируем отчет
        report = await tracking_service.generate_weekly_report(user_id)

        if not report:
            raise HTTPException(status_code=500, detail="Failed to generate weekly report")

        # Отправляем отчет в WhatsApp, если запрошено
        if send_whatsapp and "phone_number" in user:
            await whatsapp_service.send_message(user["phone_number"], report)

        return {
            "message": "Weekly report generated",
            "user_id": user_id,
            "report": report,
            "whatsapp_sent": send_whatsapp and "phone_number" in user
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error generating weekly report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/{user_id}/meal-compliance")
async def record_meal_compliance(
        compliance_data: MealCompliance,
        user_id: str = Path(..., description="ID пользователя")
):
    """Записывает соблюдение режима питания"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Если дата не указана, используем текущую
        if not compliance_data.date:
            compliance_data.date = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

        # Если не указано время создания, используем текущее
        if not compliance_data.created_at:
            compliance_data.created_at = datetime.now(pytz.timezone(settings.TIMEZONE))

        # Записываем соблюдение
        result = await tracking_service.record_meal_compliance(
            user_id,
            compliance_data.date,
            compliance_data.meal_type,
            compliance_data.status,
            compliance_data.notes,
            compliance_data.alternative_meal
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to record meal compliance")

        return {
            "message": "Meal compliance recorded successfully",
            "meal_type": compliance_data.meal_type,
            "status": compliance_data.status
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error recording meal compliance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{user_id}/diet-compliance")
async def get_diet_compliance(
        user_id: str = Path(..., description="ID пользователя"),
        date_str: Optional[str] = Query(None, description="Дата (YYYY-MM-DD)")
):
    """Получает статистику соблюдения плана питания"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Если дата не указана, используем текущую
        target_date = None
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        # Получаем статистику соблюдения
        compliance_data = await tracking_service.get_diet_compliance(user_id, target_date)

        if not compliance_data:
            return {"message": "No compliance data found", "user_id": user_id, "date": date_str}

        return compliance_data

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting diet compliance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{user_id}/compliance-history")
async def get_compliance_history(
        user_id: str = Path(..., description="ID пользователя"),
        start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
        end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)")
):
    """Получает историю соблюдения плана питания"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Преобразуем строки дат в объекты date, если они указаны
        start = None
        end = None

        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")

        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

        # Запрашиваем все записи соблюдения для пользователя
        compliances = firebase_client.query_documents("daily_compliance", "user_id", "==", user_id)

        # Фильтруем по датам, если они указаны
        if start or end:
            filtered_compliances = []

            for compliance in compliances:
                try:
                    compliance_date = datetime.strptime(compliance.get("date", "2000-01-01"), "%Y-%m-%d").date()

                    if (not start or compliance_date >= start) and (not end or compliance_date <= end):
                        filtered_compliances.append(compliance)
                except ValueError:
                    # Пропускаем записи с некорректной датой
                    continue

            compliances = filtered_compliances

        # Сортируем по дате (от новых к старым)
        compliances = sorted(compliances, key=lambda x: x.get("date", "2000-01-01"), reverse=True)

        return {
            "user_id": user_id,
            "history": compliances
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting compliance history: {str(e)}")
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

        await firebase_client.update_document("users", user_id, {"reminders": reminders})

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

def _calculate_weight_progress(user: Dict[str, Any], current_weight: float,
                               start_weight: float = None) -> WeightGoalProgress:
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
