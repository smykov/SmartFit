# app/api/endpoints/messaging.py
import asyncio

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
import logging

from app.services.messaging.message_processor_service import MessageProcessorService
from app.di.container import container

router = APIRouter()
logger = logging.getLogger(__name__)


# Определяем зависимости для инъекции в эндпоинты
def get_message_processor_service():
    return container.message_processor_service()


@router.post("/webhook/{messenger_type}")
async def messaging_webhook(
        messenger_type: str,
        request: Request,
        message_processor: MessageProcessorService = Depends(get_message_processor_service)
):
    """
    Универсальный вебхук для входящих сообщений

    Args:
        messenger_type: Тип мессенджера (whatsapp, telegram, etc.)
        request: HTTP запрос
    """
    try:
        # Получаем данные из запроса
        if messenger_type.lower() == "whatsapp":
            data = await request.form()
            data = {key: value for key, value in data.items()}
        else:
            data = await request.json()

        logger.info(f"Получен вебхук от {messenger_type}: {data}")

        # Извлекаем message_id для предварительной проверки
        message_id = None
        if messenger_type.lower() == "whatsapp":
            message_id = data.get("MessageSid", "") or data.get("SmsMessageSid", "")
        else:  # telegram
            if "message" in data:
                message_id = str(data.get("message", {}).get("message_id", ""))

        # Проверяем, обрабатывается ли уже это сообщение
        if message_id and await message_processor.is_message_being_processed(message_id):
            return JSONResponse(
                content={
                    "success": True,
                    "message": "Message is already being processed",
                }
            )

        # ВАЖНО: Сразу отправляем положительный ответ вебхуку
        # Запускаем обработку сообщения в фоновом режиме
        asyncio.create_task(message_processor.process_incoming_message(data, messenger_type.lower()))

        return JSONResponse(
            content={
                "success": True,
                "message": "Message received and processing started",
            }
        )
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Error processing webhook: {str(e)}"}
        )