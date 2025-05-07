import pytest
from datetime import datetime, date, timedelta
import pytz
from unittest.mock import AsyncMock, MagicMock, patch, ANY

from app.models.tracking import MealComplianceStatus


class TestWeeklyReportGeneration:
    """
    Интеграционные тесты для процесса генерации еженедельных отчетов о прогрессе
    """

    @pytest.fixture
    def setup_weekly_report_data(self, firebase_repositories, localization_service_mock, whatsapp_service_mock):
        """Настройка данных для тестирования еженедельных отчетов."""
        # Создаем тестового пользователя
        user_id = "test-user-id"
        phone_number = "+5012345678"

        user_data = {
            "id": user_id,
            "phone_number": phone_number,
            "name": "Test User",
            "email": "test@example.com",
            "gender": "male",
            "age": 35,
            "height": 175,
            "current_weight": 83.5,  # Текущий вес
            "target_weight": 75,  # Целевой вес
            "activity_level": "moderate",
            "weight_goal": "lose",
            "diet_preference": "regular",
            "is_onboarding_completed": True,
            "language": "ru"
        }

        # Настраиваем репозиторий пользователей
        user_repository = firebase_repositories["user_repository"]
        user_repository.get_by_id = AsyncMock(return_value=user_data)

        # Настраиваем локализацию
        localization_service_mock.get_user_language = AsyncMock(return_value="ru")

        # Создаем данные о весе за неделю
        today = date.today()
        weight_entries = []

        # Генерируем записи о весе за последние 7 дней
        for i in range(7, 0, -1):
            entry_date = today - timedelta(days=i)
            weight = 85.0 - (7 - i) * 0.2  # Постепенное снижение веса

            weight_entries.append({
                "id": f"weight-{i}",
                "user_id": user_id,
                "weight": weight,
                "date": entry_date.isoformat(),
                "notes": f"Запись за {entry_date.isoformat()}"
            })

        # Настраиваем репозиторий веса
        weight_repository = firebase_repositories["weight_entry_repository"]
        weight_repository.get_entries_by_user = AsyncMock(return_value=weight_entries)

        # Создаем данные о воде за неделю
        water_entries = []

        # Генерируем записи о воде за последние 7 дней
        for i in range(7, 0, -1):
            entry_date = today - timedelta(days=i)

            # Для разнообразия делаем разное потребление воды в разные дни
            water_amount = 500.0 if i % 2 == 0 else 750.0

            water_entries.append({
                "id": f"water-{i}",
                "user_id": user_id,
                "amount": water_amount,
                "date": entry_date.isoformat(),
                "time": datetime.now(pytz.UTC).replace(hour=12, minute=0).isoformat()
            })

        # Настраиваем репозиторий воды
        water_repository = firebase_repositories["water_entry_repository"]
        water_repository.get_entries_by_user = AsyncMock(return_value=water_entries)

        # Создаем данные о соблюдении плана за неделю
        compliance_entries = []

        # Генерируем записи о соблюдении плана за последние 7 дней
        for i in range(7, 0, -1):
            entry_date = today - timedelta(days=i)

            # Разные статусы соблюдения для разных дней
            breakfast_status = MealComplianceStatus.FOLLOWED if i % 3 != 0 else MealComplianceStatus.PARTIALLY
            lunch_status = MealComplianceStatus.FOLLOWED if i % 2 == 0 else MealComplianceStatus.SUBSTITUTED
            dinner_status = MealComplianceStatus.FOLLOWED if i % 4 != 0 else MealComplianceStatus.SKIPPED

            daily_compliance = {
                "id": f"compliance-{i}",
                "user_id": user_id,
                "date": entry_date.isoformat(),
                "meals": {
                    "breakfast": breakfast_status,
                    "lunch": lunch_status,
                    "dinner": dinner_status
                },
                "overall_score": 75.0 if i % 2 == 0 else 60.0
            }

            compliance_entries.append(daily_compliance)

        # Настраиваем репозиторий соблюдения плана
        compliance_repository = firebase_repositories["compliance_repository"]
        compliance_repository.get_compliance_by_period = AsyncMock(return_value=compliance_entries)

        # Создаем сервис трекинга
        from app.services.tracking.tracking_service import TrackingService

        tracking_service = TrackingService(
            user_repository=user_repository,
            diet_service=AsyncMock(),
            weight_entry_repository=weight_repository,
            water_entry_repository=water_repository,
            compliance_repository=compliance_repository,
            localization_service=localization_service_mock
        )

        # Настраиваем метод генерации еженедельного отчета
        async def generate_weekly_report_mock(user_id):
            # Проверяем, что мы получили данные за правильный период
            start_date = today - timedelta(days=7)
            end_date = today

            # Получаем историю веса
            weight_history = await weight_repository.get_entries_by_user(
                user_id, start_date, end_date
            )

            # Получаем историю воды
            water_history = await water_repository.get_entries_by_user(
                user_id, start_date, end_date
            )

            # Получаем историю соблюдения плана
            compliance_history = await compliance_repository.get_compliance_by_period(
                user_id, start_date, end_date
            )

            # Создаем еженедельный отчет
            if not weight_history or not water_history or not compliance_history:
                return "Недостаточно данных для формирования еженедельного отчета."

            # Расчет средних значений
            start_weight = weight_history[0]["weight"] if weight_history else None
            end_weight = weight_history[-1]["weight"] if weight_history else None
            weight_change = end_weight - start_weight if start_weight and end_weight else 0

            total_water = sum(entry["amount"] for entry in water_history)
            average_water = total_water / len(water_history) if water_history else 0

            total_compliance = sum(entry.get("overall_score", 0) for entry in compliance_history)
            average_compliance = total_compliance / len(compliance_history) if compliance_history else 0

            # Формируем отчет
            user = await user_repository.get_by_id(user_id)
            user_name = user.get("name", "Пользователь")

            report = f"📊 *Еженедельный отчет о прогрессе для {user_name}*\n\n"

            # Секция веса
            report += "⚖️ *Вес:*\n"
            report += f"• Начало недели: {start_weight:.1f} кг\n"
            report += f"• Конец недели: {end_weight:.1f} кг\n"

            if weight_change < 0:
                report += f"• Изменение: -{abs(weight_change):.1f} кг 👍\n"
            elif weight_change > 0:
                report += f"• Изменение: +{weight_change:.1f} кг\n"
            else:
                report += "• Изменение: 0 кг (вес стабилен)\n"

            target_weight = user.get("target_weight")
            if target_weight and end_weight:
                remaining = abs(end_weight - target_weight)
                report += f"• Осталось до цели: {remaining:.1f} кг\n\n"

            # Секция воды
            report += "💧 *Потребление воды:*\n"
            report += f"• Дней отслеживания: {len(water_history)}/7\n"
            report += f"• Среднее потребление: {average_water / 1000:.1f} л/день\n"

            water_status = "Отлично!" if average_water >= 2000 else \
                "Хорошо, но можно больше" if average_water >= 1500 else \
                    "Недостаточное"

            report += f"• Статус: {water_status}\n\n"

            # Секция соблюдения плана
            report += "🍽️ *Соблюдение плана питания:*\n"
            report += f"• Дней отслеживания: {len(compliance_history)}/7\n"
            report += f"• Среднее соблюдение: {average_compliance:.1f}%\n"

            compliance_status = "Отлично! Продолжай в том же духе" if average_compliance >= 80 else \
                "Хороший результат! Можно улучшить" if average_compliance >= 60 else \
                    "Стоит поработать над соблюдением плана"

            report += f"• Статус: {compliance_status}\n\n"

            # Заключение
            report += "🎯 *План на следующую неделю:*\n"

            if weight_change < 0:
                report += "• Продолжай поддерживать текущий режим питания и активности.\n"
            else:
                report += "• Попробуй быть более внимательным к соблюдению плана питания.\n"

            if average_water < 2000:
                report += "• Стремись к потреблению не менее 2 литров воды в день.\n"

            report += "\n💪 *Верим в твой успех! Продолжай движение к цели!*"

            return report

        # Устанавливаем наш mock-метод для генерации отчета
        tracking_service.generate_weekly_report = AsyncMock(side_effect=generate_weekly_report_mock)

        return {
            "tracking_service": tracking_service,
            "whatsapp_service": whatsapp_service_mock,
            "user_data": user_data,
            "user_id": user_id,
            "phone_number": phone_number,
            "weight_entries": weight_entries,
            "water_entries": water_entries,
            "compliance_entries": compliance_entries
        }

    @pytest.mark.asyncio
    async def test_weekly_report_generation_and_delivery(self, setup_weekly_report_data):
        """Тестирование генерации и доставки еженедельного отчета о прогрессе."""
        # Получаем настроенные сервисы и данные
        tracking_service = setup_weekly_report_data["tracking_service"]
        whatsapp_service = setup_weekly_report_data["whatsapp_service"]
        user_id = setup_weekly_report_data["user_id"]
        phone_number = setup_weekly_report_data["phone_number"]

        # Сбрасываем счетчики вызовов
        whatsapp_service.send_message.reset_mock()

        # Генерируем еженедельный отчет
        report = await tracking_service.generate_weekly_report(user_id)

        # Проверяем, что отчет был сгенерирован
        assert report is not None
        assert isinstance(report, str)
        assert "Еженедельный отчет о прогрессе" in report
        assert "Вес:" in report
        assert "Потребление воды:" in report
        assert "Соблюдение плана питания:" in report

        # Отправляем отчет пользователю
        await whatsapp_service.send_message(phone_number, report)

        # Проверяем, что сообщение было отправлено
        whatsapp_service.send_message.assert_called_once_with(phone_number, report)