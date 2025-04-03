import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Form, BackgroundTasks, Query
from fastapi.responses import JSONResponse

from app.services.whatsapp_service import whatsapp_service
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Вебхук для входящих сообщений WhatsApp
    
    Этот эндпоинт обрабатывает входящие сообщения от WhatsApp API
    через Twilio и перенаправляет их на обработку в сервис WhatsApp.
    """
    try:
        # Получаем данные из запроса
        form_data = await request.form()
        
        # Преобразуем данные в словарь
        message_data = {key: value for key, value in form_data.items()}
        
        # Проверяем, есть ли необходимые поля
        if "From" not in message_data or "Body" not in message_data:
            logger.error("Неверный формат данных в вебхуке WhatsApp")
            return JSONResponse(
                status_code=400,
                content={"message": "Invalid request format"}
            )
        
        # Обрабатываем сообщение
        result = await whatsapp_service.process_incoming_message(message_data)
        
        # Возвращаем ответ для Twilio (пустой TwiML ответ)
        return JSONResponse(
            content={
                "success": True,
                "message": "Message received",
                "result": result
            }
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука WhatsApp: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Error processing webhook: {str(e)}"}
        )

@router.post("/send")
async def send_whatsapp_message(
    phone_number: str = Form(...),
    message: str = Form(...)
):
    """
    Отправляет сообщение через WhatsApp
    
    Args:
        phone_number: Номер телефона получателя
        message: Текст сообщения
    """
    try:
        # Проверяем формат номера телефона
        if not phone_number or len(phone_number) < 10:
            raise HTTPException(status_code=400, detail="Invalid phone number")
        
        # Отправляем сообщение
        result = await whatsapp_service.send_message(phone_number, message)
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to send message")
        
        return {"success": True, "message": "Message sent successfully"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения WhatsApp: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

@router.post("/send-template")
async def send_template_message(
    phone_number: str = Form(...),
    template_name: str = Form(...),
    parameters: Optional[str] = Form(None)
):
    """
    Отправляет шаблонное сообщение через WhatsApp
    
    Args:
        phone_number: Номер телефона получателя
        template_name: Название шаблона
        parameters: JSON-строка с параметрами для шаблона
    """
    try:
        # Проверяем формат номера телефона
        if not phone_number or len(phone_number) < 10:
            raise HTTPException(status_code=400, detail="Invalid phone number")
        
        # Парсим параметры, если они есть
        params = None
        if parameters:
            try:
                params = json.loads(parameters)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid parameters format")
        
        # Отправляем шаблонное сообщение
        result = await whatsapp_service.send_template_message(
            phone_number,
            template_name,
            params
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to send template message")
        
        return {"success": True, "message": "Template message sent successfully"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Ошибка при отправке шаблонного сообщения WhatsApp: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending template message: {str(e)}")


@router.post("/admin/send-reminders")
async def send_reminders_manually(
        background_tasks: BackgroundTasks,
        admin_key: str = Query(..., description="Ключ администратора для подтверждения операции"),
        reminder_type: str = Query(..., description="Тип напоминания (onboarding, tracking, all)")
):
    """Вручную запускает отправку напоминаний"""
    try:
        # Проверяем ключ администратора
        if admin_key != settings.ADMIN_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid admin key")

        # Запускаем отправку напоминаний в фоновом режиме
        if reminder_type == "onboarding" or reminder_type == "all":
            background_tasks.add_task(whatsapp_service.send_onboarding_reminders)

        if reminder_type == "tracking" or reminder_type == "all":
            background_tasks.add_task(whatsapp_service.send_tracking_reminders)

        return {"success": True, "message": f"Started sending {reminder_type} reminders"}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in manual reminder sending: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")