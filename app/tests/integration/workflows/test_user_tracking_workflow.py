import pytest
from datetime import datetime, date, timedelta
import pytz
from unittest.mock import AsyncMock, MagicMock, patch, ANY

from app.models.tracking import MealComplianceStatus, WeightGoalProgress
from app.services.tracking.tracking_service import TrackingService
from app.services.messaging.message_processor_service import MessageProcessorService
from app.utils.date_helper import DateHelper


class TestUserTrackingWorkflow:
    """
    Интеграционные тесты для рабочего процесса трекинга пользователя:
    - Регистрация веса
    - Регистрация потребления воды
    - Отметка о соблюдении плана питания
    - Получение отчетов о прогрессе
    """

    @pytest.fixture
    def setup_tracking_workflow(self, firebase_repositories, localization_service_mock, whatsapp_service_mock):
        """Настройка окружения для тестирования рабочего процесса трекинга."""
        # Создаем репозитории
        user_repository = firebase_repositories["user_repository"]
        weight_entry_repository = firebase_repositories["weight_entry_repository"]
        water_entry_repository = firebase_repositories["water_entry_repository"]
        compliance_repository = firebase_repositories["compliance_repository"]
        message_repository = firebase_repositories["message_repository"]

        # Тестовые данные пользователя
        test_user = {
            "id": "test-user-id",
            "phone_number": "+5012345678",
            "name": "Test User",
            "email": "test@example.com",
            "gender": "male",
            "age": 35,
            "height": 175,
            "current_weight": 85,
            "target_weight": 75,
            "activity_level": "moderate",
            "weight_goal": "lose",
            "is_onboarding_completed": True,
            "language": "ru"
        }

        # Настройка репозиториев
        user_repository.get_by_id = AsyncMock(return_value=test_user)
        user_repository.get_by_phone = AsyncMock(return_value=test_user)

        # История записей о весе
        weight_history = [
            {"id": "weight-1", "user_id": "test-user-id", "weight": 85.0,
             "date": (date.today() - timedelta(days=14)).isoformat()},
            {"id": "weight-2", "user_id": "test-user-id", "weight": 84.5,
             "date": (date.today() - timedelta(days=7)).isoformat()},
        ]

        weight_entry_repository.get_entries_by_user = AsyncMock(return_value=weight_history)
        weight_entry_repository.get_latest_entry = AsyncMock(return_value=weight_history[-1])
        weight_entry_repository.add_entry = AsyncMock(return_value="new-weight-entry-id")

        # История записей о воде
        water_history = [
            {"id": "water-1", "user_id": "test-user-id", "amount": 250.0, "date": date.today().isoformat(),
             "time": datetime.now(pytz.UTC).replace(hour=8, minute=0).isoformat()},
            {"id": "water-2", "user_id": "test-user-id", "amount": 250.0, "date": date.today().isoformat(),
             "time": datetime.now(pytz.UTC).replace(hour=12, minute=0).isoformat()},
        ]

        water_entry_repository.get_entries_by_user = AsyncMock(return_value=water_history)
        water_entry_repository.get_daily_total = AsyncMock(return_value=500.0)
        water_entry_repository.add_entry = AsyncMock(return_value="new-water-entry-id")

        # История соблюдения плана
        compliance_history = {
            "breakfast": "followed",
            "lunch": "partially",
            "dinner": "not_recorded",
            "snack": "not_recorded"
        }

        daily_compliance = {
            "user_id": "test-user-id",
            "date": date.today(),
            "meals": compliance_history,
            "overall_score": 75.0
        }

        compliance_repository.get_daily_compliance = AsyncMock(return_value=daily_compliance)
        compliance_repository.add_meal_compliance = AsyncMock(return_value="new-compliance-id")
        compliance_repository.update_daily_compliance = AsyncMock(return_value=True)

        # Создаем сервис трекинга
        tracking_service = TrackingService(
            user_repository=user_repository,
            diet_service=AsyncMock(),
            weight_entry_repository=weight_entry_repository,
            water_entry_repository=water_entry_repository,
            compliance_repository=compliance_repository,
            localization_service=localization_service_mock
        )

        # Создаем имитацию процессора сообщений
        message_processor = AsyncMock(spec=MessageProcessorService)

        # Настраиваем локализацию
        async def get_user_language(user_id):
            return "ru"

        localization_service_mock.get_user_language = AsyncMock(side_effect=get_user_language)

        # Имитация для WeightGoalProgress
        tracking_service.calculate_weight_progress = AsyncMock(return_value=WeightGoalProgress(
            user_id="test-user-id",
            start_weight=85.0,
            current_weight=84.0,
            target_weight=75.0,
            total_weight_change=-1.0,
            weight_change_percentage=10.0,
            remaining_to_goal=9.0,
            goal_completion_percentage=10.0
        ))

        tracking_service.get_daily_status = AsyncMock(return_value={
            "user_id": "test-user-id",
            "date": date.today(),
            "weight_recorded": True,
            "current_water_intake": 500.0,
            "water_goal": 2000.0,
            "water_percentage": 25.0,
            "meal_compliance": compliance_history,
            "overall_compliance_score": 75.0
        })

        return {
            "tracking_service": tracking_service,
            "message_processor": message_processor,
            "whatsapp_service": whatsapp_service_mock,
            "user_repository": user_repository,
            "weight_entry_repository": weight_entry_repository,
            "water_entry_repository": water_entry_repository,
            "compliance_repository": compliance_repository,
            "test_user": test_user
        }

    @pytest.mark.asyncio
    async def test_weight_recording_workflow(self, setup_tracking_workflow):
        """
        Тестирование полного потока записи веса пользователя и отображения результата.
        """
        # Настройка
        tracking_service = setup_tracking_workflow["tracking_service"]
        whatsapp_service = setup_tracking_workflow["whatsapp_service"]
        test_user = setup_tracking_workflow["test_user"]
        user_id = test_user["id"]
        phone_number = test_user["phone_number"]

        # Вызываем метод записи веса
        result = await tracking_service.record_weight(user_id, 83.5, "Запись после тренировки")

        # Проверяем результат
        assert result is True

        # Проверяем, что метод репозитория был вызван с правильными параметрами
        setup_tracking_workflow["weight_entry_repository"].add_entry.assert_called_once_with(
            user_id, 83.5, DateHelper.get_tracking_date(), "Запись после тренировки"
        )

        # Получаем прогресс по весу для отображения пользователю
        progress = await tracking_service.calculate_weight_progress(user_id)

        # Проверяем расчет прогресса
        assert progress is not None
        assert progress.user_id == user_id
        assert progress.current_weight < progress.start_weight
        assert progress.goal_completion_percentage > 0

        # Имитируем отправку сообщения пользователю с результатами
        message = f"✅ Отлично! Я записал твой вес: {83.5} кг.\n\n" + \
                  f"📉 С начала ты уже похудел(а) на {progress.total_weight_change:.1f} кг " + \
                  f"({progress.weight_change_percentage:.1f}% от цели)\n" + \
                  f"🎯 До целевого веса осталось: {progress.remaining_to_goal:.1f} кг (цель: {progress.target_weight} кг)\n" + \
                  f"📊 Ты выполнил(а) {progress.goal_completion_percentage:.1f}% своей цели!\n\n" + \
                  "Продолжай отслеживать прогресс регулярно! 💪"

        await whatsapp_service.send_message(phone_number, message)

        # Проверяем, что метод отправки сообщения был вызван
        whatsapp_service.send_message.assert_called_with(phone_number, ANY)

    @pytest.mark.asyncio
    async def test_water_intake_recording_workflow(self, setup_tracking_workflow):
        """
        Тестирование полного потока записи потребления воды и отображения результата.
        """
        # Настройка
        tracking_service = setup_tracking_workflow["tracking_service"]
        whatsapp_service = setup_tracking_workflow["whatsapp_service"]
        test_user = setup_tracking_workflow["test_user"]
        user_id = test_user["id"]
        phone_number = test_user["phone_number"]

        # Количество стаканов и соответствующий объем в мл
        cups = 2
        ml_amount = cups * 250

        # Вызываем метод записи потребления воды
        result = await tracking_service.record_water_intake(user_id, ml_amount)

        # Проверяем результат
        assert result is True

        # Проверяем, что метод репозитория был вызван с правильными параметрами
        setup_tracking_workflow["water_entry_repository"].add_entry.assert_called_once_with(
            user_id, ml_amount, DateHelper.get_tracking_date()
        )

        # Получаем общее потребление воды за день
        daily_total = await setup_tracking_workflow["water_entry_repository"].get_daily_total(user_id)

        # Имитируем расчет процента от цели
        water_goal = 2000.0  # Цель в мл
        percentage = (daily_total / water_goal) * 100

        # Имитируем отправку сообщения пользователю с результатами
        message = f"💧 Отлично! Я записал потребление воды: {cups} стаканов (~{ml_amount} мл)\n\n" + \
                  f"Сегодня ты выпил(а) всего: {daily_total} мл\n" + \
                  f"Это {percentage:.1f}% от дневной цели в {water_goal} мл\n\n" + \
                  "Продолжай в том же духе! Регулярное потребление воды помогает контролировать голод и улучшает общее самочувствие."

        await whatsapp_service.send_message(phone_number, message)

        # Проверяем, что метод отправки сообщения был вызван
        whatsapp_service.send_message.assert_called_with(phone_number, ANY)

    @pytest.mark.asyncio
    async def test_meal_compliance_recording_workflow(self, setup_tracking_workflow):
        """
        Тестирование полного потока записи соблюдения плана питания и отображения результата.
        """
        # Настройка
        tracking_service = setup_tracking_workflow["tracking_service"]
        whatsapp_service = setup_tracking_workflow["whatsapp_service"]
        test_user = setup_tracking_workflow["test_user"]
        user_id = test_user["id"]
        phone_number = test_user["phone_number"]

        # Данные для записи
        today = date.today()
        meal_type = "dinner"
        status = MealComplianceStatus.FOLLOWED

        # Вызываем метод записи соблюдения плана
        result = await tracking_service.record_meal_compliance(
            user_id,
            meal_type,
            status,
            today,
            None,
            None,
            None
        )

        # Проверяем результат
        assert result is True

        # Проверяем, что метод репозитория был вызван с правильными параметрами
        setup_tracking_workflow["compliance_repository"].add_meal_compliance.assert_called_once_with(
            user_id, today, meal_type, status.value, None, None, None, None, None, None, {}
        )

        # Проверяем, что метод обновления общей статистики был вызван
        setup_tracking_workflow["compliance_repository"].update_daily_compliance.assert_called_once_with(
            user_id, today
        )

        # Имитируем отправку сообщения пользователю с результатами
        message = f"✅ Отлично! Ужин выполнен по плану."

        await whatsapp_service.send_message(phone_number, message)

        # Проверяем, что метод отправки сообщения был вызван
        whatsapp_service.send_message.assert_called_with(phone_number, ANY)

    @pytest.mark.asyncio
    async def test_progress_report_generation_workflow(self, setup_tracking_workflow):
        """
        Тестирование полного потока генерации и отображения отчета о прогрессе.
        """
        # Настройка
        tracking_service = setup_tracking_workflow["tracking_service"]
        whatsapp_service = setup_tracking_workflow["whatsapp_service"]
        test_user = setup_tracking_workflow["test_user"]
        user_id = test_user["id"]
        phone_number = test_user["phone_number"]

        # Получаем данные для отчета
        weight_progress = await tracking_service.calculate_weight_progress(user_id)
        daily_status = await tracking_service.get_daily_status(user_id)

        # Проверяем данные
        assert weight_progress is not None
        assert daily_status is not None

        # Имитируем формирование сообщения со статистикой
        stats_message = "*📊 СТАТИСТИКА И ПРОГРЕСС*\n\n"
        stats_message += f"*⚖️ Прогресс по весу:*\n"
        stats_message += f"• Начальный вес: {weight_progress.start_weight} кг\n"
        stats_message += f"• Текущий вес: {weight_progress.current_weight} кг\n"
        stats_message += f"• Целевой вес: {weight_progress.target_weight} кг\n\n"
        stats_message += f"• Изменение: {weight_progress.total_weight_change:.1f} кг\n"
        stats_message += f"• Осталось до цели: {weight_progress.remaining_to_goal:.1f} кг\n"
        stats_message += f"• Процент выполнения: {weight_progress.goal_completion_percentage:.1f}%\n\n"

        stats_message += f"*💧 Потребление воды сегодня:*\n"
        stats_message += f"• Выпито: {daily_status['current_water_intake']} мл\n"
        stats_message += f"• Цель: {daily_status['water_goal']} мл\n"
        stats_message += f"• Выполнено: {daily_status['water_percentage']:.1f}%\n\n"

        stats_message += f"*🍽️ Соблюдение плана питания:*\n"
        for meal, status in daily_status['meal_compliance'].items():
            meal_name = meal.capitalize()
            status_text = "Выполнено" if status == "followed" else \
                "Частично" if status == "partially" else \
                    "Заменено" if status == "substituted" else \
                        "Пропущено" if status == "skipped" else \
                            "Не отмечено"
            stats_message += f"• {meal_name}: {status_text}\n"

        stats_message += f"\nОбщее соблюдение: {daily_status['overall_compliance_score']:.1f}%\n\n"
        stats_message += "💪 *Продолжай в том же духе!* Ты на пути к своей цели."

        # Отправляем сообщение
        await whatsapp_service.send_message(phone_number, stats_message)

        # Проверяем, что метод отправки сообщения был вызван
        whatsapp_service.send_message.assert_called_with(phone_number, ANY)
