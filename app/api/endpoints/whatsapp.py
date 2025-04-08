from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging
import json

from app.services.messaging.message_processor_service import MessageProcessorService
from app.services.messaging.whatsapp_service import WhatsAppService
from app.di.container import container

router = APIRouter()
logger = logging.getLogger(__name__)


# Определяем зависимости для инъекции в эндпоинты
def get_message_processor_service():
    return container.message_processor_service()


def get_whatsapp_service():
    return container.whatsapp_service()


@router.post("/webhook")
async def whatsapp_webhook(
        request: Request,
        message_processor: MessageProcessorService = Depends(get_message_processor_service)
):
    """
    Вебхук для входящих сообщений WhatsApp
    """
    try:
        # Получаем данные из запроса
        form_data = await request.form()

        # Преобразуем данные в словарь
        message_data = {key: value for key, value in form_data.items()}

        # Обрабатываем сообщение
        result = await message_processor.process_incoming_message(message_data)

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
        message: str = Form(...),
        context: Optional[str] = Form(None),
        whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """
    Отправляет сообщение через WhatsApp

    Args:
        phone_number: Номер телефона получателя
        message: Текст сообщения
        context: JSON-строка с контекстом сообщения (опционально)
    """
    try:
        # Проверяем формат номера телефона
        if not phone_number or len(phone_number) < 10:
            raise HTTPException(status_code=400, detail="Invalid phone number")

        # Преобразуем строку контекста в словарь, если она предоставлена
        context_dict = None
        if context:
            try:
                context_dict = json.loads(context)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid context format")

        # Отправляем сообщение
        result = await whatsapp_service.send_message(phone_number, message, context_dict)

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
        user_id: Optional[str] = None,
        parameters: Optional[str] = Form(None),
        whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """
    Отправляет шаблонное сообщение через WhatsApp

    Args:
        phone_number: Номер телефона получателя
        template_name: Название шаблона
        user_id: ID пользователя для определения языка (если None, используется язык по умолчанию)
        parameters: JSON-строка с параметрами для шаблона
        whatsapp_service:
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

        if not user_id:
            user_id = None

        # Отправляем шаблонное сообщение
        result = await whatsapp_service.send_template_message(
            phone_number,
            template_name,
            user_id,
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
