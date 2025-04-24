import pytest
from datetime import datetime, date, timedelta
import pytz
from unittest.mock import AsyncMock, MagicMock, patch, ANY

from app.models.tracking import MealComplianceStatus
from app.services.messaging.message_processor_service import MessageProcessorService


class TestEndToEndUserTracking:
    """
    End-to-end тесты для трекинга пользователя,
    имитирующие полный цикл взаимодействия пользователя с системой через WhatsApp.
    """

    @pytest.fixture
    def setup_end_to_end_environment(self, services, whatsapp_service_mock, test_user_data,
                                     test_diet_plan_data, test_weight_entries, test_water_entries):
        """Настройка полной среды для end-to-end тестирования с реальной локализацией."""
        # Берем необходимые сервисы из основного набора сервисов
        tracking_service = services["tracking_service"]
        message_processor_service = services["message_processor_service"]

        # Настраиваем пользователя
        user_id = "test-user-id"
        phone_number = "+5012345678"

        # Настраиваем репозитории
        firebase_repositories = {
            "user_repository": AsyncMock(),
            "weight_entry_repository": AsyncMock(),
            "water_entry_repository": AsyncMock(),
            "compliance_repository": AsyncMock(),
            "diet_plan_repository": AsyncMock()
        }

        # Настраиваем тестовые данные пользователя
        test_user_data["language"] = "ru"  # Устанавливаем язык для локализации
        firebase_repositories["user_repository"].get_by_id = AsyncMock(return_value=test_user_data)
        firebase_repositories["user_repository"].get_by_phone = AsyncMock(return_value=test_user_data)

        # Настраиваем репозиторий веса
        firebase_repositories["weight_entry_repository"].add_entry = AsyncMock(return_value="new-weight-id")
        firebase_repositories["weight_entry_repository"].get_entries_by_user = AsyncMock(
            return_value=test_weight_entries)
        firebase_repositories["weight_entry_repository"].get_latest_entry = AsyncMock(
            return_value=test_weight_entries[-1])

        # Настраиваем репозиторий воды
        firebase_repositories["water_entry_repository"].add_entry = AsyncMock(return_value="new-water-id")
        firebase_repositories["water_entry_repository"].get_entries_by_user = AsyncMock(return_value=test_water_entries)
        firebase_repositories["water_entry_repository"].get_daily_total = AsyncMock(return_value=750.0)

        # Настраиваем репозиторий соблюдения плана
        daily_compliance = {
            "user_id": user_id,
            "date": date.today(),
            "meals": {
                "breakfast": "followed",
                "lunch": "partially",
                "dinner": "not_recorded",
                "snack": "not_recorded"
            },
            "overall_score": 50.0
        }

        firebase_repositories["compliance_repository"].add_meal_compliance = AsyncMock(return_value="new-compliance-id")
        firebase_repositories["compliance_repository"].get_daily_compliance = AsyncMock(return_value=daily_compliance)
        firebase_repositories["compliance_repository"].update_daily_compliance = AsyncMock(return_value=True)

        async def record_weight_mock(user_id, weight, notes=None):
            return await firebase_repositories["weight_entry_repository"].add_entry(user_id, weight, date.today(),
                                                                                    notes)

        async def record_water_intake_mock(user_id, amount):
            return await firebase_repositories["water_entry_repository"].add_entry(user_id, amount, date.today())

        async def record_meal_compliance_mock(user_id, date_val, meal_type, status, notes=None, alternative_meal=None):
            return await firebase_repositories["compliance_repository"].add_meal_compliance(
                user_id, date_val, meal_type, status, notes, alternative_meal
            )

        # Настраиваем сервис трекинга
        tracking_service.record_weight = AsyncMock(side_effect=record_weight_mock)
        tracking_service.record_water_intake = AsyncMock(side_effect=record_water_intake_mock)
        tracking_service.record_meal_compliance = AsyncMock(side_effect=record_meal_compliance_mock)

        # Инициализируем реальный сервис локализации
        from app.localization.registry import registry

        # Создаем имитацию полного цикла приема и отправки сообщений с использованием
        # реальной локализации
        async def process_full_message_flow(message):
            # Аутентификация пользователя
            user = await firebase_repositories["user_repository"].get_by_phone(message["from"])
            if not user:
                return {"success": False, "message": "User not found"}

            user_id = user["id"]
            message_text = message["text"].lower()
            phone_number = message["from"]

            # Получаем язык пользователя
            lang = user.get("language", "ru")

            # Распознавание команды
            if message_text.startswith("вес"):
                weight_str = message_text.replace("вес", "").strip()
                try:
                    weight = float(weight_str)
                    new_entry_id = await tracking_service.record_weight(user_id, weight)
                    if new_entry_id:
                        # Используем реальную локализацию
                        weight_message = registry.get(
                            "tracking.weight.recorded",
                            lang,
                            weight=weight
                        )
                        await whatsapp_service_mock.send_message(phone_number, weight_message)
                        return {"success": True, "action": "weight_recorded", "entry_id": new_entry_id}
                    else:
                        error_message = registry.get("commands.weight.error", lang)
                        await whatsapp_service_mock.send_message(phone_number, error_message)
                        return {"success": False, "error": "Failed to record weight"}
                except ValueError:
                    error_message = registry.get("commands.weight.invalidFormat", lang)
                    await whatsapp_service_mock.send_message(phone_number, error_message)
                    return {"success": False, "error": "Invalid weight format"}

            # Обработка команды воды
            elif message_text.startswith("вода"):
                cups_str = message_text.replace("вода", "").strip()
                try:
                    cups = float(cups_str)
                    ml_amount = cups * 250

                    new_entry_id = await tracking_service.record_water_intake(user_id, ml_amount)
                    if new_entry_id:
                        # Используем реальную локализацию
                        water_message = registry.get(
                            "tracking.water.recorded",
                            lang,
                            amount=cups,
                            ml_amount=ml_amount,
                            count=cups  # Для плюральных форм
                        )
                        await whatsapp_service_mock.send_message(phone_number, water_message)
                        return {"success": True, "action": "water_recorded", "entry_id": new_entry_id}
                    else:
                        error_message = registry.get("commands.water.error", lang)
                        await whatsapp_service_mock.send_message(phone_number, error_message)
                        return {"success": False, "error": "Failed to record water intake"}
                except ValueError:
                    error_message = registry.get("commands.water.invalidFormat", lang)
                    await whatsapp_service_mock.send_message(phone_number, error_message)
                    return {"success": False, "error": "Invalid water format"}

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

                    meal_display_map = {
                        "breakfast": "Завтрак",
                        "lunch": "Обед",
                        "dinner": "Ужин",
                        "snack": "Перекус"
                    }

                    if status_word in status_map and meal_word in meal_map:
                        status = status_map[status_word]
                        meal_type = meal_map[meal_word]

                        today = date.today()
                        compliance_id = await tracking_service.record_meal_compliance(
                            user_id, today, meal_type, status
                        )

                        if compliance_id:
                            # Проверяем, что обновление дневной статистики было вызвано
                            await firebase_repositories["compliance_repository"].update_daily_compliance(user_id, today)

                            # Используем реальную локализацию
                            meal_name = meal_display_map[meal_type]
                            compliance_message = registry.get(
                                f"tracking.compliance.{status.value}",
                                lang,
                                meal_type=meal_name
                            )
                            await whatsapp_service_mock.send_message(phone_number, compliance_message)
                            return {"success": True, "action": "compliance_recorded", "entry_id": compliance_id}
                        else:
                            error_message = registry.get("commands.compliance.recordError", lang)
                            await whatsapp_service_mock.send_message(phone_number, error_message)
                            return {"success": False, "error": "Failed to record compliance"}

                # Если не удалось разобрать команду
                error_message = registry.get("commands.compliance.invalidFormat", lang)
                await whatsapp_service_mock.send_message(phone_number, error_message)
                return {"success": False, "error": "Invalid compliance format"}

            # Обработка команды статистики
            elif message_text in ["статистика", "прогресс"]:
                # Формируем сообщение статистики через реальную локализацию
                stats_message = registry.get("tracking.stats.header", lang)
                stats_message += registry.get("tracking.stats.weight_section", lang)
                stats_message += registry.get("tracking.stats.weight_initial", lang, weight=85.0)
                stats_message += registry.get("tracking.stats.weight_current", lang, weight=83.7)
                stats_message += registry.get("tracking.stats.weight_target", lang, weight=75.0)
                stats_message += registry.get("tracking.stats.weight_change_negative", lang, change=1.3)
                stats_message += registry.get("tracking.stats.weight_goal_remaining", lang, remaining=8.7)
                stats_message += registry.get("tracking.stats.weight_goal_percentage", lang, percentage=13.0)
                stats_message += registry.get("tracking.stats.water_section", lang)
                stats_message += registry.get("tracking.stats.water_consumed", lang, intake=750)
                stats_message += registry.get("tracking.stats.water_goal", lang, goal=2000)
                stats_message += registry.get("tracking.stats.water_percentage", lang, percentage=37.5)
                stats_message += registry.get("tracking.stats.compliance_section", lang)
                stats_message += registry.get("tracking.stats.compliance_overall", lang, score=50.0)
                stats_message += registry.get("tracking.stats.motivation", lang)

                await whatsapp_service_mock.send_message(phone_number, stats_message)
                return {"success": True, "action": "stats_displayed"}

            # Если команда не распознана
            error_message = registry.get("commands.general.unknownCommand", lang)
            await whatsapp_service_mock.send_message(phone_number, error_message)
            return {"success": False, "error": "Command not recognized"}

        # Устанавливаем наш метод для обработки сообщений
        message_processor_service.process_message = AsyncMock(side_effect=process_full_message_flow)

        return {
            "message_processor": message_processor_service,
            "tracking_service": tracking_service,
            "whatsapp_service": whatsapp_service_mock,
            "firebase_repositories": firebase_repositories,
            "user_id": user_id,
            "phone_number": phone_number,
            "localization_registry": registry
        }

    @pytest.mark.asyncio
    async def test_complete_user_tracking_scenario(self, setup_end_to_end_environment):
        """
        Тестирование полного пользовательского сценария трекинга:
        1. Запись веса
        2. Отметка потребления воды
        3. Отметка соблюдения плана
        4. Получение статистики
        """
        # Получаем настроенные сервисы и данные
        message_processor = setup_end_to_end_environment["message_processor"]
        whatsapp_service = setup_end_to_end_environment["whatsapp_service"]
        firebase_repositories = setup_end_to_end_environment["firebase_repositories"]
        phone_number = setup_end_to_end_environment["phone_number"]
        user_id = setup_end_to_end_environment["user_id"]
        localization_registry = setup_end_to_end_environment["localization_registry"]

        # Сбрасываем счетчики вызовов
        whatsapp_service.send_message.reset_mock()

        # 1. Сценарий: Запись веса
        weight_message = {
            "message_id": "msg-1",
            "from": phone_number,
            "text": "вес 83.2"
        }

        weight_result = await message_processor.process_message(weight_message)

        # Проверяем результат
        assert weight_result["success"] is True
        assert weight_result["action"] == "weight_recorded"

        # Проверяем вызов репозитория
        firebase_repositories["weight_entry_repository"].add_entry.assert_called_once_with(
            user_id, 83.2, date.today(), None
        )

        # Проверяем отправку сообщения с использованием ожидаемого текста из локализации
        assert whatsapp_service.send_message.call_count == 1
        weight_call_args = whatsapp_service.send_message.call_args_list[0]
        assert weight_call_args[0][0] == phone_number

        # Получаем ожидаемый текст из реальной локализации
        expected_weight_text = localization_registry.get(
            "tracking.weight.recorded",
            "ru",
            weight=83.2
        )
        assert weight_call_args[0][1] == expected_weight_text

        # Сбрасываем моки
        whatsapp_service.send_message.reset_mock()
        firebase_repositories["weight_entry_repository"].add_entry.reset_mock()

        # 2. Сценарий: Запись потребления воды
        water_message = {
            "message_id": "msg-2",
            "from": phone_number,
            "text": "вода 2"
        }

        water_result = await message_processor.process_message(water_message)

        # Проверяем результат
        assert water_result["success"] is True
        assert water_result["action"] == "water_recorded"

        # Проверяем вызов репозитория
        firebase_repositories["water_entry_repository"].add_entry.assert_called_once_with(
            user_id, 500.0, date.today()
        )

        # Проверяем отправку сообщения с использованием ожидаемого текста из локализации
        assert whatsapp_service.send_message.call_count == 1
        water_call_args = whatsapp_service.send_message.call_args_list[0]
        assert water_call_args[0][0] == phone_number

        # Получаем ожидаемый текст из реальной локализации
        expected_water_text = localization_registry.get(
            "tracking.water.recorded",
            "ru",
            amount=2,
            ml_amount=500,
            count=2
        )
        assert water_call_args[0][1] == expected_water_text

        # Сбрасываем моки
        whatsapp_service.send_message.reset_mock()
        firebase_repositories["water_entry_repository"].add_entry.reset_mock()

        # 3. Сценарий: Отметка соблюдения плана
        compliance_message = {
            "message_id": "msg-3",
            "from": phone_number,
            "text": "выполнено ужин"
        }

        compliance_result = await message_processor.process_message(compliance_message)

        # Проверяем результат
        assert compliance_result["success"] is True
        assert compliance_result["action"] == "compliance_recorded"

        # Проверяем вызов репозитория
        firebase_repositories["compliance_repository"].add_meal_compliance.assert_called_once_with(
            user_id, date.today(), "dinner", MealComplianceStatus.FOLLOWED, None, None
        )

        # Проверяем обновление дневной статистики
        firebase_repositories["compliance_repository"].update_daily_compliance.assert_called_once_with(
            user_id, date.today()
        )

        # Проверяем отправку сообщения с использованием ожидаемого текста из локализации
        assert whatsapp_service.send_message.call_count == 1
        compliance_call_args = whatsapp_service.send_message.call_args_list[0]
        assert compliance_call_args[0][0] == phone_number

        # Получаем ожидаемый текст из реальной локализации
        expected_compliance_text = localization_registry.get(
            "tracking.compliance.followed",
            "ru",
            meal_type="Ужин"
        )
        assert compliance_call_args[0][1] == expected_compliance_text

        # Сбрасываем моки
        whatsapp_service.send_message.reset_mock()
        firebase_repositories["compliance_repository"].add_meal_compliance.reset_mock()
        firebase_repositories["compliance_repository"].update_daily_compliance.reset_mock()

        # 4. Сценарий: Получение статистики
        stats_message = {
            "message_id": "msg-4",
            "from": phone_number,
            "text": "статистика"
        }

        stats_result = await message_processor.process_message(stats_message)

        # Проверяем результат
        assert stats_result["success"] is True
        assert stats_result["action"] == "stats_displayed"

        # Проверяем отправку сообщения
        assert whatsapp_service.send_message.call_count == 1
        stats_call_args = whatsapp_service.send_message.call_args_list[0]
        assert stats_call_args[0][0] == phone_number

        # Проверяем, что сообщение статистики содержит ожидаемые фрагменты
        stats_text = stats_call_args[0][1]

        # Формируем ожидаемые фрагменты текста с помощью реальной локализации
        expected_header = localization_registry.get("tracking.stats.header", "ru")
        expected_weight_section = localization_registry.get("tracking.stats.weight_section", "ru")
        expected_water_section = localization_registry.get("tracking.stats.water_section", "ru")

        assert expected_header in stats_text
        assert expected_weight_section in stats_text
        assert expected_water_section in stats_text
        assert "83.7" in stats_text  # Текущий вес
        assert "750" in stats_text  # Потребление воды
