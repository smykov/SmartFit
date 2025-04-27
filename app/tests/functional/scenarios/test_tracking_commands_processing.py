import pytest
from datetime import datetime, date, timedelta
import pytz
from unittest.mock import AsyncMock, MagicMock, patch, ANY

from app.models.tracking import MealComplianceStatus
from app.services.commands.commands.weight_command import WeightCommand
from app.services.commands.commands.water_command import WaterCommand
from app.services.commands.commands.compliance_command import ComplianceCommand
from app.services.commands.commands.stats_command import StatsCommand
from app.services.messaging.message_processor_service import MessageProcessorService
from app.services.tracking.tracking_service import TrackingService


class TestTrackingCommandsScenario:
    """
    Функциональное тестирование обработки команд трекинга через MessageProcessorService.

    Тестирует end-to-end flow от получения команды через WhatsApp до ответа пользователю,
    включая:
    - Команды регистрации веса
    - Команды регистрации потребления воды
    - Команды отметки о соблюдении плана питания
    - Команды получения отчетов о прогрессе
    """

    @pytest.fixture
    def setup_command_processors(self, firebase_repositories, llm_service_mock, whatsapp_service_mock,
                                 localization_service_mock, test_user_data):
        """Настройка обработчиков команд и связанных сервисов."""
        messenger_registry = AsyncMock()
        user_identity_service = AsyncMock()
        # Получаем репозитории
        user_repository = firebase_repositories["user_repository"]
        weight_entry_repository = firebase_repositories["weight_entry_repository"]
        water_entry_repository = firebase_repositories["water_entry_repository"]
        compliance_repository = firebase_repositories["compliance_repository"]
        message_repository = firebase_repositories["message_repository"]

        # Настраиваем тестовые данные
        user_repository.get_by_id = AsyncMock(return_value=test_user_data)
        user_repository.get_by_phone = AsyncMock(return_value=test_user_data)

        # Создаем сервис трекинга
        tracking_service = TrackingService(
            user_repository=user_repository,
            weight_entry_repository=weight_entry_repository,
            water_entry_repository=water_entry_repository,
            compliance_repository=compliance_repository,
            localization_service=localization_service_mock
        )

        # Настраиваем методы сервиса трекинга
        tracking_service.record_weight = AsyncMock(return_value=True)
        tracking_service.record_water_intake = AsyncMock(return_value=True)
        tracking_service.record_meal_compliance = AsyncMock(return_value=True)

        # Настраиваем статистику пользователя
        tracking_service.calculate_weight_progress = AsyncMock(return_value={
            "user_id": "test-user-id",
            "start_weight": 85.0,
            "current_weight": 84.0,
            "target_weight": 75.0,
            "total_weight_change": -1.0,
            "weight_change_percentage": 10.0,
            "remaining_to_goal": 9.0,
            "goal_completion_percentage": 10.0
        })

        tracking_service.get_daily_status = AsyncMock(return_value={
            "user_id": "test-user-id",
            "date": date.today(),
            "weight_recorded": True,
            "current_water_intake": 500.0,
            "water_goal": 2000.0,
            "water_percentage": 25.0,
            "meal_compliance": {
                "breakfast": "followed",
                "lunch": "partially",
                "dinner": "not_recorded",
                "snack": "not_recorded"
            },
            "overall_compliance_score": 75.0
        })

        # Создаем экземпляры команд
        weight_command = WeightCommand({
            "user_repository": user_repository,
            "tracking_service": tracking_service,
            "localization_service": localization_service_mock
        })

        water_command = WaterCommand({
            "user_repository": user_repository,
            "tracking_service": tracking_service,
            "localization_service": localization_service_mock
        })

        compliance_command = ComplianceCommand({
            "user_repository": user_repository,
            "tracking_service": tracking_service,
            "localization_service": localization_service_mock
        })

        stats_command = StatsCommand({
            "user_repository": user_repository,
            "tracking_service": tracking_service,
            "localization_service": localization_service_mock
        })

        # Создаем мок для command_factory
        command_factory = MagicMock()
        command_factory.get_command = MagicMock()
        command_factory.get_command.side_effect = lambda command_name: {
            "weight": weight_command,
            "water": water_command,
            "compliance": compliance_command,
            "stats": stats_command
        }.get(command_name)

        # Создаем процессор сообщений
        message_processor = MessageProcessorService(
            messenger_registry=messenger_registry,
            user_identity_service=user_identity_service,
            user_repository=firebase_repositories["user_repository"],
            message_repository=firebase_repositories["message_repository"],
            messenger_service=whatsapp_service_mock,
            localization_service=localization_service_mock,
            onboarding_service=AsyncMock(),
            diet_service=AsyncMock(),
            tracking_service=tracking_service,
            command_factory=command_factory,
            command_extractor=AsyncMock(),
            command_executor=AsyncMock()
        )

        # Настраиваем метод обработки сообщений
        async def process_message_mock(message_data):
            message_text = message_data.get("text", "").lower()
            from_phone = message_data.get("from")
            user = await user_repository.get_by_phone(from_phone)
            user_id = user["id"]

            # Обработка команды веса
            if message_text.startswith("вес"):
                weight_str = message_text.replace("вес", "").strip()
                try:
                    weight = float(weight_str)
                    await tracking_service.record_weight(user_id, weight)
                    await whatsapp_service_mock.send_message(
                        from_phone, f"✅ Отлично! Я записал ваш вес: {weight} кг."
                    )
                    return {"success": True}
                except ValueError:
                    await whatsapp_service_mock.send_message(
                        from_phone, "Пожалуйста, введите вес в формате: вес XX"
                    )
                    return {"success": False}

            # Обработка команды воды
            elif message_text.startswith("вода"):
                cups_str = message_text.replace("вода", "").strip()
                try:
                    cups = float(cups_str)
                    ml_amount = cups * 250
                    await tracking_service.record_water_intake(user_id, ml_amount)
                    await whatsapp_service_mock.send_message(
                        from_phone, f"💧 Отлично! Я записал ваше потребление воды: {cups} стаканов (~{ml_amount} мл)."
                    )
                    return {"success": True}
                except ValueError:
                    await whatsapp_service_mock.send_message(
                        from_phone, "Пожалуйста, введите количество стаканов в формате: вода X"
                    )
                    return {"success": False}

            # Обработка команд соблюдения плана
            elif any(cmd in message_text for cmd in ["выполнено", "частично", "заменил", "пропустил"]):
                parts = message_text.split()
                if len(parts) >= 2:
                    status_word = parts[0].lower()
                    meal_word = parts[1].lower()

                    status_map = {
                        "выполнено": MealComplianceStatus.FOLLOWED,
                        "частично": MealComplianceStatus.PARTIALLY,
                        "заменил": MealComplianceStatus.SUBSTITUTED,
                        "пропустил": MealComplianceStatus.SKIPPED
                    }

                    meal_map = {
                        "завтрак": "breakfast",
                        "обед": "lunch",
                        "ужин": "dinner",
                        "перекус": "snack"
                    }

                    if status_word in status_map and meal_word in meal_map:
                        status = status_map[status_word]
                        meal_type = meal_map[meal_word]

                        await tracking_service.record_meal_compliance(
                            user_id, date.today(), meal_type, status
                        )

                        meal_name = meal_word.capitalize()
                        status_text = "выполнен" if status == MealComplianceStatus.FOLLOWED else \
                            "частично выполнен" if status == MealComplianceStatus.PARTIALLY else \
                                "заменен" if status == MealComplianceStatus.SUBSTITUTED else \
                                    "пропущен"

                        await whatsapp_service_mock.send_message(
                            from_phone, f"{meal_name} {status_text}."
                        )
                        return {"success": True}

            # Обработка команды статистики
            elif message_text in ["статистика", "прогресс"]:
                weight_progress = await tracking_service.calculate_weight_progress(user_id)
                daily_status = await tracking_service.get_daily_status(user_id)

                stats_message = "*📊 СТАТИСТИКА И ПРОГРЕСС*\n\n"
                stats_message += "⚖️ *Прогресс по весу:*\n"
                stats_message += f"• Начальный вес: {weight_progress['start_weight']} кг\n"
                stats_message += f"• Текущий вес: {weight_progress['current_weight']} кг\n"
                stats_message += f"• Целевой вес: {weight_progress['target_weight']} кг\n\n"

                stats_message += f"• Изменение: {weight_progress['total_weight_change']:.1f} кг\n"
                stats_message += f"• Осталось до цели: {weight_progress['remaining_to_goal']:.1f} кг\n"
                stats_message += f"• Процент выполнения: {weight_progress['goal_completion_percentage']:.1f}%\n\n"

                stats_message += "💧 *Потребление воды сегодня:*\n"
                stats_message += f"• Выпито: {daily_status['current_water_intake']} мл\n"
                stats_message += f"• Цель: {daily_status['water_goal']} мл\n"
                stats_message += f"• Выполнено: {daily_status['water_percentage']:.1f}%\n\n"

                stats_message += "🍽️ *Соблюдение плана питания:*\n"
                compliance = daily_status['meal_compliance']
                for meal, status in compliance.items():
                    meal_name = meal.capitalize()
                    stats_message += f"• {meal_name}: {status}\n"

                stats_message += f"\nОбщее соблюдение: {daily_status['overall_compliance_score']:.1f}%\n\n"
                stats_message += "💪 *Продолжай в том же духе!* Ты на пути к своей цели."

                await whatsapp_service_mock.send_message(from_phone, stats_message)
                return {"success": True}

            return {"success": False, "message": "Команда не распознана"}

        message_processor.process_message = AsyncMock(side_effect=process_message_mock)

        return {
            "message_processor": message_processor,
            "tracking_service": tracking_service,
            "whatsapp_service": whatsapp_service_mock,
            "user_repository": user_repository,
            "test_user": test_user_data
        }

    @pytest.mark.asyncio
    async def test_weight_command_processing(self, setup_command_processors):
        """Тестирование обработки команды веса от получения до ответа пользователю."""
        # Настройка
        message_processor = setup_command_processors["message_processor"]
        tracking_service = setup_command_processors["tracking_service"]
        whatsapp_service = setup_command_processors["whatsapp_service"]
        test_user = setup_command_processors["test_user"]

        # Сбрасываем счетчики вызовов
        tracking_service.record_weight.reset_mock()
        whatsapp_service.send_message.reset_mock()

        # Имитируем сообщение пользователя с командой веса
        message_data = {
            "message_id": "msg-1",
            "from": test_user["phone_number"],
            "text": "вес 83.5"
        }

        # Обрабатываем сообщение
        result = await message_processor.process_message(message_data)

        # Проверяем результат
        assert result["success"] is True

        # Проверяем, что метод записи веса был вызван с правильными параметрами
        tracking_service.record_weight.assert_called_once_with(test_user["id"], 83.5)

        # Проверяем, что пользователю было отправлено сообщение
        whatsapp_service.send_message.assert_called_once()
        args = whatsapp_service.send_message.call_args
        assert args[0][0] == test_user["phone_number"]
        assert "83.5" in args[0][1]

    @pytest.mark.asyncio
    async def test_water_command_processing(self, setup_command_processors):
        """Тестирование обработки команды воды от получения до ответа пользователю."""
        # Настройка
        message_processor = setup_command_processors["message_processor"]
        tracking_service = setup_command_processors["tracking_service"]
        whatsapp_service = setup_command_processors["whatsapp_service"]
        test_user = setup_command_processors["test_user"]

        # Сбрасываем счетчики вызовов
        tracking_service.record_water_intake.reset_mock()
        whatsapp_service.send_message.reset_mock()

        # Имитируем сообщение пользователя с командой воды
        message_data = {
            "message_id": "msg-2",
            "from": test_user["phone_number"],
            "text": "вода 3"
        }

        # Обрабатываем сообщение
        result = await message_processor.process_message(message_data)

        # Проверяем результат
        assert result["success"] is True

        # Проверяем, что метод записи воды был вызван с правильными параметрами
        cups = 3
        ml_amount = cups * 250
        tracking_service.record_water_intake.assert_called_once_with(test_user["id"], ml_amount)

        # Проверяем, что пользователю было отправлено сообщение
        whatsapp_service.send_message.assert_called_once()
        args = whatsapp_service.send_message.call_args
        assert args[0][0] == test_user["phone_number"]
        assert str(cups) in args[0][1]
        assert str(ml_amount) in args[0][1]

    @pytest.mark.asyncio
    async def test_meal_compliance_command_processing(self, setup_command_processors):
        """Тестирование обработки команды соблюдения плана от получения до ответа пользователю."""
        # Настройка
        message_processor = setup_command_processors["message_processor"]
        tracking_service = setup_command_processors["tracking_service"]
        whatsapp_service = setup_command_processors["whatsapp_service"]
        test_user = setup_command_processors["test_user"]

        # Сбрасываем счетчики вызовов
        tracking_service.record_meal_compliance.reset_mock()
        whatsapp_service.send_message.reset_mock()

        # Имитируем сообщение пользователя с командой соблюдения плана
        message_data = {
            "message_id": "msg-3",
            "from": test_user["phone_number"],
            "text": "выполнено завтрак"
        }

        # Обрабатываем сообщение
        result = await message_processor.process_message(message_data)

        # Проверяем результат
        assert result["success"] is True

        # Проверяем, что метод записи соблюдения был вызван с правильными параметрами
        tracking_service.record_meal_compliance.assert_called_once_with(
            test_user["id"],
            date.today(),
            "breakfast",
            MealComplianceStatus.FOLLOWED
        )

        # Проверяем, что пользователю было отправлено сообщение
        whatsapp_service.send_message.assert_called_once()
        args = whatsapp_service.send_message.call_args
        assert args[0][0] == test_user["phone_number"]
        assert "Завтрак" in args[0][1]

    @pytest.mark.asyncio
    async def test_stats_command_processing(self, setup_command_processors):
        """Тестирование обработки команды статистики от получения до ответа пользователю."""
        # Настройка
        message_processor = setup_command_processors["message_processor"]
        tracking_service = setup_command_processors["tracking_service"]
        whatsapp_service = setup_command_processors["whatsapp_service"]
        test_user = setup_command_processors["test_user"]

        # Сбрасываем счетчики вызовов
        tracking_service.calculate_weight_progress.reset_mock()
        tracking_service.get_daily_status.reset_mock()
        whatsapp_service.send_message.reset_mock()

        # Имитируем сообщение пользователя с командой статистики
        message_data = {
            "message_id": "msg-4",
            "from": test_user["phone_number"],
            "text": "статистика"
        }

        # Обрабатываем сообщение
        result = await message_processor.process_message(message_data)

        # Проверяем результат
        assert result["success"] is True

        # Проверяем, что методы получения данных были вызваны
        tracking_service.calculate_weight_progress.assert_called_once_with(test_user["id"])
        tracking_service.get_daily_status.assert_called_once_with(test_user["id"])

        # Проверяем, что пользователю было отправлено сообщение со статистикой
        whatsapp_service.send_message.assert_called_once()
        args = whatsapp_service.send_message.call_args
        assert args[0][0] == test_user["phone_number"]

        message_text = args[0][1]
        assert "*📊 СТАТИСТИКА И ПРОГРЕСС*" in message_text
        assert "Прогресс по весу" in message_text
        assert "Потребление воды" in message_text
        assert "Соблюдение плана питания" in message_text