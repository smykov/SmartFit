import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
import json
from datetime import datetime, date, timedelta
import pytz

from app.db.interfaces.compliance_repository_interface import IComplianceRepository
from app.db.interfaces.diet_plan_repository_interface import IDietPlanRepository
from app.db.interfaces.message_repository_interface import IMessageRepository
from app.db.interfaces.product_repository_interface import IProductRepository
from app.db.interfaces.shopping_list_repository_interface import IShoppingListRepository
from app.db.interfaces.user_repository_interface import IUserRepository
from app.db.interfaces.water_entry_repository_interface import IWaterEntryRepository
from app.db.interfaces.weight_entry_repository_interface import IWeightEntryRepository
from app.services.diet.diet_service import DietService
from app.services.tracking.tracking_service import TrackingService
from app.services.messaging.message_processor_service import MessageProcessorService
from app.models.tracking import MealComplianceStatus


class TestFullUserJourney:
    """
    End-to-End тестирование полного пользовательского пути от создания
    плана диеты до отслеживания прогресса.
    """

    @pytest.fixture
    def setup_data_and_services(self, firebase_repositories, llm_service_mock, whatsapp_service_mock,
                                localization_service_mock, test_user_data, test_diet_plan_data):
        """Настройка данных и сервисов для end-to-end тестирования."""
        # Настраиваем репозитории
        messenger_registry = AsyncMock()
        user_identity_service = AsyncMock()
        user_repository = AsyncMock(spec=IUserRepository)
        diet_plan_repository = AsyncMock(spec=IDietPlanRepository)
        message_repository = AsyncMock(spec=IMessageRepository)
        product_repository = AsyncMock(spec=IProductRepository)
        shopping_list_repository = AsyncMock(spec=IShoppingListRepository)
        weight_entry_repository = AsyncMock(spec=IWeightEntryRepository)
        water_entry_repository = AsyncMock(spec=IWaterEntryRepository)
        compliance_repository = AsyncMock(spec=IComplianceRepository)

        # Подготавливаем тестовые данные
        user_repository.get_by_id.return_value = test_user_data
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

        # Создаем сервис диет
        diet_service = DietService(
            user_repository=user_repository,
            messenger_service=whatsapp_service_mock,
            localization_service=localization_service_mock,
            diet_plan_repository=diet_plan_repository,
            product_repository=product_repository,
            shopping_list_repository=shopping_list_repository,
            llm_service=llm_service_mock
        )

        # Мокируем методы diet_service
        diet_service.generate_short_diet_plan = AsyncMock(return_value=test_diet_plan_data)
        diet_service.approve_short_diet_plan = AsyncMock(return_value=True)
        diet_service.update_short_diet_plan_by_request = AsyncMock(return_value={
            "success": True,
            "plan": test_diet_plan_data,
            "comment": "План обновлен",
            "updated_days": {"monday": test_diet_plan_data["daily_plans"]["monday"]}
        })
        diet_service.generate_shopping_list = AsyncMock(return_value=shopping_list_data)
        diet_service.mark_product_as_purchased = AsyncMock(return_value={
            "success": True,
            "message": "✅ Отлично! Я отметил 'Овсянка' как купленный."
        })
        diet_service.get_diet_summary = MagicMock(return_value="Сводка плана питания")
        diet_service.formatter.format_shopping_list = MagicMock(
            return_value="*🛒 СПИСОК ПОКУПОК*\n\nВсего 4 наименования.\n\n..."
        )

        # Создаем сервис трекинга
        tracking_service = TrackingService(
            user_repository=user_repository,
            weight_entry_repository=weight_entry_repository,
            water_entry_repository=water_entry_repository,
            compliance_repository=compliance_repository,
            localization_service=localization_service_mock
        )

        # Мокируем методы трекинг-сервиса
        tracking_service.record_weight = AsyncMock(return_value=True)
        tracking_service.record_water_intake = AsyncMock(return_value=True)
        tracking_service.record_meal_compliance = AsyncMock(return_value=True)
        tracking_service.get_daily_status = AsyncMock(return_value={
            "user_id": "test-user-id",
            "date": date.today(),
            "weight_recorded": True,
            "current_water_intake": 750.0,
            "water_goal": 2000.0,
            "water_percentage": 37.5,
            "meal_compliance": {"breakfast": "followed", "lunch": "partially"},
            "overall_compliance_score": 75.0
        })
        tracking_service.calculate_weight_progress = AsyncMock(return_value={
            "user_id": "test-user-id",
            "start_weight": 85.0,
            "current_weight": 83.7,
            "target_weight": 75.0,
            "total_weight_change": -1.3,
            "weight_change_percentage": 13.0,
            "remaining_to_goal": -8.7,
            "goal_completion_percentage": 13.0
        })

        # Создаем процессор сообщений
        onboarding_service = AsyncMock()
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
            user_id = "test-user-id"

            # Обработка команд, связанных с диетой
            if message_text == "диета" or message_text == "план":
                plan = await diet_service.generate_short_diet_plan(user_id)
                await whatsapp_service_mock.send_message(phone_number, diet_service.get_diet_summary(plan, "ru"))
                return {"success": True}

            elif "замени" in message_text or "измени" in message_text:
                result = await diet_service.update_short_diet_plan_by_request("test-diet-plan-id", message_text)
                await whatsapp_service_mock.send_message(phone_number,
                                                         diet_service.get_diet_summary(result["plan"], "ru"))
                return {"success": True}

            elif "список покупок" in message_text:
                shopping_list = await diet_service.generate_shopping_list("test-diet-plan-id", "ru")
                await whatsapp_service_mock.send_message(phone_number,
                                                         diet_service.formatter.format_shopping_list(shopping_list,
                                                                                                     "ru"))
                return {"success": True}

            elif message_text.startswith("купил") or message_text.startswith("купила"):
                product_name = message_text.replace("купил", "").replace("купила", "").strip()
                result = await diet_service.mark_product_as_purchased(user_id, product_name)
                await whatsapp_service_mock.send_message(phone_number, result["message"])
                return {"success": True}

            # Обработка команд, связанных с трекингом
            elif message_text.startswith("вес"):
                weight_str = message_text.replace("вес", "").strip()
                weight = float(weight_str)
                await tracking_service.record_weight(user_id, weight)
                await whatsapp_service_mock.send_message(phone_number, f"✅ Отлично! Я записал ваш вес: {weight} кг.")
                return {"success": True}

            elif message_text.startswith("вода"):
                cups_str = message_text.replace("вода", "").strip()
                cups = float(cups_str)
                ml_amount = cups * 250
                await tracking_service.record_water_intake(user_id, ml_amount)
                await whatsapp_service_mock.send_message(phone_number,
                                                         f"💧 Отлично! Я записал ваше потребление воды: {cups} стаканов (~{ml_amount} мл).")
                return {"success": True}

            elif "выполнено" in message_text:
                meal_type = None
                if "завтрак" in message_text:
                    meal_type = "breakfast"
                elif "обед" in message_text:
                    meal_type = "lunch"
                elif "ужин" in message_text:
                    meal_type = "dinner"

                if meal_type:
                    await tracking_service.record_meal_compliance(user_id, date.today(), meal_type, "followed")
                    await whatsapp_service_mock.send_message(phone_number,
                                                             f"✅ Отлично! {meal_type.capitalize()} выполнен по плану.")
                    return {"success": True}

            elif "статистика" in message_text or "прогресс" in message_text:
                # Получаем данные о прогрессе
                weight_progress = await tracking_service.calculate_weight_progress(user_id)
                daily_status = await tracking_service.get_daily_status(user_id)

                # Формируем сообщение со статистикой
                stats_message = "*📊 СТАТИСТИКА И ПРОГРЕСС*\n\n"
                stats_message += f"*⚖️ Прогресс по весу:*\n"
                stats_message += f"• Начальный вес: {weight_progress['start_weight']} кг\n"
                stats_message += f"• Текущий вес: {weight_progress['current_weight']} кг\n"
                stats_message += f"• Целевой вес: {weight_progress['target_weight']} кг\n\n"
                stats_message += f"• Изменение: {weight_progress['total_weight_change']:.1f} кг\n"
                stats_message += f"• Осталось до цели: {abs(weight_progress['remaining_to_goal']):.1f} кг\n"
                stats_message += f"• Процент выполнения: {weight_progress['goal_completion_percentage']:.1f}%\n\n"

                stats_message += f"*💧 Потребление воды сегодня:*\n"
                stats_message += f"• Выпито: {daily_status['current_water_intake']} мл\n"
                stats_message += f"• Цель: {daily_status['water_goal']} мл\n"
                stats_message += f"• Выполнено: {daily_status['water_percentage']:.1f}%\n\n"

                stats_message += f"*🍽️ Соблюдение плана питания:*\n"
                for meal, status in daily_status['meal_compliance'].items():
                    stats_message += f"• {meal.capitalize()}: {status}\n"
                stats_message += f"\nОбщее соблюдение: {daily_status['overall_compliance_score']:.1f}%\n\n"

                stats_message += "💪 *Продолжай в том же духе!* Ты на пути к своей цели."

                await whatsapp_service_mock.send_message(phone_number, stats_message)
                return {"success": True}

            return {"success": False, "message": "Команда не распознана"}

        message_processor.process_message = AsyncMock(side_effect=process_message_mock)

        return {
            "diet_service": diet_service,
            "tracking_service": tracking_service,
            "message_processor": message_processor,
            "whatsapp_service": whatsapp_service_mock
        }

    @pytest.mark.asyncio
    async def test_complete_user_journey(self, setup_data_and_services):
        """
        Тестирует полный пользовательский сценарий использования приложения:
        1. Получение плана диеты
        2. Корректировка плана
        3. Получение списка покупок и отметка продуктов
        4. Отслеживание веса и потребления воды
        5. Отметка о соблюдении плана питания
        6. Получение статистики прогресса
        """
        diet_service = setup_data_and_services["diet_service"]
        tracking_service = setup_data_and_services["tracking_service"]
        message_processor = setup_data_and_services["message_processor"]
        whatsapp_service = setup_data_and_services["whatsapp_service"]

        # Настройка телефона пользователя
        phone_number = "+1234567890"

        # 1. Получение плана диеты
        await message_processor.process_message({
            "message_id": "test-msg-1",
            "from": phone_number,
            "text": "план"
        })

        # Проверяем, что вызван метод генерации плана
        assert diet_service.generate_short_diet_plan.called
        assert whatsapp_service.send_message.called

        # Сбрасываем счетчики для следующего шага
        whatsapp_service.send_message.reset_mock()

        # 2. Корректировка плана
        await message_processor.process_message({
            "message_id": "test-msg-2",
            "from": phone_number,
            "text": "Замени завтрак в понедельник на омлет с овощами"
        })

        # Проверяем, что вызван метод обновления плана
        assert diet_service.update_short_diet_plan_by_request.called
        assert whatsapp_service.send_message.called

        # Сбрасываем счетчики для следующего шага
        whatsapp_service.send_message.reset_mock()

        # 3. Получение списка покупок
        await message_processor.process_message({
            "message_id": "test-msg-3",
            "from": phone_number,
            "text": "Список покупок"
        })

        # Проверяем, что вызван метод генерации списка покупок
        assert diet_service.generate_shopping_list.called
        assert whatsapp_service.send_message.called

        # Сбрасываем счетчики для следующего шага
        whatsapp_service.send_message.reset_mock()

        # 4. Отметка продукта как купленного
        await message_processor.process_message({
            "message_id": "test-msg-4",
            "from": phone_number,
            "text": "Купил Овсянка"
        })

        # Проверяем, что вызван метод отметки продукта
        assert diet_service.mark_product_as_purchased.called
        assert whatsapp_service.send_message.called

        # Сбрасываем счетчики для следующего шага
        whatsapp_service.send_message.reset_mock()

        # 5. Запись веса
        await message_processor.process_message({
            "message_id": "test-msg-5",
            "from": phone_number,
            "text": "Вес 83.7"
        })

        # Проверяем, что вызван метод записи веса
        assert tracking_service.record_weight.called
        tracking_service.record_weight.assert_called_once_with("test-user-id", 83.7)
        assert whatsapp_service.send_message.called

        # Сбрасываем счетчики для следующего шага
        whatsapp_service.send_message.reset_mock()

        # 6. Запись потребления воды
        await message_processor.process_message({
            "message_id": "test-msg-6",
            "from": phone_number,
            "text": "Вода 3"
        })

        # Проверяем, что вызван метод записи потребления воды
        assert tracking_service.record_water_intake.called
        tracking_service.record_water_intake.assert_called_once_with("test-user-id", 750.0)
        assert whatsapp_service.send_message.called

        # Сбрасываем счетчики для следующего шага
        whatsapp_service.send_message.reset_mock()

        # 7. Отметка о соблюдении плана питания
        await message_processor.process_message({
            "message_id": "test-msg-7",
            "from": phone_number,
            "text": "Выполнено завтрак"
        })

        # Проверяем, что вызван метод записи соблюдения плана
        assert tracking_service.record_meal_compliance.called
        tracking_service.record_meal_compliance.assert_called_once_with(
            "test-user-id", date.today(), "breakfast", "followed"
        )
        assert whatsapp_service.send_message.called

        # Сбрасываем счетчики для следующего шага
        whatsapp_service.send_message.reset_mock()

        # 8. Получение статистики прогресса
        await message_processor.process_message({
            "message_id": "test-msg-8",
            "from": phone_number,
            "text": "Статистика"
        })

        # Проверяем, что вызваны методы получения прогресса
        assert tracking_service.calculate_weight_progress.called
        assert tracking_service.get_daily_status.called
        assert whatsapp_service.send_message.called

        # Проверяем содержимое сообщения со статистикой
        call_args = whatsapp_service.send_message.call_args
        assert call_args[0][0] == phone_number
        assert "*📊 СТАТИСТИКА И ПРОГРЕСС*" in call_args[0][1]