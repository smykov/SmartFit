# app/api/endpoints/reminders.py

from fastapi import APIRouter, Depends, HTTPException
from dependency_injector.wiring import inject, Provide
from app.di.containers import Container
from app.services.reminders.reminder_service_interface import IReminderService
from typing import Dict, Any

router = APIRouter(
    prefix="/reminders",
    tags=["reminders"],
    responses={404: {"description": "Not found"}},
)


@router.post("/trigger/{reminder_type}")
@inject
async def trigger_reminder(
        reminder_type: str,
        reminder_service: IReminderService = Depends(Provide[Container.reminder_service_interface])
) -> Dict[str, Any]:
    """
    Ручной запуск конкретного типа напоминаний для тестирования

    Args:
        reminder_type: Тип напоминания (onboarding, plan_approval, tracking)

    Returns:
        Dict[str, Any]: Результат операции
    """
    if not reminder_service:
        raise HTTPException(status_code=503, detail="Reminder service not available")

    try:
        if reminder_type == "onboarding":
            await reminder_service.send_onboarding_reminders()
            return {"status": "success", "message": "Onboarding reminders triggered"}
        elif reminder_type == "plan_approval":
            await reminder_service.send_plan_approval_reminders()
            return {"status": "success", "message": "Plan approval reminders triggered"}
        elif reminder_type == "tracking":
            await reminder_service.send_tracking_reminders()
            return {"status": "success", "message": "Tracking reminders triggered"}
        else:
            raise HTTPException(status_code=400, detail=f"Unknown reminder type: {reminder_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering reminders: {str(e)}")


@router.get("/status")
@inject
async def reminder_status(
        reminder_service: IReminderService = Depends(Provide[Container.reminder_service_interface])
) -> Dict[str, Any]:
    """
    Проверка статуса сервиса напоминаний

    Returns:
        Dict[str, Any]: Статус сервиса напоминаний
    """
    if not reminder_service:
        raise HTTPException(status_code=503, detail="Reminder service not available")

    # Проверяем, есть ли метод log_reminder_status
    if hasattr(reminder_service, 'log_reminder_status'):
        return reminder_service.log_reminder_status()

    return {
        "status": "active",
        "service_type": type(reminder_service).__name__
    }