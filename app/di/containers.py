# app/di/containers.py
from dependency_injector import containers, providers
import os

# Добавляем Firebase клиент
from app.db.firebase import FirebaseClient
# Firebase репозитории
from app.db.repositories.compliance_repository import FirebaseComplianceRepository
from app.db.repositories.message_repository import FirebaseMessageRepository
from app.db.repositories.reminder_repository import FirebaseReminderRepository
from app.db.repositories.user_repository import FirebaseUserRepository
from app.db.repositories.diet_plan_repository import FirebaseDietPlanRepository
from app.db.repositories.product_repository import FirebaseProductRepository
from app.db.repositories.shopping_list_repository import FirebaseShoppingListRepository
from app.db.repositories.water_entry_repository import FirebaseWaterEntryRepository
from app.db.repositories.weight_entry_repository import FirebaseWeightEntryRepository

# Добавляем Postgres клиент
from app.db.postgres import PostgresClient
# PostgreSQL репозитории
from app.db.repositories.postgres.user_repository import PostgresUserRepository
from app.db.repositories.postgres.message_repository import PostgresMessageRepository
from app.db.repositories.postgres.diet_plan_repository import PostgresDietPlanRepository
from app.db.repositories.postgres.product_repository import PostgresProductRepository
from app.db.repositories.postgres.shopping_list_repository import PostgresShoppingListRepository
from app.db.repositories.postgres.weight_entry_repository import PostgresWeightEntryRepository
from app.db.repositories.postgres.water_entry_repository import PostgresWaterEntryRepository
from app.db.repositories.postgres.compliance_repository import PostgresComplianceRepository
from app.db.repositories.postgres.reminder_repository import PostgresReminderRepository

# Сервисы
from app.services.diet.shopping_list_manager import ShoppingListManager
from app.services.formatter.diet_formatter_service import DietFormatterService
from app.services.formatter.tracking_formatter_service import TrackingFormatterService
from app.services.llm.llm_factory import LLMFactory
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
from app.services.reminders.reminder_service import ReminderService
from app.services.reminders.reminder_service_interface import IReminderService

from config import settings


class Container(containers.DeclarativeContainer):
    """Контейнер для инъекции зависимостей приложения"""

    # Конфигурация
    config = providers.Configuration()

    # Определяем, какую БД использовать по умолчанию (из настроек или переменных окружения)
    db_engine = providers.Singleton(
        lambda: os.getenv('DB_ENGINE', settings.DB_ENGINE)
    )

    # Firebase клиент (добавлен как Singleton)
    firebase_client = providers.Singleton(FirebaseClient)

    # PostgreSQL клиент
    postgres_client = providers.Singleton(PostgresClient)

    # Утилиты
    text_splitter = providers.Singleton(TextSplitter)

    # Репозитории (все используют Singleton)
    user_repository = providers.Factory(
        lambda engine, firebase, postgres:
        FirebaseUserRepository(firebase) if engine == "firebase" else
        PostgresUserRepository(postgres),
        engine=db_engine,
        firebase=firebase_client,
        postgres=postgres_client
    )

    message_repository = providers.Factory(
        lambda engine, firebase, postgres:
        FirebaseMessageRepository(firebase) if engine == "firebase" else
        PostgresMessageRepository(postgres),
        engine=db_engine,
        firebase=firebase_client,
        postgres=postgres_client
    )
    # TODO Дописать для всех репозиториев

    diet_plan_repository = providers.Factory(
        lambda engine, firebase, postgres:
        FirebaseDietPlanRepository(firebase) if engine == "firebase" else
        PostgresDietPlanRepository(postgres),
        engine=db_engine,
        firebase=firebase_client,
        postgres=postgres_client
    )

    product_repository = providers.Factory(
        lambda engine, firebase, postgres:
        FirebaseProductRepository(firebase) if engine == "firebase" else
        PostgresProductRepository(postgres),
        engine=db_engine,
        firebase=firebase_client,
        postgres=postgres_client
    )

    shopping_list_repository = providers.Factory(
        lambda engine, firebase, postgres:
        FirebaseShoppingListRepository(firebase) if engine == "firebase" else
        PostgresShoppingListRepository(postgres),
        engine=db_engine,
        firebase=firebase_client,
        postgres=postgres_client
    )

    weight_entry_repository = providers.Factory(
        lambda engine, firebase, postgres:
        FirebaseWeightEntryRepository(firebase) if engine == "firebase" else
        PostgresWeightEntryRepository(postgres),
        engine=db_engine,
        firebase=firebase_client,
        postgres=postgres_client
    )

    water_entry_repository = providers.Factory(
        lambda engine, firebase, postgres:
        FirebaseWaterEntryRepository(firebase) if engine == "firebase" else
        PostgresWaterEntryRepository(postgres),
        engine=db_engine,
        firebase=firebase_client,
        postgres=postgres_client
    )

    compliance_repository = providers.Factory(
        lambda engine, firebase, postgres:
        FirebaseComplianceRepository(firebase) if engine == "firebase" else
        PostgresComplianceRepository(postgres),
        engine=db_engine,
        firebase=firebase_client,
        postgres=postgres_client
    )

    reminder_repository = providers.Factory(
        lambda engine, firebase, postgres:
        FirebaseReminderRepository(firebase) if engine == "firebase" else
        PostgresReminderRepository(postgres),
        engine=db_engine,
        firebase=firebase_client,
        postgres=postgres_client
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
        dependencies=providers.Dict({
            "user_repository": user_repository,
            "message_service": whatsapp_service,
            "diet_service": diet_service,
            "tracking_service": tracking_service,
            "localization_service": localization_service,
        })
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
            "tracking_formatter_service": tracking_formatter_service,
            "localization_service": localization_service,
            "llm_service": llm_service
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

    # Сервис напоминаний
    reminder_service = providers.Singleton(
        ReminderService,
        message_service=whatsapp_service,
        user_repository=user_repository,
        reminder_repository=reminder_repository,
        tracking_service=tracking_service,
        diet_service=diet_service,
        localization_service=localization_service
    )

    # Зарегистрировать интерфейс
    reminder_service_interface = providers.Factory(
        lambda reminder_service: reminder_service,
        reminder_service=reminder_service
    )
