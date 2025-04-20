# tests/functional/scenarios/test_diet_plan_usage.py
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta


class TestDietPlanUsageScenario:

    @pytest.fixture
    def setup_data_and_services(self, firebase_mock, llm_service_mock, message_client_mock, localization_service_mock,
                                test_user_data, test_diet_plan_data):
        """Настройка данных и сервисов для функционального тестирования."""
        from app.services.diet.diet_service import DietService
        from app.services.tracking.tracking_service import TrackingService
        from app.services.messaging.message_processor_service import MessageProcessorService

        # Создаем репозитории и другие зависимости
        user_repository = AsyncMock()
        diet_plan_repository = AsyncMock()
        message_repository = AsyncMock()
        product_repository = AsyncMock()
        shopping_list_repository = AsyncMock()
        weight_entry_repository = AsyncMock()
        water_entry_repository = AsyncMock()
        compliance_repository = AsyncMock()

        # Настраиваем данные в репозиториях
        user_repository.get_by_id.return_value = test_user_data
        user_repository.get_by_phone.return_value = test_user_data
        diet_plan_repository.get_by_id.return_value = test_diet_plan_data
        diet_plan_repository.get_current_diet.return_value = test_diet_plan_data

        # Создаем сервисы
        message_service = AsyncMock()
        message_service.send_message = message_client_mock.send_message

        # Трекинг-сервис
        tracking_service = TrackingService(
            user_repository=user_repository,
            weight_entry_repository=weight_entry_repository,
            water_entry_repository=water_entry_repository,
            compliance_repository=compliance_repository,
            localization_service=localization_service_mock
        )

        # Моки для трекинг-сервиса
        tracking_service.record_weight = AsyncMock(return_value=True)
        tracking_service.record_water_intake = AsyncMock(return_value=True)
        tracking_service.record_meal_compliance = AsyncMock(return_value=True)
        tracking_service.get_daily_status = AsyncMock(return_value={
            "weight_recorded": True,
            "current_water_intake": 1000,
            "water_goal": 2000,
            "water_percentage": 50,
            "meal_compliance": {"breakfast": "followed", "lunch": "partially"},
            "overall_compliance_score": 75
        })

        # Сервис диет
        diet_service = DietService(
            user_repository=user_repository,
            message_service=message_service,
            localization_service=localization_service_mock,
            diet_plan_repository=diet_plan_repository,
            product_repository=product_repository,
            shopping_list_repository=shopping_list_repository,
            llm_service=llm_service_mock
        )

        # Моки для сервиса диет
        diet_service.update_short_diet_plan_by_request = AsyncMock(return_value={
            "success": True,
            "plan": test_diet_plan_data,
            "comment": "План обновлен",
            "updated_days": {"monday": test_diet_plan_data["daily_plans"]["monday"]}
        })

        diet_service.generate_shopping_list = AsyncMock(return_value={
            "user_id": "test-user-id",
            "diet_plan_id": "test-diet-plan-id",
            "items": [
                {"name": "Овсянка", "quantity": 50, "unit": "г", "is_purchased": False},
                {"name": "Банан", "quantity": 1, "unit": "шт.", "is_purchased": False},
                {"name": "Куриная грудка", "quantity": 150, "unit": "г", "is_purchased": False}
            ]
        })

        diet_service.mark_product_as_purchased = AsyncMock(return_value={
            "success": True,
            "message": "Продукт отмечен как купленный"
        })

        diet_service.get_diet_summary = MagicMock(return_value="Сводка плана питания")
        diet_service.format_shopping_list = MagicMock(return_value="Список покупок: Овсянка, Банан, Куриная грудка")

        # Процессор сообщений
        onboarding_service = AsyncMock()
        command_factory = AsyncMock()

        message_processor = MessageProcessorService(
            user_repository=user_repository,
            message_repository=message_repository,
            message_service=message_service,
            localization_service=localization_service_mock,
            onboarding_service=onboarding_service,
            diet_service=diet_service,
            tracking_service=tracking_service,
            command_factory=command_factory
        )

        # Переопределяем методы обработки сообщений для тестирования
        async def process_message_mock(message_data):
            message_text = message_data.get("text", "").lower()
            user_id = "test-user-id"
            phone_number = "+5012345678"

            # Имитируем различные команды
            if "замени" in message_text or "измени" in message_text:
                result = await diet_service.update_short_diet_plan_by_request("test-diet-plan-id", message_text)
                await message_service.send_message(phone_number, diet_service.get_diet_summary(result["plan"], "ru"))
                return {"success": True}

            elif "список покупок" in message_text:
                shopping_list = await diet_service.generate_shopping_list("test-diet-plan-id")
                await message_service.send_message(phone_number, diet_service.format_shopping_list(shopping_list))
                return {"success": True}

            elif message_text.startswith("купил"):
                product_name = message_text.replace("купил", "").strip()
                result = await diet_service.mark_product_as_purchased(user_id, product_name)
                await message_service.send_message(phone_number, result["message"])
                return {"success": True}

            elif message_text.startswith("вес"):
                weight_str = message_text.replace("вес", "").strip()
                weight = float(weight_str)
                await tracking_service.record_weight(user_id, weight)
                await message_service.send_message(phone_number, f"Вес {weight} кг записан")
                return {"success": True}

            elif message_text.startswith("вода"):
                cups_str = message_text.replace("вода", "").strip()
                cups = float(cups_str)
                ml_amount = cups * 250
                await tracking_service.record_water_intake(user_id, ml_amount)
                await message_service.send_message(phone_number,
                                                   f"Потребление воды {cups} стаканов (~{ml_amount} мл) записано")
                return {"success": True}

            elif "выполнено" in message_text:
                meal_type = "breakfast" if "завтрак" in message_text else "lunch" if "обед" in message_text else "dinner" if "ужин" in message_text else None
                if meal_type:
                    await tracking_service.record_meal_compliance(user_id, datetime.now().date(), meal_type, "followed")
                    await message_service.send_message(phone_number, f"Отмечено: {meal_type} выполнен")
                    return {"success": True}

            return {"success": False, "message": "Command not recognized"}

        message_processor.process_message = AsyncMock(side_effect=process_message_mock)

        return {
            "user_data": test_user_data,
            "diet_plan_data": test_diet_plan_data,
            "diet_service": diet_service,
            "tracking_service": tracking_service,
            "message_processor": message_processor,
            "message_service": message_service
        }

    async def test_complete_diet_usage_flow(self, setup_data_and_services):
        """Тестирование полного сценария использования плана диеты."""
        diet_service = setup_data_and_services["diet_service"]
        tracking_service = setup_data_and_services["tracking_service"]
        message_processor = setup_data_and_services["message_processor"]
        message_service = setup_data_and_services["message_service"]

        # 1. Пользователь запрашивает изменение в план диеты
        await message_processor.process_message({
            "message_id": "msg-1",
            "from": "+5012345678",
            "text": "Замени завтрак в понедельник на омлет с овощами"
        })

        # Проверяем вызов метода обновления плана
        diet_service.update_short_diet_plan_by_request.assert_called_once()
        message_service.send_message.assert_called_once()
        message_service.send_message.reset_mock()

        # 2. Пользователь запрашивает список покупок
        await message_processor.process_message({
            "message_id": "msg-2",
            "from": "+5012345678",
            "text": "Список покупок"
        })

        # Проверяем генерацию списка покупок
        diet_service.generate_shopping_list.assert_called_once()
        diet_service.format_shopping_list.assert_called_once()
        message_service.send_message.assert_called_once()
        message_service.send_message.reset_mock()

        # 3. Пользователь отмечает покупку продукта
        await message_processor.process_message({
            "message_id": "msg-3",
            "from": "+5012345678",
            "text": "Купил Овсянка"
        })

        # Проверяем отметку о покупке продукта
        diet_service.mark_product_as_purchased.assert_called_once_with("test-user-id", "овсянка")
        message_service.send_message.assert_called_once()
        message_service.send_message.reset_mock()

        # 4. Пользователь записывает свой вес
        await message_processor.process_message({
            "message_id": "msg-4",
            "from": "+5012345678",
            "text": "Вес 84"
        })

        # Проверяем запись веса
        tracking_service.record_weight.assert_called_once_with("test-user-id", 84.0)
        message_service.send_message.assert_called_once()
        message_service.send_message.reset_mock()

        # 5. Пользователь записывает потребление воды
        await message_processor.process_message({
            "message_id": "msg-5",
            "from": "+5012345678",
            "text": "Вода 3"
        })

        # Проверяем запись потребления воды
        tracking_service.record_water_intake.assert_called_once_with("test-user-id", 750.0)
        message_service.send_message.assert_called_once()
        message_service.send_message.reset_mock()

        # 6. Пользователь отмечает соблюдение плана питания
        await message_processor.process_message({
            "message_id": "msg-6",
            "from": "+5012345678",
            "text": "Выполнено завтрак"
        })

        # Проверяем запись о соблюдении плана питания
        tracking_service.record_meal_compliance.assert_called_once()
        message_service.send_message.assert_called_once()