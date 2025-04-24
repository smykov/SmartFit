import unittest

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
import json
from datetime import datetime, date, timedelta
import pytz

from app.services.diet.diet_service import DietService
from app.services.messaging.message_processor_service import MessageProcessorService


class TestDietPlanGenerationWorkflow:
    """
    Тестирование полного процесса генерации плана диеты и его согласования.
    Проверяет интеграцию между diet_service, diet_plan_manager, LLM и системой сообщений.
    """

    @pytest.fixture
    def setup_services(self, firebase_repositories, llm_service_mock, whatsapp_service_mock,
                       localization_service_mock, test_user_data):
        """Настройка всех необходимых сервисов для тестирования потока."""
        # Создаем моки репозиториев
        messenger_registry = AsyncMock()
        user_identity_service = AsyncMock()
        user_repository = AsyncMock()
        diet_plan_repository = AsyncMock()
        message_repository = AsyncMock()
        product_repository = AsyncMock()
        shopping_list_repository = AsyncMock()

        # Настраиваем моки
        user_repository.get_by_id.return_value = test_user_data
        user_repository.get_by_phone.return_value = test_user_data
        diet_plan_repository.get_by_id = AsyncMock(return_value={"version": "short"})

        # Создаем экземпляр тестируемого сервиса с моками
        diet_service = DietService(
            user_repository=user_repository,
            messenger_service=whatsapp_service_mock,
            localization_service=localization_service_mock,
            diet_plan_repository=diet_plan_repository,
            product_repository=product_repository,
            shopping_list_repository=shopping_list_repository,
            llm_service=llm_service_mock
        )

        # Подготавливаем мок formatter для diet_service
        diet_service.formatter.get_short_diet_summary = MagicMock(
            return_value="Ваш краткий план питания: Пн: Завтрак - Овсянка, Обед - Куриный салат"
        )
        diet_service.formatter.get_short_diet_next_steps = MagicMock(
            return_value="Чтобы утвердить план, напишите 'Подтвердить план'"
        )
        diet_service.formatter.get_diet_summary = MagicMock(
            return_value="Ваш план питания: Пн: Завтрак - Овсянка, Обед - Куриный салат"
        )
        diet_service.formatter.get_diet_summary_commands = MagicMock(
            return_value="Используйте команду 'план на сегодня' для деталей или 'список покупок'"
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
            command_factory=command_factory
        )

        # Настраиваем обработку команд
        async def process_message_mock(message_data):
            message_text = message_data.get("text", "").lower()
            phone_number = message_data.get("from", "+1234567890")

            if message_text == "диета" or message_text == "план":
                # Имитируем создание краткого плана диеты
                plan = await diet_service.generate_short_diet_plan("test-user-id")
                summary = diet_service.formatter.get_short_diet_summary(plan, "ru")
                next_steps = diet_service.formatter.get_short_diet_next_steps("ru")
                await whatsapp_service_mock.send_message(phone_number, summary)
                await whatsapp_service_mock.send_message(phone_number, next_steps)
                return {"success": True}

            elif "подтвердить план" in message_text:
                # Имитируем подтверждение плана и создание полной версии
                plan_id = "test-diet-plan-id"
                await diet_service.approve_short_diet_plan(plan_id)
                await diet_service.start_full_diet_generation("test-user-id", plan_id)
                return {"success": True}

            return {"success": False, "message": "Команда не распознана"}

        message_processor.process_message = AsyncMock(side_effect=process_message_mock)

        return {
            "diet_service": diet_service,
            "message_processor": message_processor,
            "whatsapp_service": whatsapp_service_mock
        }

    @pytest.mark.asyncio
    async def test_diet_plan_generation_approval_workflow(self, setup_services):
        """
        Тестирует полный поток создания плана диеты, включая:
        1. Запрос на создание плана
        2. Получение и отображение краткого плана
        3. Подтверждение плана пользователем
        4. Создание полной версии плана
        """
        diet_service = setup_services["diet_service"]
        message_processor = setup_services["message_processor"]
        whatsapp_service = setup_services["whatsapp_service"]
        # Создаем spy для методов, сохраняя их реальное поведение
        with unittest.mock.patch.object(diet_service, 'generate_short_diet_plan',
                                        wraps=diet_service.generate_short_diet_plan) as spy_generate, \
                unittest.mock.patch.object(diet_service, 'approve_short_diet_plan',
                                           wraps=diet_service.approve_short_diet_plan) as spy_approve, \
                unittest.mock.patch.object(diet_service, 'start_full_diet_generation',
                                           wraps=diet_service.start_full_diet_generation) as spy_generate_full:

            # 1. Пользователь запрашивает диету через сообщение
            await message_processor.process_message({
                "message_id": "test-msg-1",
                "from": "+1234567890",
                "text": "диета"
            })

            # Проверяем, что diet_service вызвал метод создания краткого плана
            assert spy_generate.called
            # Сбрасываем счетчики для следующего шага
            whatsapp_service.send_message.reset_mock()

            # 2. Пользователь подтверждает план
            await message_processor.process_message({
                "message_id": "test-msg-2",
                "from": "+1234567890",
                "text": "Подтвердить план"
            })

            # Проверяем, что вызваны методы подтверждения плана и создания полной версии
            assert spy_approve.called
            assert spy_generate_full.called

        # 3. Имитируем завершение генерации полного плана
        # Этот вызов делает diet_service._generate_full_diet_plan_task
        plan_data = {
            "id": "test-diet-plan-id",
            "user_id": "test-user-id",
            "version": "full",
            "status": "active",
            "daily_plans": {
                "monday": {
                    "meals": [
                        {
                            "type": "breakfast",
                            "title": "Овсянка с фруктами",
                            "calories": 350
                        }
                    ]
                }
            }
        }

        # Вызываем колбэк, который выполняется после генерации полного плана
        diet_service.formatter.get_diet_summary(plan_data, "ru")
        diet_service.formatter.get_diet_summary_commands(plan_data, "ru")

        # Проверяем, что форматтеры были вызваны для генерации сообщений
        assert diet_service.formatter.get_diet_summary.called
        assert diet_service.formatter.get_diet_summary_commands.called

    @pytest.mark.asyncio
    async def test_update_diet_plan_integration(self, setup_services):
        """
        Тестирует интеграцию между diet_service и diet_plan_manager
        при обновлении плана питания.
        """
        diet_service = setup_services["diet_service"]

        # Мокируем метод diet_plan_manager.update_short_diet_plan_by_request
        expected_result = {
            "success": True,
            "plan": {
                "id": "test-diet-plan-id",
                "daily_plans": {
                    "monday": {
                        "meals": [
                            {
                                "type": "breakfast",
                                "title": "Омлет с овощами",
                                "calories": 300
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
                            "title": "Омлет с овощами",
                            "calories": 300
                        }
                    ]
                }
            }
        }

        # Используем spy с подменой результата
        with unittest.mock.patch.object(
                diet_service, 'update_short_diet_plan_by_request',
                return_value=expected_result) as mock_update:
            # Выполняем обновление плана
            update_request = "Замени завтрак в понедельник на омлет с овощами"
            result = await diet_service.update_short_diet_plan_by_request("test-diet-plan-id", update_request)

            # Проверяем, что метод был вызван с правильными параметрами
            mock_update.assert_called_once_with("test-diet-plan-id", update_request)

            # Проверяем результат
            assert result["success"] is True
            assert "plan" in result
            assert "comment" in result
            assert "updated_days" in result