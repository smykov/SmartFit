# tests/unit/services/test_daily_tracking_history.py
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock, ANY
from datetime import datetime, date, timedelta
import pytz

from app.services.tracking.tracking_service import TrackingService
from app.services.messaging.message_processor_service import MessageProcessorService
from app.models.tracking import MealComplianceStatus
from app.utils.date_helper import DateHelper


class TestDailyTrackingHistory:

    @pytest.fixture
    def tracking_service_dependencies(self):
        """Фикстура для создания моков зависимостей TrackingService."""
        dependencies = {
            "user_repository": AsyncMock(),
            "diet_service": AsyncMock(),
            "weight_entry_repository": AsyncMock(),
            "water_entry_repository": AsyncMock(),
            "compliance_repository": AsyncMock(),
            "localization_service": MagicMock()
        }

        # Настройка возвращаемых значений для часто используемых методов
        dependencies["localization_service"].get_message.return_value = "Локализованное сообщение"
        dependencies["localization_service"].get_user_language = AsyncMock(return_value="ru")

        return dependencies

    @pytest.fixture
    def message_processor_dependencies(self):
        """Фикстура для создания моков зависимостей MessageProcessorService."""
        dependencies = {
            "messenger_registry": MagicMock(),
            "user_identity_service": AsyncMock(),
            "user_repository": AsyncMock(),
            "message_repository": AsyncMock(),
            "messenger_service": AsyncMock(),
            "onboarding_service": AsyncMock(),
            "diet_service": AsyncMock(),
            "tracking_service": AsyncMock(),
            "command_factory": MagicMock(),
            "localization_service": MagicMock(),
            "command_extractor": AsyncMock(),
            "command_executor": AsyncMock()
        }

        # Настройка возвращаемых значений
        dependencies["localization_service"].DEFAULT_LANGUAGE = "ru"
        dependencies["localization_service"].get_message.return_value = "Локализованное сообщение"

        return dependencies

    @pytest.fixture
    def tracking_service(self, tracking_service_dependencies):
        """Фикстура для создания тестируемого экземпляра TrackingService."""
        return TrackingService(**tracking_service_dependencies)

    @pytest.fixture
    def message_processor_service(self, message_processor_dependencies):
        """Фикстура для создания тестируемого экземпляра MessageProcessorService."""
        return MessageProcessorService(**message_processor_dependencies)

    @pytest.fixture
    def test_user_data(self):
        """Фикстура для создания тестовых данных пользователя."""
        return {
            "id": "test-user-id",
            "phone_number": "+5012345678",
            "name": "Test User",
            "timezone": "Europe/Moscow",
            "current_weight": 75.0,
            "target_weight": 70.0,
            "language": "ru"
        }

    @pytest.fixture
    def test_daily_compliance_data(self):
        """Фикстура для создания тестовых данных соблюдения плана за день."""
        return {
            "id": "compliance-id",
            "user_id": "test-user-id",
            "date": "2025-05-27",
            "overall_score": 85.0,
            "meals": {
                "breakfast": {
                    "status": "followed",
                    "notes": "Съел овсянку как в плане",
                    "calories_consumed": 350.0,
                    "proteins_consumed": 15.0,
                    "fats_consumed": 8.0,
                    "carbs_consumed": 55.0,
                    "calories_adherence": 100.0,
                    "proteins_adherence": 95.0,
                    "fats_adherence": 110.0,
                    "carbs_adherence": 98.0
                },
                "lunch": {
                    "status": "partially",
                    "notes": "Добавил немного масла в салат",
                    "calories_consumed": 520.0,
                    "proteins_consumed": 35.0,
                    "fats_consumed": 18.0,
                    "carbs_consumed": 45.0,
                    "calories_adherence": 115.6,
                    "proteins_adherence": 100.0,
                    "fats_adherence": 120.0,
                    "carbs_adherence": 90.0
                },
                "dinner": {
                    "status": "skipped",
                    "notes": "Пропустил ужин",
                    "calories_consumed": 0.0,
                    "proteins_consumed": 0.0,
                    "fats_consumed": 0.0,
                    "carbs_consumed": 0.0
                }
            }
        }

    @pytest.fixture
    def test_weight_entries(self):
        """Фикстура для создания тестовых записей веса."""
        return [
            {
                "id": "weight-1",
                "user_id": "test-user-id",
                "weight": 75.2,
                "date": "2025-05-27",
                "notes": "Утреннее взвешивание"
            }
        ]

    @pytest.fixture
    def test_today_diet_plan(self):
        """Фикстура для создания тестового плана на сегодня."""
        return {
            "date": "2025-05-27",
            "day_of_week": "tuesday",
            "total_calories": 1800,
            "total_proteins": 120,
            "total_fats": 70,
            "total_carbs": 180,
            "meals": [
                {
                    "type": "breakfast",
                    "title": "Овсянка с ягодами",
                    "calories": 350,
                    "proteins": 15,
                    "fats": 8,
                    "carbs": 55
                },
                {
                    "type": "lunch",
                    "title": "Куриная грудка с рисом",
                    "calories": 450,
                    "proteins": 35,
                    "fats": 15,
                    "carbs": 50
                },
                {
                    "type": "dinner",
                    "title": "Рыба с овощами",
                    "calories": 480,
                    "proteins": 40,
                    "fats": 20,
                    "carbs": 35
                },
                {
                    "type": "snack",
                    "title": "Орехи и йогурт",
                    "calories": 250,
                    "proteins": 12,
                    "fats": 18,
                    "carbs": 15
                }
            ]
        }

    #
    # 1. Тесты для метода get_daily_tracking_history
    #

    async def test_get_daily_tracking_history_success(self, tracking_service, tracking_service_dependencies,
                                                      test_user_data, test_daily_compliance_data,
                                                      test_weight_entries):
        """Тестирование успешного получения истории трекинга за день."""
        # Arrange
        user_id = "test-user-id"
        target_date = date(2025, 5, 27)
        water_total = 1500.0  # мл

        tracking_service_dependencies["user_repository"].get_by_id.return_value = test_user_data
        tracking_service_dependencies[
            "compliance_repository"].get_daily_compliance.return_value = test_daily_compliance_data
        tracking_service_dependencies["weight_entry_repository"].get_entries_by_user.return_value = test_weight_entries
        tracking_service_dependencies["water_entry_repository"].get_daily_total.return_value = water_total

        # Act
        result = await tracking_service.get_daily_tracking_history(user_id, target_date)

        # Assert
        assert result is not None
        assert result["date"] == "2025-05-27"
        assert result["day_of_week"] == "tuesday"
        assert result["overall_compliance_score"] == 85.0

        # Проверяем данные о приемах пищи
        meals_tracking = result["meals_tracking"]
        assert "breakfast" in meals_tracking
        assert "lunch" in meals_tracking
        assert "dinner" in meals_tracking

        breakfast_data = meals_tracking["breakfast"]
        assert breakfast_data["status"] == "followed"
        assert breakfast_data["calories_consumed"] == 350.0
        assert breakfast_data["proteins_consumed"] == 15.0
        assert breakfast_data["notes"] == "Съел овсянку как в плане"

        # Проверяем кумулятивные нутриенты
        cumulative = result["cumulative_nutrients"]
        assert cumulative["calories"] == 870.0  # 350 + 520 + 0
        assert cumulative["proteins"] == 50.0  # 15 + 35 + 0
        assert cumulative["fats"] == 26.0  # 8 + 18 + 0
        assert cumulative["carbs"] == 100.0  # 55 + 45 + 0

        # Проверяем итоги дня
        daily_totals = result["daily_totals"]
        assert daily_totals["water_consumed"] == 1500.0
        assert daily_totals["weight_recorded"] is True
        assert daily_totals["latest_weight"] == 75.2

        # Verify calls
        tracking_service_dependencies["user_repository"].get_by_id.assert_called_once_with(user_id)
        tracking_service_dependencies["compliance_repository"].get_daily_compliance.assert_called_once_with(user_id,
                                                                                                            target_date)
        tracking_service_dependencies["weight_entry_repository"].get_entries_by_user.assert_called_once_with(user_id,
                                                                                                             target_date,
                                                                                                             target_date)
        tracking_service_dependencies["water_entry_repository"].get_daily_total.assert_called_once_with(user_id,
                                                                                                        target_date)

    async def test_get_daily_tracking_history_no_data(self, tracking_service, tracking_service_dependencies,
                                                      test_user_data):
        """Тестирование получения истории когда нет данных за день."""
        # Arrange
        user_id = "test-user-id"
        target_date = date(2025, 5, 27)

        tracking_service_dependencies["user_repository"].get_by_id.return_value = test_user_data
        tracking_service_dependencies["compliance_repository"].get_daily_compliance.return_value = None
        tracking_service_dependencies["weight_entry_repository"].get_entries_by_user.return_value = []
        tracking_service_dependencies["water_entry_repository"].get_daily_total.return_value = 0.0

        # Act
        result = await tracking_service.get_daily_tracking_history(user_id, target_date)

        # Assert
        assert result is not None
        assert result["date"] == "2025-05-27"
        assert result["overall_compliance_score"] == 0
        assert result["meals_tracking"] == {}
        assert result["cumulative_nutrients"]["calories"] == 0
        assert result["daily_totals"]["water_consumed"] == 0.0
        assert result["daily_totals"]["weight_recorded"] is False
        assert result["daily_totals"]["latest_weight"] is None

    async def test_get_daily_tracking_history_user_not_found(self, tracking_service,
                                                             tracking_service_dependencies):
        """Тестирование получения истории когда пользователь не найден."""
        # Arrange
        user_id = "non-existent-user"
        target_date = date(2025, 5, 27)

        tracking_service_dependencies["user_repository"].get_by_id.return_value = None

        # Act
        result = await tracking_service.get_daily_tracking_history(user_id, target_date)

        # Assert
        assert result == {}

        # Verify calls
        tracking_service_dependencies["user_repository"].get_by_id.assert_called_once_with(user_id)
        tracking_service_dependencies["compliance_repository"].get_daily_compliance.assert_not_called()

    async def test_get_daily_tracking_history_with_default_date(self, tracking_service,
                                                                tracking_service_dependencies,
                                                                test_user_data):
        """Тестирование получения истории с использованием текущей даты по умолчанию."""
        # Arrange
        user_id = "test-user-id"

        tracking_service_dependencies["user_repository"].get_by_id.return_value = test_user_data
        tracking_service_dependencies["compliance_repository"].get_daily_compliance.return_value = None
        tracking_service_dependencies["weight_entry_repository"].get_entries_by_user.return_value = []
        tracking_service_dependencies["water_entry_repository"].get_daily_total.return_value = 0.0

        # Мокируем DateHelper.get_tracking_date
        with patch.object(DateHelper, 'get_tracking_date') as mock_get_tracking_date:
            mock_tracking_date = date(2025, 5, 27)
            mock_get_tracking_date.return_value = mock_tracking_date

            # Act
            result = await tracking_service.get_daily_tracking_history(user_id)

            # Assert
            assert result is not None
            assert result["date"] == "2025-05-27"

            # Verify DateHelper was called with user timezone
            mock_get_tracking_date.assert_called_once_with(test_user_data.get("timezone"))

    async def test_get_daily_tracking_history_exception_handling(self, tracking_service,
                                                                 tracking_service_dependencies,
                                                                 test_user_data):
        """Тестирование обработки исключений при получении истории трекинга."""
        # Arrange
        user_id = "test-user-id"
        target_date = date(2025, 5, 27)

        tracking_service_dependencies["user_repository"].get_by_id.return_value = test_user_data
        tracking_service_dependencies["compliance_repository"].get_daily_compliance.side_effect = Exception(
            "Database error")

        # Act
        result = await tracking_service.get_daily_tracking_history(user_id, target_date)

        # Assert
        assert result == {}

    #
    # 2. Тесты для обогащения контекста
    #

    async def test_enrich_context_with_tracking_history(self, message_processor_service,
                                                        message_processor_dependencies,
                                                        test_user_data, test_daily_compliance_data,
                                                        test_today_diet_plan):
        """Тестирование обогащения контекста историей трекинга."""
        # Arrange
        user_id = "test-user-id"
        initial_context = {"some_key": "some_value"}

        # Настройка моков
        message_processor_dependencies["user_repository"].get_by_id.return_value = test_user_data
        message_processor_dependencies["diet_service"].get_current_diet.return_value = {
            "id": "diet-id",
            "daily_plans": {"tuesday": test_today_diet_plan}
        }
        message_processor_dependencies["diet_service"].get_diet_for_day.return_value = test_today_diet_plan

        # Мокируем TrackingService
        expected_tracking_history = {
            "date": "2025-05-27",
            "day_of_week": "tuesday",
            "overall_compliance_score": 85.0,
            "meals_tracking": test_daily_compliance_data["meals"],
            "cumulative_nutrients": {
                "calories": 870.0,
                "proteins": 50.0,
                "fats": 26.0,
                "carbs": 100.0
            },
            "daily_totals": {
                "water_consumed": 1500.0,
                "weight_recorded": True,
                "latest_weight": 75.2
            }
        }
        message_processor_dependencies[
            "tracking_service"].get_daily_tracking_history.return_value = expected_tracking_history

        # Мокируем DateHelper
        with patch.object(DateHelper, 'get_tracking_date') as mock_get_tracking_date:
            mock_get_tracking_date.return_value = date(2025, 5, 27)

            with patch.object(DateHelper, 'get_day_of_week') as mock_get_day_of_week:
                mock_get_day_of_week.return_value = "tuesday"

                # Act
                result = await message_processor_service._enrich_context_with_state(initial_context, user_id)

                # Assert
                assert result is not None
                assert "daily_tracking_history" in result
                assert "tracking_summary" in result

                # Проверяем историю трекинга
                tracking_history = result["daily_tracking_history"]
                assert tracking_history["date"] == "2025-05-27"
                assert tracking_history["overall_compliance_score"] == 85.0

                # Проверяем сводку трекинга
                tracking_summary = result["tracking_summary"]
                assert tracking_summary["total_calories_consumed"] == 870.0
                assert tracking_summary["total_proteins_consumed"] == 50.0
                assert tracking_summary["compliance_score"] == 85.0
                assert "breakfast" in tracking_summary["completed_meals"]
                assert "lunch" in tracking_summary["completed_meals"]
                assert "dinner" in tracking_summary["skipped_meals"]

                # Проверяем план на сегодня
                assert "today_diet_plan" in result
                today_plan = result["today_diet_plan"]
                assert today_plan["total_calories"] == 1800
                assert len(today_plan["meals"]) == 4

                # Verify calls
                message_processor_dependencies["tracking_service"].get_daily_tracking_history.assert_called_once()

    async def test_enrich_context_without_tracking_data(self, message_processor_service,
                                                        message_processor_dependencies,
                                                        test_user_data):
        """Тестирование обогащения контекста когда нет данных трекинга."""
        # Arrange
        user_id = "test-user-id"
        initial_context = {}

        message_processor_dependencies["user_repository"].get_by_id.return_value = test_user_data
        message_processor_dependencies["diet_service"].get_current_diet.return_value = None
        message_processor_dependencies["tracking_service"].get_daily_tracking_history.return_value = {}

        # Act
        result = await message_processor_service._enrich_context_with_state(initial_context, user_id)

        # Assert
        assert result is not None
        assert "daily_tracking_history" not in result
        assert "tracking_summary" not in result
        assert "today_diet_plan" not in result

    async def test_enrich_context_tracking_service_exception(self, message_processor_service,
                                                             message_processor_dependencies,
                                                             test_user_data):
        """Тестирование обработки исключений в tracking_service при обогащении контекста."""
        # Arrange
        user_id = "test-user-id"
        initial_context = {}

        message_processor_dependencies["user_repository"].get_by_id.return_value = test_user_data
        message_processor_dependencies["diet_service"].get_current_diet.return_value = None
        message_processor_dependencies["tracking_service"].get_daily_tracking_history.side_effect = Exception(
            "Tracking error")

        # Act
        result = await message_processor_service._enrich_context_with_state(initial_context, user_id)

        # Assert
        assert result is not None
        # Контекст должен быть обогащен другими данными, но без истории трекинга
        assert "daily_tracking_history" not in result

    #
    # 3. Интеграционные тесты
    #

    async def test_full_tracking_context_flow(self, tracking_service, tracking_service_dependencies,
                                              test_user_data, test_daily_compliance_data, test_weight_entries):
        """Интеграционный тест полного потока получения контекста трекинга."""
        # Arrange
        user_id = "test-user-id"
        target_date = date(2025, 5, 27)

        # Настройка всех моков
        tracking_service_dependencies["user_repository"].get_by_id.return_value = test_user_data
        tracking_service_dependencies[
            "compliance_repository"].get_daily_compliance.return_value = test_daily_compliance_data
        tracking_service_dependencies["weight_entry_repository"].get_entries_by_user.return_value = test_weight_entries
        tracking_service_dependencies["water_entry_repository"].get_daily_total.return_value = 2000.0

        # Act
        tracking_history = await tracking_service.get_daily_tracking_history(user_id, target_date)

        # Assert - полная проверка структуры данных
        assert tracking_history["date"] == "2025-05-27"
        assert tracking_history["day_of_week"] == "tuesday"
        assert tracking_history["overall_compliance_score"] == 85.0

        # Проверка структуры meals_tracking
        meals = tracking_history["meals_tracking"]
        assert len(meals) == 3  # breakfast, lunch, dinner

        # Проверка breakfast
        breakfast = meals["breakfast"]
        assert breakfast["status"] == "followed"
        assert breakfast["calories_consumed"] == 350.0
        assert breakfast["adherence_percentages"]["calories"] == 100.0

        # Проверка lunch
        lunch = meals["lunch"]
        assert lunch["status"] == "partially"
        assert lunch["calories_consumed"] == 520.0
        assert lunch["adherence_percentages"]["calories"] == 115.6

        # Проверка dinner (пропущен)
        dinner = meals["dinner"]
        assert dinner["status"] == "skipped"
        assert dinner["calories_consumed"] == 0.0

        # Проверка кумулятивных данных
        cumulative = tracking_history["cumulative_nutrients"]
        assert cumulative["calories"] == 870.0
        assert cumulative["proteins"] == 50.0

        # Проверка дневных итогов
        daily_totals = tracking_history["daily_totals"]
        assert daily_totals["water_consumed"] == 2000.0
        assert daily_totals["weight_recorded"] is True
        assert daily_totals["latest_weight"] == 75.2

    async def test_tracking_context_for_partial_day(self, tracking_service, tracking_service_dependencies,
                                                    test_user_data):
        """Тестирование контекста для частично заполненного дня."""
        # Arrange
        user_id = "test-user-id"
        target_date = date(2025, 5, 27)

        # Только завтрак выполнен
        partial_compliance = {
            "user_id": user_id,
            "date": "2025-05-27",
            "overall_score": 25.0,
            "meals": {
                "breakfast": {
                    "status": "followed",
                    "calories_consumed": 350.0,
                    "proteins_consumed": 15.0,
                    "fats_consumed": 8.0,
                    "carbs_consumed": 55.0
                }
            }
        }

        tracking_service_dependencies["user_repository"].get_by_id.return_value = test_user_data
        tracking_service_dependencies["compliance_repository"].get_daily_compliance.return_value = partial_compliance
        tracking_service_dependencies["weight_entry_repository"].get_entries_by_user.return_value = []
        tracking_service_dependencies["water_entry_repository"].get_daily_total.return_value = 500.0

        # Act
        result = await tracking_service.get_daily_tracking_history(user_id, target_date)

        # Assert
        assert result["overall_compliance_score"] == 25.0
        assert len(result["meals_tracking"]) == 1
        assert "breakfast" in result["meals_tracking"]
        assert result["cumulative_nutrients"]["calories"] == 350.0
        assert result["daily_totals"]["water_consumed"] == 500.0
        assert result["daily_totals"]["weight_recorded"] is False

    #
    # 4. Тесты для edge cases
    #

    async def test_tracking_history_with_malformed_compliance_data(self, tracking_service,
                                                                   tracking_service_dependencies,
                                                                   test_user_data):
        """Тестирование обработки некорректных данных соблюдения плана."""
        # Arrange
        user_id = "test-user-id"
        target_date = date(2025, 5, 27)

        # Некорректные данные
        malformed_compliance = {
            "user_id": user_id,
            "date": "2025-05-27",
            "overall_score": 50.0,
            "meals": {
                "breakfast": "invalid_data",  # Некорректный формат
                "lunch": {
                    "status": "followed",
                    # отсутствуют нутриенты
                }
            }
        }

        tracking_service_dependencies["user_repository"].get_by_id.return_value = test_user_data
        tracking_service_dependencies["compliance_repository"].get_daily_compliance.return_value = malformed_compliance
        tracking_service_dependencies["weight_entry_repository"].get_entries_by_user.return_value = []
        tracking_service_dependencies["water_entry_repository"].get_daily_total.return_value = 0.0

        # Act
        result = await tracking_service.get_daily_tracking_history(user_id, target_date)

        # Assert - система должна обработать некорректные данные корректно
        assert result is not None
        assert result["overall_compliance_score"] == 50.0

        # Проверяем, что некорректные данные не обрабатываются
        meals_tracking = result["meals_tracking"]
        assert "breakfast" not in meals_tracking  # Пропущен из-за некорректного формата

        # lunch должен быть обработан, но с нулевыми значениями для отсутствующих полей
        if "lunch" in meals_tracking:
            lunch = meals_tracking["lunch"]
            assert lunch["status"] == "followed"
            assert lunch["calories_consumed"] == 0  # Значение по умолчанию
            assert lunch["proteins_consumed"] == 0

    async def test_tracking_history_performance_with_large_dataset(self, tracking_service,
                                                                   tracking_service_dependencies,
                                                                   test_user_data):
        """Тестирование производительности с большим объемом данных."""
        # Arrange
        user_id = "test-user-id"
        target_date = date(2025, 5, 27)

        # Создаем большой объем данных
        large_compliance_data = {
            "user_id": user_id,
            "date": "2025-05-27",
            "overall_score": 80.0,
            "meals": {}
        }

        # Добавляем много приемов пищи (например, каждый час)
        for hour in range(24):
            meal_key = f"meal_{hour}"
            large_compliance_data["meals"][meal_key] = {
                "status": "followed",
                "calories_consumed": 100.0,
                "proteins_consumed": 10.0,
                "fats_consumed": 5.0,
                "carbs_consumed": 15.0
            }

        tracking_service_dependencies["user_repository"].get_by_id.return_value = test_user_data
        tracking_service_dependencies["compliance_repository"].get_daily_compliance.return_value = large_compliance_data
        tracking_service_dependencies["weight_entry_repository"].get_entries_by_user.return_value = []
        tracking_service_dependencies["water_entry_repository"].get_daily_total.return_value = 3000.0

        # Act
        result = await tracking_service.get_daily_tracking_history(user_id, target_date)

        # Assert
        assert result is not None
        assert len(result["meals_tracking"]) == 24
        assert result["cumulative_nutrients"]["calories"] == 2400.0  # 24 * 100
        assert result["cumulative_nutrients"]["proteins"] == 240.0  # 24 * 10

    #
    # 5. Тесты для вспомогательных функций
    #

    def test_tracking_summary_generation(self):
        """Тестирование генерации сводки трекинга."""
        # Arrange
        tracking_history = {
            "meals_tracking": {
                "breakfast": {"status": "followed"},
                "lunch": {"status": "partially"},
                "dinner": {"status": "skipped"},
                "snack": {"status": "substituted"}
            },
            "cumulative_nutrients": {
                "calories": 1200,
                "proteins": 80,
                "fats": 45,
                "carbs": 120
            },
            "daily_totals": {"water_consumed": 1800},
            "overall_compliance_score": 75
        }

        # Act - симулируем логику создания сводки (как в _enrich_context_with_state)
        completed_meals = [
            meal_type for meal_type, meal_data in tracking_history["meals_tracking"].items()
            if meal_data.get("status") in ["followed", "partially", "substituted"]
        ]

        skipped_meals = [
            meal_type for meal_type, meal_data in tracking_history["meals_tracking"].items()
            if meal_data.get("status") == "skipped"
        ]

        # Assert
        assert len(completed_meals) == 3  # breakfast, lunch, snack
        assert "breakfast" in completed_meals
        assert "lunch" in completed_meals
        assert "snack" in completed_meals

        assert len(skipped_meals) == 1  # dinner
        assert "dinner" in skipped_meals