import logging
from datetime import datetime
from typing import Dict, Any

import pytz
from fastapi import APIRouter, HTTPException, Path, Query, BackgroundTasks

from app.db.firebase import firebase_client
from app.services.diet.diet_service import DietService as diet_service
from app.services.messaging.whatsapp_service import WhatsAppService as whatsapp_service
from app.services.localization import localization_service as localization_service
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{user_id}/generate")
async def generate_diet_plan(
        background_tasks: BackgroundTasks,
        user_id: str = Path(..., description="ID пользователя"),
        days: int = Query(1, description="Количество дней для плана"),
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
        # Получаем текущий план через сервис
        diet_plan = await diet_service.get_current_diet(user_id)

        if not diet_plan:
            return {"message": "No current diet plan found"}

        return diet_plan

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


@router.get("/{user_id}/day/{date}")
async def get_diet_for_day(
        user_id: str = Path(..., description="ID пользователя"),
        date_str: str = Path(..., description="Дата в формате YYYY-MM-DD")
):
    """Получает план диеты на конкретный день"""
    try:
        # Вместо проверки конкретной даты, используем новую логику
        if date_str == "today" or date_str == datetime.now(pytz.timezone(settings.TIMEZONE)).date().isoformat():
            # Получаем план на сегодня с учетом дня недели
            day_plan = await diet_service.get_today_diet(user_id)
        else:
            # Если нужна конкретная дата, преобразуем её в день недели
            try:
                day_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                weekday = diet_service.get_day_of_week(day_date)
                day_plan = await diet_service.get_diet_for_weekday(user_id, weekday)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        if not day_plan:
            return {"message": "No diet plan found for the specified date"}

        return day_plan

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving diet plan for day: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{user_id}/summary")
async def get_diet_summary(
        user_id: str = Path(..., description="ID пользователя"),
        send_whatsapp: bool = Query(False, description="Отправить сводку в WhatsApp")
):
    """Получает сводку текущего плана диеты пользователя"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        lang = user.get("language")
        phone_number = user["phone_number"]
        # Получаем текущий план через сервис
        diet_plan = await diet_service.get_current_diet(user_id)

        if not diet_plan:
            return {"message": "No current diet plan found"}

        # Получаем сводку через сервис
        summary = diet_service.get_diet_summary(diet_plan)
        commands = localization_service.get_message("commands_message", lang)
        # Отправляем сводку в WhatsApp, если запрошено
        if send_whatsapp and "phone_number" in user:
            await whatsapp_service.send_message(phone_number, summary)
            await whatsapp_service.send_message(phone_number, commands)

        return {
            "message": "Diet summary generated",
            "user_id": user_id,
            "summary": summary,
            "commands": commands,
            "whatsapp_sent": send_whatsapp and "phone_number" in user
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error generating diet summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{user_id}/full-plan")
async def get_full_diet_plan(
        user_id: str = Path(..., description="ID пользователя"),
        send_whatsapp: bool = Query(False, description="Отправить полный план в WhatsApp")
):
    """Получает полный план диеты пользователя"""
    try:
        # Проверяем существование пользователя
        user = firebase_client.get_document("users", user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Получаем текущий план через сервис
        diet_plan = await diet_service.get_current_diet(user_id)

        if not diet_plan:
            return {"message": "No current diet plan found"}

        # Получаем полный план через сервис
        full_plan_messages = diet_service.get_full_diet_plan(diet_plan)

        # Отправляем план в WhatsApp, если запрошено
        if send_whatsapp and "phone_number" in user:
            await whatsapp_service.send_messages(user["phone_number"], full_plan_messages)

        return {
            "message": "Full diet plan generated",
            "user_id": user_id,
            "plan_messages": full_plan_messages,
            "whatsapp_sent": send_whatsapp and "phone_number" in user
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error generating full diet plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/{plan_id}/shopping-list")
async def generate_shopping_list(
        plan_id: str = Path(..., description="ID плана диеты"),
        send_whatsapp: bool = Query(False, description="Отправить список покупок в WhatsApp")
):
    """Генерирует список покупок на основе плана диеты"""
    try:
        # Проверяем существование плана
        plan = firebase_client.get_document("diet_plans", plan_id)

        if not plan:
            raise HTTPException(status_code=404, detail="Diet plan not found")

        # Генерируем список покупок через сервис
        shopping_list = await diet_service.generate_shopping_list(plan_id)

        if not shopping_list or "error" in shopping_list:
            error_msg = shopping_list.get("error",
                                          "Unknown error") if shopping_list else "Failed to generate shopping list"
            raise HTTPException(status_code=500, detail=error_msg)

        # Форматируем список покупок для WhatsApp
        if send_whatsapp:
            user_id = plan.get("user_id")
            if user_id:
                user = firebase_client.get_document("users", user_id)
                if user and "phone_number" in user:
                    formatted_list = diet_service.format_shopping_list(shopping_list)
                    await whatsapp_service.send_message(user["phone_number"], formatted_list)

        return shopping_list

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

        # Генерируем план диеты через сервис
        diet_plan = await diet_service.generate_diet_plan(user_id, days)

        if not diet_plan or "error" in diet_plan:
            error_msg = diet_plan.get("error", "Unknown error") if diet_plan else "Failed to generate diet plan"
            logger.error(f"Failed to generate diet plan: {error_msg}")

            if notify_user and "phone_number" in user_data:
                await whatsapp_service.send_message(
                    user_data["phone_number"],
                    "К сожалению, не удалось создать план диеты. Попробуйте позже или обратитесь в поддержку."
                )
            return

        logger.info(f"Diet plan successfully generated with ID {diet_plan.get('id', 'unknown')}")

        # Уведомляем пользователя, если нужно
        if notify_user and "phone_number" in user_data:
            # Получаем и отправляем сводку диеты
            summary, commands = diet_service.get_diet_summary(diet_plan)
            await whatsapp_service.send_message(user_data["phone_number"], summary)
            await whatsapp_service.send_message(user_data["phone_number"], commands)

            # Генерируем и отправляем список покупок
            try:
                shopping_list = await diet_service.generate_shopping_list(diet_plan["id"])
                if shopping_list and "error" not in shopping_list:
                    formatted_list = diet_service.format_shopping_list(shopping_list)
                    await whatsapp_service.send_message(user_data["phone_number"], formatted_list)
            except Exception as e:
                logger.error(f"Error generating shopping list for notification: {str(e)}")

    except Exception as e:
        logger.error(f"Error in diet plan generation task: {str(e)}")

        # Уведомляем пользователя об ошибке
        if notify_user and "phone_number" in user_data:
            await whatsapp_service.send_message(
                user_data["phone_number"],
                "К сожалению, произошла ошибка при создании плана диеты. Попробуйте позже или обратитесь в поддержку."
            )
