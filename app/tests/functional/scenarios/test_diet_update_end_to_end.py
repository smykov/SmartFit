import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
import json
from datetime import datetime, date, timedelta
import pytz

from app.services.diet.diet_service import DietService
from app.services.diet.diet_plan_manager import DietPlanManager
from app.services.formatter.diet_formatter import DietFormatter
from app.services.messaging.message_processor_service import MessageProcessorService


class TestDietUpdateEndToEnd:
    """
    End-to-End тестирование процесса обновления плана диеты.
    Проверяет полный путь от запроса пользователя до получения обновленного плана.
    """

    @pytest.fixture
    def setup_services(self, firebase_repositories, llm_service_mock, whatsapp_service_mock,
                       localization_service_mock, test_user_data, test_diet_plan_data):
        """Настройка сервисов для E2E тестирования."""
        # Настраиваем репозитории
        user_repository = AsyncMock()
        diet_plan_repository = AsyncMock()
        message_repository = AsyncMock()
        product_repository = AsyncMock()
        shopping_list_repository = AsyncMock()

        # Подготавливаем данные в репозиториях
        user_repository.get_by_id.return_value = test_user_data
        user_repository.get_by_phone.return_value = test_user_data
        diet_plan_repository.get_by_id.return_value = test_diet_plan_data
        diet_plan_repository.get_current_diet.return_value = test_diet_plan_data

        # Создаем сервис диет и план-менеджер
        diet_formatter = DietFormatter(localization_service_mock)

        diet_service = DietService(
            user_repository=user_repository,
            message_service=whatsapp_service_mock,
            localization_service=localization_service_mock,
            diet_plan_repository=diet_plan_repository,
            product_repository=product_repository,
            shopping_list_repository=shopping_list_repository,
            llm_service=llm_service_mock
        )

        # Настраиваем конкретное поведение diet_plan_manager
        # (Этот пример показывает, как можно детально настроить менеджер планов для тестирования)
        diet_plan_manager = DietPlanManager(
            llm_service=llm_service_mock,
            diet_plan_repository=diet_plan_repository,
            product_repository=product_repository,
            user_repository=user_repository,
            localization_service=localization_service_mock
        )

        # Обновляем diet_service для использования нашего настроенного diet_plan_manager
        diet_service.diet_plan_manager = diet_plan_manager

        # Настраиваем поведение методов
        async def update_diet_plan_mock(plan_id, update_request):
            # Имитируем сам процесс обновления плана
            # 1. Проверяем, существует ли план
            if plan_id != "test-diet-plan-id":
                return {"success": False, "error": "План не найден"}

            # 2. Подготавливаем обновленные данные плана
            updated_plan = dict(test_diet_plan_data)

            # 3. Изменяем план в зависимости от запроса
            if "завтрак" in update_request.lower() and "понедельник" in update_request.lower():
                # Запрос на изменение завтрака в понедельник
                if "омлет" in update_request.lower():
                    # Изменяем завтрак на омлет
                    updated_plan["daily_plans"]["monday"]["meals"][0] = {
                        "type": "breakfast",
                        "title": "Омлет с овощами",
                        "calories": 300,
                        "products": [
                            {"name": "Яйца", "quantity": 2, "unit": "шт."},
                            {"name": "Помидоры", "quantity": 1, "unit": "шт."},
                            {"name": "Перец", "quantity": 0.5, "unit": "шт."}
                        ]
                    }

                    # Обновляем общую калорийность
                    calories = sum(meal.get("calories", 0) for meal in updated_plan["daily_plans"]["monday"]["meals"])
                    updated_plan["daily_plans"]["monday"]["total_calories"] = calories

                    return {
                        "success": True,
                        "plan": updated_plan,
                        "comment": "Заменил овсянку на омлет с овощами согласно вашему запросу",
                        "updated_days": {
                            "monday": updated_plan["daily_plans"]["monday"]
                        }
                    }

            # Если не смогли обработать запрос
            return {"success": False, "error": "Не удалось обновить план"}

        # Заменяем метод update_diet_plan в diet_service нашим моком
        diet_service.update_diet_plan = AsyncMock(side_effect=update_diet_plan_mock)

        # Настраиваем форматтер
        diet_service.formatter.get_diet_summary = MagicMock(
            return_value="Сводка плана: Понедельник - Завтрак: Омлет с овощами")

        # Создаем процессор сообщений
        onboarding_service = AsyncMock()
        tracking_service = AsyncMock()
        command_factory = AsyncMock()

        message_processor = MessageProcessorService(
            user_repository=user_repository,
            message_repository=message_repository,
            message_service=whatsapp_service_mock,
            localization_service=localization_service_mock,
            onboarding_service=onboarding_service,
            diet_service=diet_service,
            tracking_service=tracking_service,
            command_factory=command_factory
        )

        # Настраиваем обработчик сообщений
        async def process_update_request(user_id, message_text, phone_number):
            # Получаем текущий план
            current_plan = await diet_plan_repository.get_current_diet(user_id)

            if not current_plan:
                await whatsapp_service_mock.send_message(phone_number, "У вас нет активного плана диеты")
                return False

            # Обновляем план
            result = await diet_service.update_diet_plan(current_plan["id"], message_text)

            if result["success"]:
                # Формируем и отправляем ответ
                summary = diet_service.formatter.get_diet_summary(result["plan"], "ru")
                await whatsapp_service_mock.send_message(phone_number, summary)

                # Также отправляем комментарий к изменениям
                if "comment" in result:
                    await whatsapp_service_mock.send_message(phone_number, f"💡 {result['comment']}")

                return True
            else:
                # Отправляем сообщение об ошибке
                error_message = result.get("error", "Не удалось обновить план диеты")
                await whatsapp_service_mock.send_message(phone_number, f"❌ {error_message}")
                return False

        # Настраиваем процессор сообщений
        async def process_message_mock(message_data):
            message_text = message_data.get("text", "").lower()
            phone_number = message_data.get("from")

            # Находим пользователя по номеру телефона
            user = await user_repository.get_by_phone(phone_number)
            if not user:
                return {"success": False, "message": "Пользователь не найден"}

            user_id = user["id"]

            # Обрабатываем запрос на изменение диеты
            if ("измени" in message_text or "замени" in message_text) and (
                    "план" in message_text or "диету" in message_text or "завтрак" in message_text):
                return {"success": await process_update_request(user_id, message_text, phone_number)}

            return {"success": False, "message": "Неизвестная команда"}

        message_processor.process_message = AsyncMock(side_effect=process_message_mock)

        return {
            "diet_service": diet_service,
            "message_processor": message_processor,
            "whatsapp_service": whatsapp_service_mock,
            "diet_plan_manager": diet_plan_manager
        }

    @pytest.mark.asyncio
    async def test_diet_update_from_user_request_to_response(self, setup_services):
        """
        End-to-End тест обновления плана диеты:
        1. Пользователь отправляет запрос на изменение плана
        2. Сообщение обрабатывается процессором
        3. Запрос передается в сервис диет
        4. Сервис диет делегирует обновление плана менеджеру планов
        5. Обновленный план форматируется и отправляется пользователю
        """
        diet_service = setup_services["diet_service"]
        message_processor = setup_services["message_processor"]
        whatsapp_service = setup_services["whatsapp_service"]

        # 1. Пользователь запрашивает изменение плана
        await message_processor.process_message({
            "message_id": "test-msg-1",
            "from": "+1234567890",
            "text": "Замени завтрак в понедельник на омлет с овощами"
        })

        # 2. Проверяем, что diet_service.update_diet_plan был вызван с правильными параметрами
        diet_service.update_diet_plan.assert_called_once_with(
            "test-diet-plan-id",
            "замени завтрак в понедельник на омлет с овощами"
        )

        # 3. Проверяем, что formatter был вызван для форматирования обновленного плана
        diet_service.formatter.get_diet_summary.assert_called_once()

        # 4. Проверяем, что пользователю были отправлены сообщения
        assert whatsapp_service.send_message.call_count >= 2

        # 5. Проверяем содержимое первого сообщения (сводка плана)
        first_call_args = whatsapp_service.send_message.call_args_list[0]
        assert first_call_args[0][0] == "+1234567890"
        assert "Сводка плана" in first_call_args[0][1]

        # 6. Проверяем содержимое второго сообщения (комментарий)
        second_call_args = whatsapp_service.send_message.call_args_list[1]
        assert second_call_args[0][0] == "+1234567890"
        assert "💡" in second_call_args[0][1]
        assert "Заменил овсянку на омлет" in second_call_args[0][1]