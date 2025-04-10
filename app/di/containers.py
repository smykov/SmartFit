from dependency_injector import containers, providers

# Репозитории
from app.db.repositories.message_repository import FirebaseMessageRepository
from app.db.repositories.user_repository import FirebaseUserRepository
from app.db.repositories.diet_plan_repository import FirebaseDietPlanRepository
from app.db.repositories.product_repository import FirebaseProductRepository
from app.db.repositories.shopping_list_repository import FirebaseShoppingListRepository

from app.services.diet.diet_service import DietService
from app.services.localization.localization_service import LocalizationService
from app.services.messaging.clients.twilio_whatsapp_client import TwilioWhatsAppClient
from app.services.messaging.whatsapp_service import WhatsAppService
from app.services.tracking.tracking_service import TrackingService
from app.utils.text_splitter import TextSplitter
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
    user_repository = providers.Singleton(FirebaseUserRepository)
    message_repository = providers.Singleton(FirebaseMessageRepository)
    diet_plan_repository = providers.Singleton(FirebaseDietPlanRepository)
    product_repository = providers.Singleton(FirebaseProductRepository)
    shopping_list_repository = providers.Singleton(FirebaseShoppingListRepository)

    # Сервис локализации
    localization_service = providers.Singleton(
        LocalizationService,
        user_repository=user_repository
    )

    # Клиенты API
    message_client = providers.Singleton(
        TwilioWhatsAppClient,
        account_sid=settings.TWILIO_ACCOUNT_SID,
        auth_token=settings.TWILIO_AUTH_TOKEN,
        from_phone=settings.TWILIO_PHONE_NUMBER,
        localization_service=localization_service
    )

    # Сервисы
    whatsapp_service = providers.Singleton(
        WhatsAppService,
        message_client=message_client,
        message_repository=message_repository,
        localization_service=localization_service,
        text_splitter=text_splitter,
        from_phone_number=settings.TWILIO_PHONE_NUMBER,
        retry_interval_seconds=getattr(settings, "WHATSAPP_RETRY_INTERVAL_SECONDS", 300),
        max_message_size=getattr(settings, "WHATSAPP_MAX_MESSAGE_SIZE", 1500),
        max_message_age_hours=getattr(settings, "WHATSAPP_MAX_MESSAGE_AGE_HOURS", 72)
    )

    # Сервис диет
    diet_service = providers.Singleton(
        DietService,
        user_repository=user_repository,
        message_service=whatsapp_service,
        localization_service=localization_service,
        diet_plan_repository=diet_plan_repository,
        product_repository=product_repository,
        shopping_list_repository=shopping_list_repository
    )

    # Сервис трекинга
    tracking_service = providers.Singleton(
        TrackingService
    )
    # Сервис обработки команд
    command_handler_service = providers.Singleton(
        CommandHandlerService,
        user_repository=user_repository,
        message_service=whatsapp_service,
        diet_service=diet_service,
        tracking_service=tracking_service,
    )

    # Сервис онбординга
    onboarding_service = providers.Singleton(
        OnboardingService,
        user_repository=user_repository,
        message_service=whatsapp_service,
        diet_service=diet_service,
        command_handler_service=command_handler_service
    )

    # Фабрика команд
    command_factory = providers.Factory(
        CommandFactory,
        dependencies=providers.Dict({
            "user_repository": user_repository,
            "message_service": whatsapp_service,
            "diet_service": diet_service,
            "tracking_service": tracking_service,
            "localization_service": localization_service
        })
    )

    # Сервис обработки сообщений
    message_processor_service = providers.Singleton(
        MessageProcessorService,
        user_repository=user_repository,
        message_repository=message_repository,
        message_service=whatsapp_service,
        localization_service=localization_service,
        onboarding_service=onboarding_service,
        diet_service=diet_service,
        tracking_service=tracking_service,
        command_factory=command_factory
    )
