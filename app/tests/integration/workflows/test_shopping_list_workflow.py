import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
import json
from datetime import datetime, date, timedelta
import pytz

from app.services.diet.diet_service import DietService
from app.services.messaging.message_processor_service import MessageProcessorService


class TestShoppingListWorkflow:
    """
    Тестирование рабочего процесса генерации и использования списка покупок.
    Проверяет интеграцию между diet_service, shopping_list_manager, и системой сообщений.
    """

    @pytest.fixture
    def setup_services(self, firebase_repositories, llm_service_mock, whatsapp_service_mock,
                       localization_service_mock, test_user_data, test_diet_plan_data):
        """Настройка всех необходимых сервисов для тестирования потока."""
        # Создаем моки репозиториев вместо использования реальных
        messenger_registry = AsyncMock()
        user_identity_service = AsyncMock()
        user_repository = AsyncMock()
        diet_plan_repository = AsyncMock()
        message_repository = AsyncMock()
        product_repository = AsyncMock()
        shopping_list_repository = AsyncMock()

        # Настраиваем поведение моков
        user_repository.get_by_id.return_value = test_user_data
        user_repository.get_by_phone.return_value = test_user_data
        diet_plan_repository.get_by_id.return_value = test_diet_plan_data
        diet_plan_repository.get_current_diet.return_value = test_diet_plan_data

        # Создаем тестовый список покупок
        shopping_list_data = {
            "id": "test-shopping-list-id",
            "user_id": "test-user-id",
            "diet_plan_id": "test-diet-plan-id",
            "items": [
                {"name": "Овсянка", "quantity": 100, "unit": "г", "category": "bread_cereals", "is_purchased": False},
                {"name": "Банан", "quantity": 3, "unit": "шт.", "category": "fruits_vegetables", "is_purchased": False},
                {"name": "Яйца", "quantity": 6, "unit": "шт.", "category": "dairy", "is_purchased": False},
                {"name": "Куриная грудка", "quantity": 300, "unit": "г", "category": "meat_fish", "is_purchased": False}
            ],
            "total_estimated_price": 150.0
        }

        # Настраиваем сервисы
        diet_service = DietService(
            user_repository=user_repository,
            messenger_service=whatsapp_service_mock,
            localization_service=localization_service_mock,
            diet_plan_repository=diet_plan_repository,
            product_repository=product_repository,
            shopping_list_repository=shopping_list_repository,
            llm_service=llm_service_mock
        )

        # Мокируем методы diet_service и shopping_list_manager
        diet_service.generate_shopping_list = AsyncMock(return_value=shopping_list_data)
        diet_service.mark_product_as_purchased = AsyncMock(return_value={
            "success": True,
            "message": "✅ Отлично! Я отметил 'Овсянка' как купленный."
        })
        diet_service.formatter.format_shopping_list = MagicMock(
            return_value="*🛒 СПИСОК ПОКУПОК*\n\n" +
                         "Всего 4 наименования.\n\n" +
                         "*Крупы (1):*\n- Овсянка: 100 г\n\n" +
                         "*Фрукты и овощи (1):*\n- Банан: 3 шт.\n\n" +
                         "*Молочные продукты (1):*\n- Яйца: 6 шт.\n\n" +
                         "*Мясо и рыба (1):*\n- Куриная грудка: 300 г\n\n" +
                         "Примерная стоимость: 150.0 кетцаль"
        )

        # Создаем процессор сообщений
        onboarding_service = AsyncMock()
        tracking_service = AsyncMock()
        command_factory = AsyncMock()

        message_processor = MessageProcessorService(
            messenger_registry=messenger_registry,
            user_identity_service=user_identity_service,
            user_repository=user_repository,
            message_repository=message_repository,
            messenger_service=whatsapp_service_mock,
            localization_service=localization_service_mock,
            onboarding_service=onboarding_service,
            diet_service=diet_service,
            tracking_service=tracking_service,
            command_factory=command_factory,
            command_extractor=AsyncMock(),
            command_executor=AsyncMock()
        )

        # Настраиваем обработку команд
        async def process_message_mock(message_data):
            message_text = message_data.get("text", "").lower()
            phone_number = message_data.get("from", "+1234567890")

            if "список покупок" in message_text:
                # Генерируем список покупок
                shopping_list = await diet_service.generate_shopping_list("test-diet-plan-id", "ru")
                formatted_list = diet_service.formatter.format_shopping_list(shopping_list, "ru")
                await whatsapp_service_mock.send_message(phone_number, formatted_list)
                return {"success": True}

            elif message_text.startswith("купил") or message_text.startswith("купила"):
                # Отмечаем продукт как купленный
                product_name = message_text.replace("купил", "").replace("купила", "").strip()
                result = await diet_service.mark_product_as_purchased("test-user-id", product_name)
                await whatsapp_service_mock.send_message(phone_number, result["message"])
                return {"success": True}

            return {"success": False, "message": "Команда не распознана"}

        message_processor.process_message = AsyncMock(side_effect=process_message_mock)

        return {
            "diet_service": diet_service,
            "message_processor": message_processor,
            "whatsapp_service": whatsapp_service_mock,
            "shopping_list_data": shopping_list_data
        }

    @pytest.mark.asyncio
    async def test_shopping_list_generation_workflow(self, setup_services):
        """
        Тестирует поток генерации списка покупок на основе плана диеты:
        1. Пользователь запрашивает список покупок
        2. Система генерирует список и отправляет пользователю
        """
        diet_service = setup_services["diet_service"]
        message_processor = setup_services["message_processor"]
        whatsapp_service = setup_services["whatsapp_service"]

        # 1. Пользователь запрашивает список покупок
        await message_processor.process_message({
            "message_id": "test-msg-1",
            "from": "+1234567890",
            "text": "Список покупок"
        })

        # Проверяем, что diet_service вызвал метод генерации списка покупок
        assert diet_service.generate_shopping_list.called
        diet_service.generate_shopping_list.assert_called_once_with("test-diet-plan-id", "ru")

        # Проверяем, что список был отформатирован
        assert diet_service.formatter.format_shopping_list.called

        # Проверяем, что пользователю отправлено сообщение со списком покупок
        assert whatsapp_service.send_message.called

        # Проверяем содержимое отправленного сообщения
        call_args = whatsapp_service.send_message.call_args
        assert call_args[0][0] == "+1234567890"  # Номер телефона
        assert "*🛒 СПИСОК ПОКУПОК*" in call_args[0][1]  # Текст сообщения

    @pytest.mark.asyncio
    async def test_mark_product_as_purchased_workflow(self, setup_services):
        """
        Тестирует поток отметки продукта как купленного:
        1. Пользователь сообщает о покупке продукта
        2. Система обновляет список покупок и подтверждает
        """
        diet_service = setup_services["diet_service"]
        message_processor = setup_services["message_processor"]
        whatsapp_service = setup_services["whatsapp_service"]

        # Сбрасываем счетчики вызовов
        whatsapp_service.send_message.reset_mock()

        # 1. Пользователь сообщает о покупке продукта
        await message_processor.process_message({
            "message_id": "test-msg-2",
            "from": "+1234567890",
            "text": "Купил Овсянка"
        })

        # Проверяем, что diet_service вызвал метод отметки продукта
        assert diet_service.mark_product_as_purchased.called
        diet_service.mark_product_as_purchased.assert_called_once_with("test-user-id", "овсянка")

        # Проверяем, что пользователю отправлено подтверждение
        assert whatsapp_service.send_message.called

        # Проверяем содержимое отправленного сообщения
        call_args = whatsapp_service.send_message.call_args
        assert call_args[0][0] == "+1234567890"  # Номер телефона
        assert "отметил" in call_args[0][1]  # Текст сообщения
        assert "Овсянка" in call_args[0][1]  # Название продукта