"""
Шаблоны промптов для генерации диет
"""

def create_diet_system_prompt(product_list=None):
    """
    Создает системный промпт для генерации диет
    
    Args:
        product_list: Список доступных продуктов с ценами и информацией
        
    Returns:
        str: Системный промпт
    """
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

def create_diet_user_prompt(user_data, days=7):
    """
    Создает пользовательский промпт для генерации диет
    
    Args:
        user_data: Данные пользователя
        days: Количество дней для плана
        
    Returns:
        str: Пользовательский промпт
    """
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

def create_shopping_list_prompt(diet_plan):
    """
    Создает промпт для генерации списка покупок
    
    Args:
        diet_plan: План диеты
        
    Returns:
        str: Промпт для списка покупок
    """
    system_prompt = """Ты помощник, который создает оптимизированные списки покупок на основе планов питания.
    Твоя задача - объединить все продукты из плана в единый список, 
    суммируя необходимые количества для каждого продукта.
    Возвращай данные в формате JSON."""
    
    user_prompt = f"""Создай список покупок на основе следующего плана диеты:
    {diet_plan}
    
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
    
    return system_prompt, user_prompt

def create_nutrition_question_prompt():
    """
    Создает промпт для ответов на вопросы о питании
    
    Returns:
        str: Системный промпт
    """
    return """Ты помощник по питанию и здоровому образу жизни для пользователей из Гватемалы. 
    Отвечай на вопросы кратко, научно обоснованно, но понятным языком. 
    Используй информацию о местных продуктах Гватемалы, где это уместно.
    Ориентируйся на типичные продукты гватемальской кухни: черная фасоль, кукуруза, тортильи, 
    авокадо, плантаны, манго, папайя, перец чили, томаты, лук.
    Если не знаешь ответа, честно признайся в этом."""
