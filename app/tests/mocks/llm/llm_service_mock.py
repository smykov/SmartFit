# tests/mocks/llm/llm_service_mock.py
from typing import Dict, Any, List, Optional
import json
import re


class LLMServiceMock:
    """Мок для LLM-сервиса с предопределенными ответами."""

    def __init__(self):
        """Инициализация мока с предопределенными ответами."""
        self.predefined_responses = self._initialize_predefined_responses()

    def _initialize_predefined_responses(self) -> Dict[str, str]:
        """Инициализирует словарь предопределенных ответов для разных запросов."""
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

    async def generate_completion(self, system_prompt: str, user_prompt: str, temperature: float = 0.7,
                                  max_tokens: int = 2000) -> str:
        """Имитирует вызов LLM API на основе входных промптов."""

        # Определяем тип запроса на основе ключевых слов в промптах
        request_type = self._determine_request_type(system_prompt, user_prompt)

        # Возвращаем предопределенный ответ на основе типа запроса
        if request_type in self.predefined_responses:
            return self.predefined_responses[request_type]

        # Если не нашли предопределенный ответ, возвращаем заглушку
        return json.dumps({"error": "No predefined response for this prompt"})

    def _determine_request_type(self, system_prompt: str, user_prompt: str) -> str:
        """Определяет тип запроса на основе текста промптов."""

        # Запрос на генерацию краткой версии плана питания
        if "diet plan" in system_prompt.lower() and "short" in system_prompt.lower():
            return "generate_short_diet"

        # Запрос на обновление плана питания
        if "update" in system_prompt.lower() or "modify" in system_prompt.lower():
            if "breakfast" in user_prompt.lower() and "monday" in user_prompt.lower():
                return "update_monday_breakfast"

        # Запрос на создание списка покупок
        if "shopping list" in system_prompt.lower():
            return "generate_shopping_list"

        # Вопросы о питании
        if "nutrition" in system_prompt.lower() or "food" in system_prompt.lower():
            if "avocado" in user_prompt.lower() or "авокадо" in user_prompt.lower():
                return "nutrition_question"

        # Дефолтный ответ
        return "default"

    async def generate_diet_plan(self, user_data: Dict[str, Any], days: int = 7,
                                 product_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Имитирует генерацию плана диеты."""
        return json.loads(self.predefined_responses["generate_short_diet"])

    async def update_diet_plan(self, diet_plan: Dict[str, Any], update_request: str) -> Dict[str, Any]:
        """Имитирует обновление плана диеты."""
        # Определяем, какой день и прием пищи нужно обновить
        if "monday" in update_request.lower() and "breakfast" in update_request.lower():
            return json.loads(self.predefined_responses["update_monday_breakfast"])

        # Дефолтный ответ
        return {"success": False, "error": "Unable to process update request"}

    async def create_shopping_list(self, diet_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Имитирует создание списка покупок."""
        return json.loads(self.predefined_responses["generate_shopping_list"])

    async def answer_nutrition_question(self, user_id: str, question: str) -> str:
        """Имитирует ответ на вопрос о питании."""
        if "авокадо" in question.lower() or "avocado" in question.lower():
            return self.predefined_responses["nutrition_question"]

        return "Извините, у меня нет информации по этому вопросу."