from dependency_injector import containers, providers

from app.db.repositories.message_repository import FirebaseMessageRepository
from app.db.repositories.user_repository import FirebaseUserRepository
from app.services.diet import DietService
from app.services.messaging.clients.twilio_whatsapp_client import TwilioWhatsAppClient
from app.services.messaging.whatsapp_service import WhatsAppService
from app.services.tracking.tracking_service import TrackingService
from app.services.utils.text_splitter import TextSplitter
from app.services.messaging.message_processor_service import MessageProcessorService
from app.services.onboarding.onboarding_service import OnboardingService
from app.services.commands.command_handler_service import CommandHandlerService
from app.services.commands.command_factory import CommandFactory
from config import settings


class Container(containers.DeclarativeContainer):
    """Контейнер для инъекции зависимостей приложения"""

    # Конфигурация
    config = providers.Configuration()

    # Утилиты
    text_splitter = providers.Singleton(TextSplitter)

    # Репозитории
    user_repository = providers.Factory(FirebaseUserRepository)
    message_repository = providers.Singleton(FirebaseMessageRepository)

    # Клиенты API
    message_client = providers.Singleton(
        TwilioWhatsAppClient,
        account_sid=settings.TWILIO_ACCOUNT_SID,
        auth_token=settings.TWILIO_AUTH_TOKEN,
        from_phone=settings.TWILIO_PHONE_NUMBER
    )

    # Сервисы
    whatsapp_service = providers.Singleton(
        WhatsAppService,
        message_client=message_client,
        message_repository=message_repository,
        text_splitter=text_splitter,
        from_phone_number=settings.TWILIO_PHONE_NUMBER,
        retry_interval_seconds=getattr(settings, "WHATSAPP_RETRY_INTERVAL_SECONDS", 300),
        max_message_size=getattr(settings, "WHATSAPP_MAX_MESSAGE_SIZE", 1500),
        max_message_age_hours=getattr(settings, "WHATSAPP_MAX_MESSAGE_AGE_HOURS", 72)
    )

    # Сервис обработки команд
    command_handler_service = providers.Singleton(
        CommandHandlerService,
        user_repository=user_repository,
        message_service=whatsapp_service,
    )

    # Сервис онбординга
    onboarding_service = providers.Singleton(
        OnboardingService,
        user_repository=user_repository,
        message_service=whatsapp_service
    )

    # Сервис диет
    diet_service = providers.Singleton(
        DietService,
        user_repository=user_repository
    )

    # Сервис трекинга
    tracking_service = providers.Singleton(
        TrackingService
    )

    # Фабрика команд
    command_factory = providers.Factory(
        CommandFactory,
        dependencies=providers.Dict({
            "user_repository": user_repository,
            "message_service": whatsapp_service,
            "diet_service": diet_service,
            "tracking_service": tracking_service
        })
    )

    # Сервис обработки сообщений
    message_processor_service = providers.Singleton(
        MessageProcessorService,
        user_repository=user_repository,
        message_repository=message_repository,
        message_service=whatsapp_service,
        onboarding_service=onboarding_service,
        diet_service=diet_service,
        tracking_service=tracking_service,
        command_factory=command_factory
    )