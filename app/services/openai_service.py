import openai
import logging
from typing import Dict, Any, List, Optional
import json

from config import settings

logger = logging.getLogger(__name__)

# Настройка OpenAI API
openai.api_key = settings.OPENAI_API_KEY

class OpenAIService:
    """Сервис для работы с OpenAI API"""
    
    def __init__(self):
        self.model = settings.OPENAI_MODEL
    
    async def generate_diet_plan(
        self,
        user_data: Dict[str, Any],
        days: int = 7,
        product_list: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Генерирует план диеты на основе данных пользователя
        
        Args:
            user_data: Данные пользователя (пол, возраст, вес, цели и т.д.)
            days: Количество дней для плана (по умолчанию 7)
            product_list: Список доступных продуктов с ценами
        
        Returns:
            Dict[str, Any]: План диеты
        """
        try:
            # Формируем промпт для GPT
            system_prompt = self._create_diet_system_prompt(product_list)
            user_prompt = self._create_diet_user_prompt(user_data, days)
            
            # Вызываем OpenAI API
            response = await self._call_openai(system_prompt, user_prompt)
            
            # Обрабатываем и валидируем результат
            diet_plan = self._parse_diet_response(response)
            return diet_plan
            
        except Exception as e:
            logger.error(f"Ошибка при генерации плана диеты: {str(e)}")
            return {"error": str(e)}
    
    async def answer_nutrition_question(self, user_id: str, question: str) -> str:
        """
        Отвечает на вопрос пользователя о питании
        
        Args:
            user_id: ID пользователя
            question: Вопрос о питании
        
        Returns:
            str: Ответ на вопрос
        """
        try:
            # Формируем промпт
            system_prompt = """Ты помощник по питанию и здоровому образу жизни для пользователей из Гватемалы. 
            Отвечай на вопросы кратко, научно обоснованно, но понятным языком. 
            Используй информацию о местных продуктах Гватемалы, где это уместно.
            Если не знаешь ответа, честно признайся в этом."""
            
            # Вызываем OpenAI API
            response = await self._call_openai(system_prompt, question)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Ошибка при ответе на вопрос: {str(e)}")
            return f"Извините, произошла ошибка при обработке вашего вопроса. Пожалуйста, попробуйте еще раз позже."
    
    async def create_shopping_list(self, diet_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Создает список покупок на основе плана диеты
        
        Args:
            diet_plan: План диеты
        
        Returns:
            List[Dict[str, Any]]: Список покупок
        """
        try:
            # Формируем промпты
            system_prompt = """Ты помощник, который создает оптимизированные списки покупок на основе планов питания.
            Твоя задача - объединить все продукты из плана в единый список, 
            суммируя необходимые количества для каждого продукта.
            Возвращай данные в формате JSON."""
            
            user_prompt = f"""Создай список покупок на основе следующего плана диеты:
            {json.dumps(diet_plan, ensure_ascii=False)}
            
            Объедини одинаковые продукты и суммируй их количество.
            Учитывай единицы измерения (граммы, штуки и т.д.).
            Верни результат в формате JSON-списка:
            [
                {{
                    "name": "название продукта",
                    "quantity": числовое_значение,
                    "unit": "единица_измерения",
                    "estimated_price": примерная_цена_если_известна,
                    "store_suggestions": ["магазин1", "магазин2"]
                }},
                ...
            ]
            """
            
            # Вызываем OpenAI API
            response = await self._call_openai(system_prompt, user_prompt)
            
            # Парсим JSON-ответ
            try:
                shopping_list = json.loads(response)
                return shopping_list
            except json.JSONDecodeError:
                logger.error(f"Не удалось распарсить JSON ответ: {response}")
                return []
            
        except Exception as e:
            logger.error(f"Ошибка при создании списка покупок: {str(e)}")
            return []
    
    async def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Вызывает OpenAI API с указанными промптами"""
        try:
            logger.info(f"Вызов OpenAI API с моделью {self.model}")
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            
            # Извлекаем содержимое ответа
            content = response.choices[0].message.content
            return content
            
        except Exception as e:
            logger.error(f"Ошибка при вызове OpenAI API: {str(e)}")
            raise e
    
    def _create_diet_system_prompt(self, product_list: Optional[List[Dict[str, Any]]] = None) -> str:
        """Создает системный промпт для генерации диеты"""
        system_prompt = """Ты диетолог-эксперт, специализирующийся на создании персонализированных планов питания.
        Твоя задача - создать детальный план питания, основанный на данных пользователя и доступных продуктах в Гватемале.
        
        Важные принципы:
        1. Учитывай местные продукты Гватемалы и их сезонность
        2. Рассчитывай калории и макронутриенты в соответствии с целями пользователя
        3. Учитывай бюджетные ограничения пользователя
        4. Включай разнообразные блюда, подходящие для местной кухни
        5. Соблюдай пищевые предпочтения и ограничения пользователя
        
        Ответ должен быть в формате JSON с детализацией по дням и приемам пищи."""
        
        # Если есть список продуктов, добавляем его к промпту
        if product_list and len(product_list) > 0:
            product_info = "\n\nДоступные местные продукты:\n"
            for product in product_list[:30]:  # Ограничиваем количество продуктов в промпте
                price_info = ""
                if "store_prices" in product and product["store_prices"]:
                    stores = list(product["store_prices"].values())
                    if stores:
                        price_info = f" (цена: ~{stores[0].get('price', 'N/A')} {stores[0].get('unit', '')})"
                
                product_info += f"- {product['name']}{' (местный)' if product.get('is_local') else ''}{price_info}\n"
            
            system_prompt += product_info
        
        return system_prompt
    
    def _create_diet_user_prompt(self, user_data: Dict[str, Any], days: int) -> str:
        """Создает пользовательский промпт для генерации диеты"""
        
        # Преобразуем данные пользователя в текстовый промпт
        gender = user_data.get("gender", "не указан")
        age = user_data.get("age", "не указан")
        height = user_data.get("height", "не указан")
        current_weight = user_data.get("current_weight", "не указан")
        target_weight = user_data.get("target_weight", "не указан")
        activity_level = user_data.get("activity_level", "не указан")
        weight_goal = user_data.get("weight_goal", "не указан")
        diet_preference = user_data.get("diet_preference", "regular")
        budget_limit = user_data.get("budget_limit", "не указан")
        allergies = user_data.get("allergies", [])
        disliked_products = user_data.get("disliked_products", [])
        
        user_prompt = f"""Создай план питания на {days} дней для пользователя со следующими параметрами:
        
        - Пол: {gender}
        - Возраст: {age}
        - Рост: {height} см
        - Текущий вес: {current_weight} кг
        - Целевой вес: {target_weight} кг
        - Уровень активности: {activity_level}
        - Цель по весу: {weight_goal}
        - Пищевые предпочтения: {diet_preference}
        - Бюджет на продукты: {budget_limit} кетцалей в неделю
        - Аллергии: {', '.join(allergies) if allergies else 'нет'}
        - Нелюбимые продукты: {', '.join(disliked_products) if disliked_products else 'нет'}
        
        Формат ответа должен быть в виде JSON-объекта со следующей структурой:
        {{
            "user_id": "идентификатор пользователя",
            "start_date": "дата начала плана",
            "end_date": "дата окончания плана",
            "daily_plans": {{
                "YYYY-MM-DD": {{
                    "date": "YYYY-MM-DD",
                    "meals": [
                        {{
                            "type": "breakfast/lunch/dinner/snack",
                            "title": "название блюда",
                            "description": "краткое описание",
                            "products": [
                                {{
                                    "name": "название продукта",
                                    "quantity": числовое_количество,
                                    "unit": "единица измерения"
                                }}
                            ],
                            "preparation": "инструкция по приготовлению",
                            "calories": примерное_количество_калорий,
                            "proteins": граммы_белков,
                            "fats": граммы_жиров,
                            "carbs": граммы_углеводов,
                            "estimated_price": примерная_стоимость_в_кетцалях
                        }}
                    ],
                    "total_calories": общее_количество_калорий_за_день,
                    "total_proteins": общее_количество_белков_за_день,
                    "total_fats": общее_количество_жиров_за_день,
                    "total_carbs": общее_количество_углеводов_за_день,
                    "estimated_total_price": примерная_стоимость_за_день,
                    "tips": "советы на день"
                }}
            }},
            "general_recommendations": "общие рекомендации",
            "estimated_weekly_price": примерная_стоимость_за_неделю
        }}
        
        Используй местные продукты Гватемалы, соблюдай калорийность, учитывай бюджетные ограничения.
        """
        
        return user_prompt
    
    def _parse_diet_response(self, response: str) -> Dict[str, Any]:
        """Парсит и валидирует ответ с планом диеты"""
        try:
            # Пытаемся распарсить JSON
            diet_plan = json.loads(response)
            
            # Здесь можно добавить дополнительную валидацию структуры плана питания
            
            return diet_plan
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON ответа: {str(e)}")
            return {"error": "Не удалось распарсить ответ с планом диеты"}
        except Exception as e:
            logger.error(f"Ошибка обработки ответа: {str(e)}")
            return {"error": str(e)}

# Создаем экземпляр сервиса OpenAI
openai_service = OpenAIService()
