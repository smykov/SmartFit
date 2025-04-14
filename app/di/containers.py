# app/di/containers.py
from dependency_injector import containers, providers

from app.db.repositories.compliance_repository import FirebaseComplianceRepository
# Репозитории
from app.db.repositories.message_repository import FirebaseMessageRepository
from app.db.repositories.reminder_repository import FirebaseReminderRepository
from app.db.repositories.user_repository import FirebaseUserRepository
from app.db.repositories.diet_plan_repository import FirebaseDietPlanRepository
from app.db.repositories.product_repository import FirebaseProductRepository
from app.db.repositories.shopping_list_repository import FirebaseShoppingListRepository
from app.db.repositories.water_entry_repository import FirebaseWaterEntryRepository
from app.db.repositories.weight_entry_repository import FirebaseWeightEntryRepository
from app.services.diet.shopping_list_manager import ShoppingListManager
from app.services.formatter.diet_formatter_service import DietFormatterService
from app.services.formatter.tracking_formatter_service import TrackingFormatterService

# Сервисы
from app.services.llm.llm_factory import LLMFactory
from app.services.diet.diet_service import DietService
from app.services.localization.localization_service import LocalizationService
from app.services.messaging.clients.twilio_whatsapp_client import TwilioWhatsAppClient
from app.services.messaging.whatsapp_service import WhatsAppService
from app.services.reminders.reminder_service import ReminderService
from app.services.tracking.tracking_service import TrackingService
from app.utils.text_splitter import TextSplitter
from app.services.messaging.message_processor_service import MessageProcessorService
from app.services.onboarding.onboarding_service import OnboardingService
from app.services.commands.command_handler_service import CommandHandlerService
from app.services.commands.command_factory import CommandFactory

# Добавляем Firebase клиент
from app.db.firebase import FirebaseClient

from config import settings


class Container(containers.DeclarativeContainer):
    """Контейнер для инъекции зависимостей приложения"""

    # Конфигурация
    config = providers.Configuration()

    # Firebase клиент (добавлен как Singleton)
    firebase_client = providers.Singleton(FirebaseClient)

    # Утилиты
    text_splitter = providers.Singleton(TextSplitter)

    # Репозитории (все используют Singleton)
    user_repository = providers.Singleton(
        FirebaseUserRepository,
        firebase_client=firebase_client
    )

    message_repository = providers.Singleton(
        FirebaseMessageRepository,
        firebase_client=firebase_client
    )

    diet_plan_repository = providers.Singleton(
        FirebaseDietPlanRepository,
        firebase_client=firebase_client
    )

    product_repository = providers.Singleton(
        FirebaseProductRepository,
        firebase_client=firebase_client
    )

    shopping_list_repository = providers.Singleton(
        FirebaseShoppingListRepository,
        firebase_client=firebase_client
    )

    # Репозиторий напоминаний
    reminder_repository = providers.Singleton(
        FirebaseReminderRepository,
        firebase_client=firebase_client
    )

    # Репозитории для трекинга
    weight_entry_repository = providers.Singleton(
        FirebaseWeightEntryRepository,
        firebase_client=firebase_client
    )

    water_entry_repository = providers.Singleton(
        FirebaseWaterEntryRepository,
        firebase_client=firebase_client
    )

    compliance_repository = providers.Singleton(
        FirebaseComplianceRepository,
        firebase_client=firebase_client
    )

    # LLM сервис
    llm_service = providers.Singleton(
        LLMFactory.get_default_llm_service
    )

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

    # Сервис трекинга
    tracking_service = providers.Singleton(
        TrackingService,
        user_repository=user_repository,
        weight_entry_repository=weight_entry_repository,
        water_entry_repository=water_entry_repository,
        compliance_repository=compliance_repository,
        localization_service=localization_service
    )

    # Сервис диет
    diet_service = providers.Singleton(
        DietService,
        user_repository=user_repository,
        message_service=whatsapp_service,
        localization_service=localization_service,
        diet_plan_repository=diet_plan_repository,
        product_repository=product_repository,
        shopping_list_repository=shopping_list_repository,
        llm_service=llm_service
    )

    # Сервис обработки команд
    command_handler_service = providers.Singleton(
        CommandHandlerService,
        user_repository=user_repository,
        message_service=whatsapp_service,
        diet_service=diet_service,
        tracking_service=tracking_service,
        localization_service=localization_service
    )

    # Сервис онбординга
    onboarding_service = providers.Singleton(
        OnboardingService,
        user_repository=user_repository,
        message_service=whatsapp_service,
        diet_service=diet_service,
        command_handler_service=command_handler_service,
        localization_service=localization_service
    )

    # Фабрика команд
    command_factory = providers.Factory(
        CommandFactory,
        dependencies=providers.Dict({
            "user_repository": user_repository,
            "message_service": whatsapp_service,
            "diet_service": diet_service,
            "tracking_service": tracking_service,
            "localization_service": localization_service,
            "llm_service": llm_service
        })
    )

    # Форматтеры
    diet_formatter_service = providers.Singleton(
        DietFormatterService,
        localization_service=localization_service
    )

    tracking_formatter_service = providers.Singleton(
        TrackingFormatterService,
        localization_service=localization_service
    )
    shopping_list_manager = providers.Singleton(
        ShoppingListManager,
        llm_service=llm_service,
        diet_plan_repository=diet_plan_repository,
        shopping_list_repository=shopping_list_repository,
        localization_service=localization_service  # Добавить этот параметр
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

    # Сервис напоминаний
    reminder_service = providers.Singleton(
        ReminderService,
        message_service=whatsapp_service,
        user_repository=user_repository,
        reminder_repository=reminder_repository,
        tracking_service=tracking_service,
        diet_service=diet_service,
        localization_service=localization_service  # Добавляем сервис локализации
    )
