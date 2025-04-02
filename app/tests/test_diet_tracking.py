import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime, date, timedelta
import pytz

from app.services.diet_service import DietService
from app.services.tracking_service import TrackingService
from app.templates.formatting_helpers import (
    format_message_with_emojis,
    create_meal_emoji,
    get_relevance_stars,
    translate_day_name,
    translate_meal_type
)
from app.models.tracking import MealComplianceStatus


class TestFormattingHelpers(unittest.TestCase):
    """Тесты для помощников форматирования"""

    def test_format_message_with_emojis(self):
        """Тест форматирования сообщения с эмодзи"""
        message = format_message_with_emojis("greeting", "Hello, world!")
        self.assertIn("👋", message)
        self.assertIn("*GREETING*", message)
        self.assertIn("Hello, world!", message)

    def test_create_meal_emoji(self):
        """Тест создания эмодзи для типа приема пищи"""
        self.assertEqual(create_meal_emoji("breakfast"), "🍳")
        self.assertEqual(create_meal_emoji("lunch"), "🍲")
        self.assertEqual(create_meal_emoji("dinner"), "🍽️")
        self.assertEqual(create_meal_emoji("snack"), "🥪")
        self.assertEqual(create_meal_emoji("unknown"), "🍴")

    def test_get_relevance_stars(self):
        """Тест создания звездочек для релевантности"""
        self.assertEqual(get_relevance_stars(10), "★★★★★")
        self.assertEqual(get_relevance_stars(8), "★★★★")
        self.assertEqual(get_relevance_stars(6), "★★★")
        self.assertEqual(get_relevance_stars(4), "★★")
        self.assertEqual(get_relevance_stars(2), "★")
        self.assertEqual(get_relevance_stars(None), "")

    def test_translate_day_name(self):
        """Тест перевода названия дня недели"""
        self.assertEqual(translate_day_name("Monday"), "Понедельник")
        self.assertEqual(translate_day_name("Sunday"), "Воскресенье")
        self.assertEqual(translate_day_name("Unknown"), "Unknown")

    def test_translate_meal_type(self):
        """Тест перевода типа приема пищи"""
        self.assertEqual(translate_meal_type("breakfast"), "Завтрак")
        self.assertEqual(translate_meal_type("Lunch"), "Обед")
        self.assertEqual(translate_meal_type("Unknown"), "Unknown")


class TestDietService(unittest.IsolatedAsyncioTestCase):
    """Тесты для сервиса работы с диетами"""

    def setUp(self):
        """Настройка тестового окружения"""
        self.diet_service = DietService()

        # Создаем тестовый план диеты
        self.test_diet_plan = {
            "id": "test-plan-id",
            "user_id": "test-user-id",
            "start_date": "2024-01-01",
            "end_date": "2024-01-07",
            "personalized_note": "Привет, Тест! Этот план создан специально для тебя.",
            "caloric_deficit": "500 ккал в день",
            "general_recommendations": "Пейте больше воды и соблюдайте режим питания.",
            "estimated_weekly_price": 350,
            "daily_plans": {
                "2024-01-01": {
                    "date": "2024-01-01",
                    "meals": [
                        {
                            "type": "breakfast",
                            "title": "Овсянка с фруктами",
                            "description": "Питательный завтрак",
                            "why_recommended": "Богата клетчаткой и надолго дает чувство сытости",
                            "relevance_score": 9,
                            "products": [
                                {"name": "Овсянка", "quantity": 50, "unit": "г"},
                                {"name": "Банан", "quantity": 1, "unit": "шт"}
                            ],
                            "calories": 350,
                            "proteins": 10,
                            "fats": 5,
                            "carbs": 60,
                            "fiber": 8,
                            "estimated_price": 15
                        },
                        {
                            "type": "lunch",
                            "title": "Куриная грудка с овощами",
                            "description": "Белковый обед",
                            "why_recommended": "Высокое содержание белка для сохранения мышечной массы",
                            "relevance_score": 10,
                            "products": [
                                {"name": "Куриная грудка", "quantity": 150, "unit": "г"},
                                {"name": "Овощи", "quantity": 200, "unit": "г"}
                            ],
                            "calories": 400,
                            "proteins": 40,
                            "fats": 10,
                            "carbs": 15,
                            "fiber": 5,
                            "estimated_price": 35
                        }
                    ],
                    "total_calories": 750,
                    "total_proteins": 50,
                    "total_fats": 15,
                    "total_carbs": 75,
                    "macros_ratio": "Б:Ж:У = 27%:18%:55%",
                    "estimated_total_price": 50,
                    "tips": "Не забудьте выпить стакан воды перед едой."
                }
            }
        }

    @patch('app.services.diet_service.diet_service._post_process_diet_plan')
    @patch('app.db.firebase.firebase_client.add_document')
    @patch('app.services.llm.llm_service.generate_diet_plan')
    @patch('app.db.firebase.firebase_client.get_document')
    @patch('app.db.firebase.firebase_client.get_all_documents')
    async def test_generate_diet_plan(self, mock_get_all_docs, mock_get_doc, mock_generate, mock_add,
                                      mock_post_process):
        """Тест генерации плана диеты"""
        # Настройка моков
        mock_get_doc.return_value = {"name": "Test User", "id": "test-user-id"}
        mock_get_all_docs.return_value = [{"name": "Овсянка", "is_local": True}]
        mock_generate.return_value = self.test_diet_plan
        mock_add.return_value = "test-plan-id"

        # Вызываем тестируемый метод
        result = await self.diet_service.generate_diet_plan("test-user-id", 7)

        # Проверяем результат
        self.assertEqual(result["id"], "test-plan-id")
        self.assertEqual(result["user_id"], "test-user-id")

        # Проверяем, что методы были вызваны
        mock_get_doc.assert_called_once_with("users", "test-user-id")
        mock_get_all_docs.assert_called_once_with("products")
        mock_generate.assert_called_once()
        mock_add.assert_called_once()
        mock_post_process.assert_called_once()

    @patch('app.db.firebase.firebase_client.query_documents')
    async def test_get_current_diet(self, mock_query):
        """Тест получения текущего плана диеты"""
        # Настройка мока
        today = datetime.now(pytz.UTC).date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        mock_query.return_value = [
            {
                "start_date": yesterday.isoformat(),
                "end_date": tomorrow.isoformat(),
                "id": "current-plan"
            },
            {
                "start_date": "2023-01-01",
                "end_date": "2023-01-07",
                "id": "old-plan"
            }
        ]

        # Вызываем тестируемый метод
        result = await self.diet_service.get_current_diet("test-user-id")

        # Проверяем результат
        self.assertEqual(result["id"], "current-plan")

        # Проверяем, что методы были вызваны
        mock_query.assert_called_once_with("diet_plans", "user_id", "==", "test-user-id")

    def test_get_diet_summary(self):
        """Тест создания сводки плана диеты"""
        # Вызываем тестируемый метод
        summary = self.diet_service.get_diet_summary(self.test_diet_plan)

        # Проверяем результат
        self.assertIn("ПЕРСОНАЛЬНЫЙ ПЛАН ПИТАНИЯ", summary)
        self.assertIn("Привет, Тест!", summary)
        self.assertIn("500 ккал", summary)
        self.assertIn("350 кетцалей", summary)
        self.assertIn("Овсянка с фруктами", summary)
        self.assertIn("Куриная грудка с овощами", summary)

    def test_get_full_diet_plan(self):
        """Тест создания полного плана диеты"""
        # Вызываем тестируемый метод
        messages = self.diet_service.get_full_diet_plan(self.test_diet_plan)

        # Проверяем результат
        self.assertTrue(len(messages) > 0)
        self.assertIn("ПОЛНЫЙ ПЛАН ПИТАНИЯ НА НЕДЕЛЮ", messages[0])

        # В других сообщениях должны быть дни
        day_found = False
        for msg in messages[1:]:
            if "2024-01-01" in msg:
                day_found = True
                self.assertIn("Овсянка с фруктами", msg)
                self.assertIn("Куриная грудка с овощами", msg)
        self.assertTrue(day_found)

    def test_get_day_diet_plan(self):
        """Тест создания плана на день"""
        # Вызываем тестируемый метод
        day_plan = self.diet_service.get_day_diet_plan(
            self.test_diet_plan,
            datetime.strptime("2024-01-01", "%Y-%m-%d").date()
        )

        # Проверяем результат
        self.assertIn("ПЛАН ПИТАНИЯ НА", day_plan)
        self.assertIn("Овсянка с фруктами", day_plan)
        self.assertIn("Куриная грудка с овощами", day_plan)
        self.assertIn("750 ккал", day_plan)
        self.assertIn("40 г", day_plan)  # Белки

    def test_format_shopping_list(self):
        """Тест форматирования списка покупок"""
        # Создаем тестовый список покупок
        shopping_list = {
            "user_id": "test-user-id",
            "diet_plan_id": "test-plan-id",
            "items": [
                {
                    "name": "Овсянка",
                    "quantity": 350,
                    "unit": "г",
                    "estimated_price": 40
                },
                {
                    "name": "Куриная грудка",
                    "quantity": 1050,
                    "unit": "г",
                    "estimated_price": 180
                },
                {
                    "name": "Банан",
                    "quantity": 7,
                    "unit": "шт",
                    "estimated_price": 35
                },
                {
                    "name": "Овощи",
                    "quantity": 1400,
                    "unit": "г",
                    "estimated_price": 100
                }
            ],
            "total_estimated_price": 355
        }

        # Вызываем тестируемый метод
        formatted_list = self.diet_service.format_shopping_list(shopping_list)

        # Проверяем результат
        self.assertIn("СПИСОК ПОКУПОК", formatted_list)
        self.assertIn("Овсянка", formatted_list)
        self.assertIn("Куриная грудка", formatted_list)
        self.assertIn("Банан", formatted_list)
        self.assertIn("355 кетцалей", formatted_list)


class TestTrackingService(unittest.IsolatedAsyncioTestCase):
    """Тесты для сервиса трекинга"""

    def setUp(self):
        """Настройка тестового окружения"""
        self.tracking_service = TrackingService()

    @patch('app.db.firebase.firebase_client.add_document')
    @patch('app.db.firebase.firebase_client.update_document')
    @patch('app.db.firebase.firebase_client.get_document')
    async def test_record_meal_compliance(self, mock_get_doc, mock_update, mock_add):
        """Тест записи соблюдения режима питания"""
        # Настройка моков
        mock_get_doc.return_value = {"name": "Test User", "id": "test-user-id"}
        mock_add.return_value = "test-compliance-id"
        mock_update.return_value = True

        # Параметры
        user_id = "test-user-id"
        date_val = datetime.now(pytz.UTC).date()
        meal_type = "breakfast"
        status = MealComplianceStatus.FOLLOWED
        notes = "Съел все по плану"

        # Добавляем мок для _update_daily_compliance
        with patch.object(self.tracking_service, '_update_daily_compliance',
                          new_callable=AsyncMock) as mock_update_daily:
            mock_update_daily.return_value = None

            # Вызываем тестируемый метод
            result = await self.tracking_service.record_meal_compliance(
                user_id, date_val, meal_type, status, notes
            )

            # Проверяем результат
            self.assertTrue(result)

            # Проверяем, что методы были вызваны
            mock_get_doc.assert_called_once_with("users", user_id)
            mock_add.assert_called_once()
            mock_update_daily.assert_called_once()

    @patch('app.db.firebase.firebase_client.query_documents')
    async def test_get_diet_compliance(self, mock_query):
        """Тест получения статистики соблюдения плана питания"""
        # Настройка мока
        today = datetime.now(pytz.UTC).date().isoformat()
        compliance_data = {
            "user_id": "test-user-id",
            "date": today,
            "meals": {
                "breakfast": MealComplianceStatus.FOLLOWED,
                "lunch": MealComplianceStatus.PARTIALLY,
                "dinner": MealComplianceStatus.SKIPPED
            },
            "overall_score": 50.0,
            "id": "test-compliance-id"
        }
        mock_query.return_value = [compliance_data]

        # Вызываем тестируемый метод
        result = await self.tracking_service.get_diet_compliance("test-user-id")

        # Проверяем результат
        self.assertEqual(result["id"], "test-compliance-id")
        self.assertEqual(result["overall_score"], 50.0)
        self.assertEqual(len(result["meals"]), 3)

        # Проверяем, что методы были вызваны
        mock_query.assert_called_once()

    @patch('app.db.firebase.firebase_client.update_document')
    @patch('app.db.firebase.firebase_client.add_document')
    @patch('app.db.firebase.firebase_client.query_documents')
    async def test_update_daily_compliance(self, mock_query, mock_add, mock_update):
        """Тест обновления общей статистики соблюдения за день"""
        # Настройка моков
        today = "2024-01-15"
        compliances = [
            {
                "user_id": "test-user-id",
                "date": today,
                "meal_type": "breakfast",
                "status": MealComplianceStatus.FOLLOWED
            },
            {
                "user_id": "test-user-id",
                "date": today,
                "meal_type": "lunch",
                "status": MealComplianceStatus.PARTIALLY
            },
            {
                "user_id": "test-user-id",
                "date": today,
                "meal_type": "dinner",
                "status": MealComplianceStatus.SKIPPED
            }
        ]
        mock_query.return_value = compliances

        # Первый вызов - нет существующей записи
        mock_query.side_effect = [compliances, []]
        mock_add.return_value = "test-daily-compliance-id"

        # Вызываем тестируемый метод
        await self.tracking_service._update_daily_compliance("test-user-id", today)

        # Проверяем, что методы были вызваны
        mock_query.assert_called()
        mock_add.assert_called_once()

        # Второй вызов - есть существующая запись
        existing_daily = [{"id": "existing-id", "date": today}]
        mock_query.side_effect = [compliances, existing_daily]
        mock_update.return_value = True

        # Сбрасываем счетчики вызовов
        mock_query.reset_mock()
        mock_add.reset_mock()

        # Вызываем тестируемый метод еще раз
        await self.tracking_service._update_daily_compliance("test-user-id", today)

        # Проверяем, что методы были вызваны
        mock_query.assert_called()
        mock_add.assert_not_called()
        mock_update.assert_called_once()


if __name__ == '__main__':
    unittest.main()