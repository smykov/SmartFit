import pytest
from unittest.mock import AsyncMock, MagicMock
import json
from typing import Dict, Any, List, Optional

from app.services.llm.base_llm_service import BaseLLMService


@pytest.fixture
def llm_predefined_responses():
    """Возвращает предопределенные ответы для LLM-сервиса."""
    return {
        # Ответы для генерации плана питания
        "generate_short_diet": json.dumps({
            "daily_plans": {
                "monday": {
                    "meals": [
                        {
                            "type": "breakfast",
                            "title": "Овсянка с фруктами и орехами",
                            "calories": 350
                        },
                        {
                            "type": "lunch",
                            "title": "Куриный салат с авокадо",
                            "calories": 450
                        },
                        {
                            "type": "dinner",
                            "title": "Запеченная рыба с овощами",
                            "calories": 400
                        }
                    ],
                    "total_calories": 1200
                },
                "tuesday": {
                    "meals": [
                        {
                            "type": "breakfast",
                            "title": "Омлет с овощами",
                            "calories": 300
                        },
                        {
                            "type": "lunch",
                            "title": "Суп из чечевицы",
                            "calories": 350
                        },
                        {
                            "type": "dinner",
                            "title": "Индейка с зеленью и киноа",
                            "calories": 450
                        }
                    ],
                    "total_calories": 1100
                }
            }
        }),

        # Ответы для обновления понедельника
        "update_monday_breakfast": json.dumps({
            "updated_days": {
                "monday": {
                    "meals": [
                        {
                            "type": "breakfast",
                            "title": "Омлет с овощами",
                            "calories": 300
                        },
                        {
                            "type": "lunch",
                            "title": "Куриный салат с авокадо",
                            "calories": 450
                        },
                        {
                            "type": "dinner",
                            "title": "Запеченная рыба с овощами",
                            "calories": 400
                        }
                    ],
                    "total_calories": 1150
                }
            },
            "comment": "Заменил овсянку на омлет с овощами согласно вашему запросу"
        }),

        # Ответы для генерации списка покупок
        "generate_shopping_list": json.dumps([
            {"name": "Овсянка", "quantity": 100, "unit": "г", "category": "bread_cereals"},
            {"name": "Яйца", "quantity": 10, "unit": "шт.", "category": "dairy"},
            {"name": "Куриная грудка", "quantity": 500, "unit": "г", "category": "meat_fish"},
            {"name": "Авокадо", "quantity": 2, "unit": "шт.", "category": "fruits_vegetables"},
            {"name": "Помидоры", "quantity": 4, "unit": "шт.", "category": "fruits_vegetables"},
            {"name": "Рыба (тилапия)", "quantity": 400, "unit": "г", "category": "meat_fish"}
        ]),

        # Ответы для вопросов о питании
        "nutrition_question": "Авокадо богат полезными жирами и является отличным источником витамина Е. Его можно добавлять в салаты, намазывать на тосты или использовать для приготовления гуакамоле."
    }


@pytest.fixture
def llm_service_mock(llm_predefined_responses):
    """Возвращает мок для LLM-сервиса с предопределенными ответами."""
    mock = AsyncMock(spec=BaseLLMService)
    responses = llm_predefined_responses

    # Метод для определения типа запроса
    def determine_request_type(system_prompt, user_prompt):
        # Ищем ключевые слова в промптах
        if "diet plan" in system_prompt.lower() and "short" in system_prompt.lower():
            return "generate_short_diet"

        if "update" in system_prompt.lower() or "modify" in system_prompt.lower():
            if "breakfast" in user_prompt.lower() and "monday" in user_prompt.lower():
                return "update_monday_breakfast"

        if "shopping list" in system_prompt.lower():
            return "generate_shopping_list"

        if "nutrition" in system_prompt.lower() or "food" in system_prompt.lower():
            if "avocado" in user_prompt.lower() or "авокадо" in user_prompt.lower():
                return "nutrition_question"

        return "default"

    # Метод для генерации ответа
    async def generate_completion(system_prompt, user_prompt, temperature=0.7, max_tokens=2000):
        request_type = determine_request_type(system_prompt, user_prompt)

        if request_type in responses:
            return responses[request_type]

        return json.dumps({"error": "No predefined response found for this prompt"})

    # Методы для работы с планами диет
    async def generate_diet_plan(user_data, days=7, product_list=None):
        return json.loads(responses["generate_short_diet"])

    async def update_diet_plan(diet_plan, update_request):
        if "monday" in update_request.lower() and "breakfast" in update_request.lower():
            result = json.loads(responses["update_monday_breakfast"])
            return {"success": True, **result}
        return {"success": False, "error": "Unable to process update request"}

    async def update_short_diet_plan(diet_plan_id, update_request):
        if "monday" in update_request.lower() and "breakfast" in update_request.lower():
            result = json.loads(responses["update_monday_breakfast"])
            return {"success": True, **result}
        return {"success": False, "error": "Unable to process update request"}

    # Методы для работы со списками покупок
    async def create_shopping_list(diet_plan):
        return json.loads(responses["generate_shopping_list"])

    # Методы для ответов на вопросы о питании
    async def answer_nutrition_question(user_id, question):
        if "авокадо" in question.lower() or "avocado" in question.lower():
            return responses["nutrition_question"]
        return "Извините, у меня нет информации по этому вопросу."

    # Привязываем методы к моку
    mock.generate_completion = AsyncMock(side_effect=generate_completion)
    mock.generate_diet_plan = AsyncMock(side_effect=generate_diet_plan)
    mock.update_diet_plan = AsyncMock(side_effect=update_diet_plan)
    mock.update_short_diet_plan = AsyncMock(side_effect=update_short_diet_plan)
    mock.create_shopping_list = AsyncMock(side_effect=create_shopping_list)
    mock.answer_nutrition_question = AsyncMock(side_effect=answer_nutrition_question)

    return mock


@pytest.fixture
def llm_factory_mock(llm_service_mock):
    """Возвращает мок для LLMFactory."""
    from app.services.llm.llm_factory import LLMFactory

    # Перегружаем статический метод
    LLMFactory.create_llm_service = MagicMock(return_value=llm_service_mock)
    LLMFactory.get_default_llm_service = MagicMock(return_value=llm_service_mock)

    return LLMFactory