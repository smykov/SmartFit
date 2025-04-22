from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
import json
import logging

from app.services.messaging.message_processor_service import MessageProcessorService
from app.services.messaging.telegram_service import TelegramService
from app.di.container import container

router = APIRouter()
logger = logging.getLogger(__name__)


# Определяем зависимости для инъекции в эндпоинты
def get_message_processor_service():
    return container.message_processor_service()


def get_telegram_service():
    return container.telegram_service()


@router.post("/webhook")
async def telegram_webhook(
        request: Request,
        message_processor: MessageProcessorService = Depends(get_message_processor_service)
):
    """Вебхук для входящих сообщений Telegram"""
    try:
        # Получаем данные из запроса
        data = await request.json()

        # Обрабатываем сообщение через процессор
        result = await message_processor.process_incoming_message(data, "telegram")

        return JSONResponse(
            content={
                "success": True,
                "message": "Message received",
                "result": result
            }
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука Telegram: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Error processing webhook: {str(e)}"}
        )


@router.post("/send")
async def send_telegram_message(
        chat_id: str,
        message: str,
        context: Optional[str] = None,
        telegram_service: TelegramService = Depends(get_telegram_service)
):
    """
    Отправляет сообщение через Telegram

    Args:
        chat_id: ID чата получателя
        message: Текст сообщения
        context: JSON-строка с контекстом сообщения (опционально)
    """
    try:
        # Проверяем формат ID чата
        if not chat_id:
            raise HTTPException(status_code=400, detail="Invalid chat ID")

        # Преобразуем строку контекста в словарь, если предоставлена
        context_dict = None
        if context:
            try:
                context_dict = json.loads(context)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid context format")

        # Отправляем сообщение
        result = await telegram_service.send_message(chat_id, message, context_dict)

        if not result:
            raise HTTPException(status_code=500, detail="Failed to send message")

        return {"success": True, "message": "Message sent successfully"}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения Telegram: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")