import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.messaging.command_extraction.command_executor import CommandExecutor
from app.services.messaging.command_extraction.llm_command_extractor import LLMCommandExtractor
from app.services.messaging.command_extraction.logging_command_extractor import LoggingCommandExtractor


@pytest.fixture
def services(firebase_repositories, llm_service_mock, whatsapp_service_mock, localization_service_mock):
    """Создает набор сервисов для тестирования."""
    from app.services.diet.diet_service import DietService
    from app.services.tracking.tracking_service import TrackingService
    from app.services.formatter.diet_formatter_service import DietFormatterService
    from app.services.formatter.tracking_formatter_service import TrackingFormatterService
    from app.services.onboarding.onboarding_service import OnboardingService
    from app.services.commands.command_handler_service import CommandHandlerService
    from app.services.commands.command_factory import CommandFactory
    from app.services.reminders.reminder_service import ReminderService
    from app.services.messaging.message_processor_service import MessageProcessorService
    messenger_registry = AsyncMock()
    user_identity_service = AsyncMock()
    # Создаем форматтеры
    diet_formatter_service = DietFormatterService(localization_service_mock)
    tracking_formatter_service = TrackingFormatterService(localization_service_mock)

    # Создаем сервис диет
    diet_service = DietService(
        user_repository=firebase_repositories["user_repository"],
        messenger_service=whatsapp_service_mock,
        localization_service=localization_service_mock,
        diet_plan_repository=firebase_repositories["diet_plan_repository"],
        product_repository=firebase_repositories["product_repository"],
        shopping_list_repository=firebase_repositories["shopping_list_repository"],
        llm_service=llm_service_mock
    )
    # Создаем сервис трекинга
    tracking_service = TrackingService(
        user_repository=firebase_repositories["user_repository"],
        diet_service=diet_service,
        weight_entry_repository=firebase_repositories["weight_entry_repository"],
        water_entry_repository=firebase_repositories["water_entry_repository"],
        compliance_repository=firebase_repositories["compliance_repository"],
        localization_service=localization_service_mock
    )

    # Создаем обработчик команд
    command_factory = CommandFactory({
        "user_repository": firebase_repositories["user_repository"],
        "messenger_service": whatsapp_service_mock,
        "diet_service": diet_service,
        "tracking_service": tracking_service,
        "tracking_formatter_service": tracking_formatter_service,
        "localization_service": localization_service_mock,
        "llm_service": llm_service_mock
    })

    command_handler_service = CommandHandlerService({
        "user_repository": firebase_repositories["user_repository"],
        "messenger_service": whatsapp_service_mock,
        "diet_service": diet_service,
        "tracking_service": tracking_service,
        "localization_service": localization_service_mock
    })

    # Создаем сервис онбординга
    onboarding_service = OnboardingService(
        user_repository=firebase_repositories["user_repository"],
        messenger_service=whatsapp_service_mock,
        diet_service=diet_service,
        command_handler_service=command_handler_service,
        localization_service=localization_service_mock
    )

    llm_command_extractor = LLMCommandExtractor(
        llm_service=llm_service_mock,
        user_repository=firebase_repositories["user_repository"],
        diet_plan_repository=firebase_repositories["diet_plan_repository"],
        min_confidence=0.7
    )
    command_extractor = LoggingCommandExtractor(
        command_extractor=llm_command_extractor
    )

    command_executor = CommandExecutor(
        command_factory=command_factory,
        messenger_service=whatsapp_service_mock,
        diet_service=diet_service,
        user_repository=firebase_repositories["user_repository"],
        localization_service=localization_service_mock
    )
    # Создаем сервис процессора сообщений
    message_processor_service = MessageProcessorService(
        messenger_registry=messenger_registry,
        user_identity_service=user_identity_service,
        user_repository=firebase_repositories["user_repository"],
        message_repository=firebase_repositories["message_repository"],
        messenger_service=whatsapp_service_mock,
        localization_service=localization_service_mock,
        onboarding_service=onboarding_service,
        diet_service=diet_service,
        tracking_service=tracking_service,
        command_factory=command_factory,
        command_extractor=command_extractor,
        command_executor=command_executor
    )

    # Создаем сервис напоминаний
    reminder_service = ReminderService(
        messenger_service=whatsapp_service_mock,
        user_repository=firebase_repositories["user_repository"],
        reminder_repository=firebase_repositories["reminder_repository"],
        tracking_service=tracking_service,
        diet_service=diet_service,
        localization_service=localization_service_mock
    )

    return {
        "diet_formatter_service": diet_formatter_service,
        "tracking_formatter_service": tracking_formatter_service,
        "tracking_service": tracking_service,
        "diet_service": diet_service,
        "command_factory": command_factory,
        "command_handler_service": command_handler_service,
        "onboarding_service": onboarding_service,
        "message_processor_service": message_processor_service,
        "reminder_service": reminder_service
    }