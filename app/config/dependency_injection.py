# Добавить в существующий файл конфигурации DI
from app.db.interfaces.user_repository_interface import IUserRepository
from app.db.repositories.user_repository import FirebaseUserRepository
from app.db.interfaces.message_repository_interface import IMessageRepository
from app.db.repositories.message_repository import FirebaseMessageRepository
from app.services.messaging.clients.twilio_whatsapp_client import TwilioWhatsAppClient
from app.services.messaging.interfaces.message_client_interface import IMessageClient
from app.services.messaging.whatsapp_service import WhatsAppService
from app.utils.text_splitter import TextSplitter
from config import settings


# Регистрация зависимостей для репозиториев
def register_repository_dependencies(container):
    # Репозиторий пользователей
    container.register(
        IUserRepository,
        FirebaseUserRepository
    )

    # Остальные регистрации репозиториев...


# В основной регистрации зависимостей
def register_dependencies(container):
    # Регистрируем репозитории
    register_repository_dependencies(container)

    # Регистрируем WhatsApp-зависимости
    register_whatsapp_dependencies(container)

# Регистрация зависимостей для WhatsApp сервиса
def register_whatsapp_dependencies(container):
    # Репозиторий сообщений
    container.register(
        IMessageRepository,
        FirebaseMessageRepository
    )

    # Клиент Twilio для WhatsApp
    container.register(
        IMessageClient,
        lambda: TwilioWhatsAppClient(
            account_sid=settings.TWILIO_ACCOUNT_SID,
            auth_token=settings.TWILIO_AUTH_TOKEN,
            from_phone=settings.TWILIO_PHONE_NUMBER
        )
    )

    # Утилита для разбиения текста
    container.register(
        TextSplitter,
        TextSplitter
    )

    # WhatsApp сервис
    container.register(
        WhatsAppService,
        lambda: WhatsAppService(
            message_client=container.resolve(IMessageClient),
            message_repository=container.resolve(IMessageRepository),
            text_splitter=container.resolve(TextSplitter),
            from_phone_number=settings.TWILIO_PHONE_NUMBER,
            retry_interval_seconds=settings.WHATSAPP_RETRY_INTERVAL_SECONDS,
            max_message_size=settings.WHATSAPP_MAX_MESSAGE_SIZE,
            max_message_age_hours=settings.WHATSAPP_MAX_MESSAGE_AGE_HOURS
        )
    )