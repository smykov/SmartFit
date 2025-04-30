# tests/integration/workflows/test_diet_modification_flow.py
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.diet.diet_service import DietService
from app.services.diet.diet_plan_manager import DietPlanManager
from app.services.messaging.message_processor_service import MessageProcessorService


class TestDietModificationFlow:

    @pytest.fixture
    def setup_services(self, firebase_mock, llm_service_mock, message_client_mock, localization_service_mock):
        """Настройка всех необходимых сервисов для тестирования потока."""
        # Создаем репозитории
        messenger_registry = AsyncMock()
        user_identity_service = AsyncMock()
        user_repository = AsyncMock()
        diet_plan_repository = AsyncMock()
        message_repository = AsyncMock()
        product_repository = AsyncMock()
        shopping_list_repository = AsyncMock()

        # Создаем сервисы
        messenger_service = AsyncMock()
        messenger_service.send_message = message_client_mock.send_message

        # Настраиваем необходимые моки
        user_repository.get_by_id.return_value = {
            "id": "test-user-id",
            "phone_number": "+1234567890",
            "name": "Test User",
            "language": "ru",
            "is_onboarding_completed": True
        }

        user_repository.get_by_phone.return_value = {
            "id": "test-user-id",
            "phone_number": "+1234567890",
            "name": "Test User",
            "language": "ru",
            "is_onboarding_completed": True
        }

        test_diet_plan = {
            "id": "test-diet-plan-id",
            "user_id": "test-user-id",
            "version": "short",
            "status": "pending",
            "daily_plans": {
                "monday": {
                    "meals": [
                        {
                            "type": "breakfast",
                            "title": "Овсянка с фруктами"
                        },
                        {
                            "type": "lunch",
                            "title": "Куриный салат"
                        }
                    ]
                }
            }
        }

        diet_plan_repository.get_by_id.return_value = test_diet_plan
        diet_plan_repository.get_current_diet.return_value = test_diet_plan

        # Создаем сервис диет
        diet_service = DietService(
            user_repository=user_repository,
            messenger_service=messenger_service,
            localization_service=localization_service_mock,
            diet_plan_repository=diet_plan_repository,
            product_repository=product_repository,
            shopping_list_repository=shopping_list_repository,
            llm_service=llm_service_mock
        )

        # Переопределяем метод diet_plan_manager для тестов
        diet_service.diet_plan_manager = AsyncMock(spec=DietPlanManager)
        diet_service.diet_plan_manager.update_short_diet_plan_by_request.return_value = {
            "success": True,
            "plan": {
                "id": "test-diet-plan-id",
                "daily_plans": {
                    "monday": {
                        "meals": [
                            {
                                "type": "breakfast",
                                "title": "Омлет с овощами"
                            },
                            {
                                "type": "lunch",
                                "title": "Куриный салат"
                            }
                        ]
                    }
                }
            },
            "comment": "Заменил овсянку на омлет с овощами согласно вашему запросу",
            "updated_days": {
                "monday": {
                    "meals": [
                        {
                            "type": "breakfast",
                            "title": "Омлет с овощами"
                        },
                        {
                            "type": "lunch",
                            "title": "Куриный салат"
                        }
                    ]
                }
            }
        }

        diet_service.get_diet_summary = MagicMock(
            return_value="Ваш план питания обновлен. Понедельник: Завтрак - Омлет с овощами, Обед - Куриный салат")

        # Создаем процессор сообщений
        onboarding_service = AsyncMock()
        tracking_service = AsyncMock()
        command_factory = AsyncMock()

        message_processor = MessageProcessorService(
            messenger_registry=messenger_registry,
            user_identity_service=user_identity_service,
            user_repository=user_repository,
            message_repository=message_repository,
            messenger_service=messenger_service,
            localization_service=localization_service_mock,
            onboarding_service=onboarding_service,
            diet_service=diet_service,
            tracking_service=tracking_service,
            command_factory=command_factory,
            command_extractor=AsyncMock(),
            command_executor=AsyncMock()
        )

        # Устанавливаем обработчик для сообщений о корректировке диеты
        async def process_diet_modification(user_id, message_text):
            if "замени" in message_text.lower() or "измени" in message_text.lower():
                result = await diet_service.update_short_diet_plan_by_request("test-diet-plan-id", message_text)
                if result["success"]:
                    summary = diet_service.get_diet_summary(result["plan"], "ru")
                    await messenger_service.send_message("+1234567890", summary)
                    return True
            return False

        message_processor._process_diet_modification = process_diet_modification

        # Переопределяем метод распознавания команд
        async def process_message_mock(message_data):
            message_text = message_data.get("text", "")
            user_id = "test-user-id"

            # Если это запрос на изменение диеты
            if "замени" in message_text.lower() or "измени" in message_text.lower():
                await process_diet_modification(user_id, message_text)
                return {"success": True}

            return {"success": False, "message": "Command not recognized"}

        message_processor.process_message = AsyncMock(side_effect=process_message_mock)

        return {
            "diet_service": diet_service,
            "message_processor": message_processor,
            "messenger_service": messenger_service
        }

    async def test_diet_modification_full_flow(self, setup_services):
        """Тестирование полного потока модификации диеты."""
        diet_service = setup_services["diet_service"]
        message_processor = setup_services["message_processor"]
        messenger_service = setup_services["messenger_service"]

        # Создаем тестовое сообщение от пользователя
        message_data = {
            "message_id": "test-message-id",
            "from": "+1234567890",
            "text": "Замени завтрак в понедельник на омлет с овощами"
        }

        # Обрабатываем сообщение
        await message_processor.process_message(message_data)

        # Проверяем, что метод update_short_diet_plan_by_request был вызван с правильными параметрами
        diet_service.diet_plan_manager.update_short_diet_plan_by_request.assert_called_once_with(
            "test-diet-plan-id",
            "Замени завтрак в понедельник на омлет с овощами"
        )

        # Проверяем, что пользователю было отправлено сообщение с обновленным планом
        messenger_service.send_message.assert_called_once()

        # Проверяем содержимое отправленного сообщения
        call_args = messenger_service.send_message.call_args
        assert call_args[0][0] == "+1234567890"  # Номер телефона
        assert "Ваш план питания обновлен" in call_args[0][1]  # Текст сообщения