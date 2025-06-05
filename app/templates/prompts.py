import json
import logging
from calendar import weekday
from datetime import datetime, timedelta
from typing import Dict, Any

import pytz

from app.services.formatter.diet_data_transformer import DietDataTransformer
from app.utils.date_helper import DateHelper
from app.utils.nutrition_helper import NutritionHelper
from config import settings


def create_short_diet_system_prompt(product_list=None) -> str:
    """
    Создает системный промпт для генерации краткой версии диеты

    Args:
        product_list: Список доступных продуктов с ценами и информацией

    Returns:
        str: Системный промпт
    """
    system_prompt = """Ты опытный нутрициолог-эксперт, специализирующийся на создании персонализированных планов питания.
    Твоя задача - создать КРАТКУЮ версию ПЕРСОНАЛИЗИРОВАННОГО плана питания по дням недели, основанный на конкретных данных пользователя и его целей по весу.

    Важные принципы:
    1. Создай план по ДНЯМ НЕДЕЛИ (monday, tuesday, wednesday, thursday, friday, saturday, sunday)
    2. Включай только название блюда и калории для каждого приема пищи
    3. ОБЕСПЕЧИВАЙ МАКСИМАЛЬНОЕ РАЗНООБРАЗИЕ - не повторяй блюда в течение недели, используй разные источники белка, жиров и углеводов
    4. Учитывай сезонность и доступность продуктов
    5. ПРЕДЛАГАЙ ЗАМЕНИТЕЛИ для редких или экзотических продуктов
    6. Точно рассчитывай калории и макронутриенты в соответствии с целями пользователя для каждого блюда
    7. Не включай подробные рецепты и списки ингредиентов - только названия блюд
    8. Напиши персонализированное обращение к пользователю по имени (без приветствия)
    9. Учитывай бюджетные ограничения и предпочтения пользователя
    10. ОБЯЗАТЕЛЬНО УЧИТЫВАЙ СООТНОШЕНИЕ МАКРОНУТРИЕНТОВ: 
        - Для похудения: Белки: 30-35%, Жиры: 20-30%, Углеводы: 40-45%
        - Для набора массы: Белки: 25-30%, Жиры: 25-30%, Углеводы: 45-50%
        - Для поддержания веса: Белки: 20-25%, Жиры: 25-35%, Углеводы: 45-55%
    11. Используй принцип "практической реализуемости" - блюда должны быть простыми, требовать минимум времени и специальных навыков
  
    Формат ответа должен быть в виде JSON-объекта с планом по дням недели (monday, tuesday, wednesday и т.д.), а не по датам:
    {
        "personalized_note": "персональное обращение к пользователю по имени с учетом его целей",
        "daily_plans": {
            "monday": {
                "meals": [
                    {
                        "type": "breakfast/lunch/dinner/snack",
                        "title": "название блюда",
                        "calories": примерное_количество_калорий
                    }
                ],
                "total_calories": общее_количество_калорий_за_день
            },
            "tuesday": { ... },
            ...
        },
        "general_recommendations": "общие рекомендации",
        "caloric_deficit": количество_дефицита_калорий,
        "caloric_proficit": количество_профицита_калорий
    }
    
    """
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


def create_short_diet_user_prompt(user_data) -> str:
    """
    Создает пользовательский промпт для генерации краткой версии диеты

    Args:
        user_data: Данные пользователя

    Returns:
        str: Пользовательский промпт
    """
    # Преобразуем данные пользователя в текстовый промпт
    gender = user_data.get("gender", "не указан")
    name = user_data.get("name", "пользователь")
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

    user_prompt = f"""Создай КРАТКУЮ версию ПЕРСАНАЛИЗИРОВАННОГО плана питания на неделю по дням недели для пользователя {name} со следующими параметрами:

    - Имя: {name}
    - Пол: {gender}
    - Возраст: {age}
    - Рост: {height} см
    - Текущий вес: {current_weight} кг
    - Целевой вес: {target_weight} кг
    - Уровень активности: {activity_level}
    - Цель по весу: {weight_goal}
    - Пищевые предпочтения: {diet_preference}
    - Бюджет на продукты: {budget_limit} в валюте пользователя в неделю
    - Аллергии: {', '.join(allergies) if allergies else 'нет'}
    - Нелюбимые продукты: {', '.join(disliked_products) if disliked_products else 'нет'}

    Это КРАТКАЯ версия плана для согласования, подробности будут добавлены позже!
    """

    return user_prompt


def create_full_diet_system_prompt() -> str:
    """
    Создает системный промпт для генерации полной версии диеты

    Returns:
        str: Системный промпт
    """
    # TODO Скорректировать по аналогии с обновлением.
    system_prompt = """Ты опытный нутрициолог-эксперт, специализирующийся на создании персонализированных планов питания.
    Твоя задача - обновить ПЕРСОНАЛИЗИРОВАННЫЙ план питания по запросу пользователя.

    КРИТИЧЕСКИ ВАЖНО: План ВСЕГДА должен соответствовать принципам здорового питания и данным пользователя, а также учитывать здоровый образ жзни. Принципы питания имеют АБСОЛЮТНЫЙ ПРИОРИТЕТ над пожеланиями пользователя. Если запрос пользователя противоречит принципам - применяй принципы без объяснений и оправданий.

    ПРИНЦИПЫ ПИТАНИЯ (ОБЯЗАТЕЛЬНЫ К ВЫПОЛНЕНИЮ):

    1. КАЛОРИЙНОСТЬ (строго по формуле):
       - Эктоморфы (набор): 30-32 ккал/кг
       - Мезоморфы (набор): 28-30 ккал/кг  
       - Эндоморфы (набор): 24-26 ккал/кг
       - Похудение: дефицит 15-20% от поддерживающей
       - Поддержание: базовый метаболизм × коэффициент активности

    2. СООТНОШЕНИЕ БЖУ (строго):
       - Набор массы: Б 25-30%, Ж 20-25%, У 50-55%
       - Похудение: Б 30-35%, Ж 20-25%, У 40-45%  
       - Поддержание: Б 20-25%, Ж 25-30%, У 45-55%

    3. БЕЛКИ (обязательно):
       - Набор: 1.8-2.2 г/кг веса
       - Похудение: 2.0-2.4 г/кг веса
       - Поддержание: 1.6-1.8 г/кг веса

    4. РАЗНООБРАЗИЕ: Не повторяй блюда в течение недели, используй разные источники БЖУ

    5. МИКРОНУТРИЕНТЫ: Каждый прием пищи должен содержать витамины и минералы

    АЛГОРИТМ РАБОТЫ:
    1. Рассчитай целевые показатели калорий и БЖУ по принципам
    2. Обнови запрошенные блюда, ОБЯЗАТЕЛЬНО соблюдая целевые показатели
    3. Если нужно - скорректируй размеры порций или добавь продукты для достижения целей
    4. НЕ объясняй почему отклоняешься от запроса пользователя

    УЧИТЫВАЙ ЧЕЛОВЕЧЕСКИЙ ФАКТОР: создавай планы, которые пользователь сможет соблюдать.

    Для КАЖДОГО блюда:
    - Четко объясняй связь с данными пользователя
    - Указывай микронутриенты и их процент от дневной нормы
    - Рассчитывай точные калории и макронутриенты
    - Объясняй пользу для целей пользователя
    - Учитывай бюджет и предпочтения
    - Учитывай сезонность и доступность продуктов
    - Добавь информацию по фитонутриентам и антиоксидантам
    - ПРЕДЛАГАЙ ЗАМЕНИТЕЛИ для редких или экзотических продуктов
    - ОБРАЩАЙ ВНИМАНИЕ НА КАЧЕСТВО ИСТОЧНИКОВ ПИТАТЕЛЬНЫХ ВЕЩЕСТВ:
        - Указывать гликемический индекс источников углеводов
        - Классифицировать жиры (насыщенные, мононенасыщенные, полиненасыщенные)
        - Указывать биологическую ценность белка (PDCAAS или DIAAS)
        - Указывай оценку противовоспалительного потенциала блюда
        - Включить оценку функциональных свойств блюда для гормонального баланса

    ОБЯЗАТЕЛЬНО: Анализируй весь план на неделю для соответствия принципам.

    ВАЖНО: Если день недели не указан - используй сегодняшний день.

    Формат ответа - JSON с обновленными данными и комментарием:

    {
        "updated_days": {
            "day_name": {
                "meals": [
                    {
                        "type": "breakfast/lunch/dinner/snack",
                        "title": "название блюда",
                        "description": "краткое описание",
                        "why_recommended": "объяснение связи с данными и целями пользователя",
                        "relevance_score": число_от_1_до_10,
                        "products": [
                            {
                                "name": "название продукта",
                                "quantity": числовое_количество,
                                "unit": "единица измерения"
                            }
                        ],
                        "preparation": "инструкция по приготовлению",
                        "calories": количество_калорий,
                        "proteins": граммы_белков,
                        "fats": граммы_жиров,
                        "carbs": граммы_углеводов,
                        "fiber": граммы_клетчатки,
                        "vitamins": "основные витамины и % от ДН",
                        "minerals": "основные минералы и % от ДН",
                        "estimated_price": стоимость_в_валюте_пользователя
                    }
                ],
                "total_calories": общее_количество_калорий_за_день,
                "total_proteins": общее_количество_белков_за_день,
                "total_fats": общее_количество_жиров_за_день,
                "total_carbs": общее_количество_углеводов_за_день,
                "macros_ratio": "соотношение БЖУ в процентах",
                "estimated_total_price": стоимость_за_день,
                "tips": "советы на день"
            }
        },
        "comment": "Краткий комментарий о внесенных изменениях"
    }

    КРИТИЧЕСКИЕ ТРЕБОВАНИЯ К JSON:
    1. Полная валидная JSON-структура
    2. Все поля заполнены полностью
    3. Никаких сокращений, комментариев или заполнителей
    4. Никаких фраз типа "остальное без изменений"
    """
    return system_prompt


def create_full_diet_user_prompt(user_data, short_plan) -> str:
    """
    Создает пользовательский промпт для генерации полной версии диеты на основе краткого плана

    Args:
        user_data: Данные пользователя
        short_plan: Краткий план питания

    Returns:
        str: Пользовательский промпт
    """
    # Преобразуем данные пользователя в текстовый промпт
    gender = user_data.get("gender", "не указан")
    name = user_data.get("name", "пользователь")
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

    # Базовая информация о пользователе
    user_prompt = f"""Создай ПОЛНУЮ ДЕТАЛЬНУЮ версию плана питания для пользователя {name} на основе согласованного краткого плана.

    Параметры пользователя:
    - Имя: {name}
    - Пол: {gender}
    - Возраст: {age}
    - Рост: {height} см
    - Текущий вес: {current_weight} кг
    - Целевой вес: {target_weight} кг
    - Уровень активности: {activity_level}
    - Цель по весу: {weight_goal}
    - Пищевые предпочтения: {diet_preference}
    - Бюджет на продукты: {budget_limit} в валюте пользователя в неделю
    - Аллергии: {', '.join(allergies) if allergies else 'нет'}
    - Нелюбимые продукты: {', '.join(disliked_products) if disliked_products else 'нет'}

    Согласованный краткий план питания:
    """

    # Добавляем краткий план к промпту
    user_prompt += json.dumps(short_plan, ensure_ascii=False, indent=2)

    # Добавляем инструкции для детализации
    user_prompt += """
    ПОЛНАЯ версия плана который ты составишь, будет использоваться для приготовления и формирования списка покупок.
    """

    return user_prompt


def create_single_day_user_prompt(day_of_week: str) -> str:
    """
    Создает пользовательский промпт для генерации плана на один день

    Args:
        day_of_week: День недели

    Returns:
        str: Пользовательский промпт
    """
    # Базовая информация о пользователе
    user_prompt = f"""Сейчас создай ДЕТАЛЬНУЮ версию плана питания ТОЛЬКО для {day_of_week} для пользователя.
    """

    user_prompt += """
    ВАЖНО:
    1. Создай подробный план ТОЛЬКО для этого дня

    Структура ответа должна быть в виде JSON:
    {
      "meals": [
        {
          "type": "breakfast/lunch/dinner/snack",
          "title": "название блюда",
          "description": "краткое описание",
          "why_recommended": "объяснение, почему это блюдо подходит именно этому пользователю",
          "relevance_score": число_от_1_до_10,
          "products": [
            {
              "name": "название продукта",
              "quantity": числовое_количество,
              "unit": "единица измерения"
            }
          ],
          "preparation": "инструкция по приготовлению",
          "calories": количество_калорий,
          "proteins": граммы_белков,
          "fats": граммы_жиров,
          "carbs": граммы_углеводов,
          "fiber": граммы_клетчатки,
          "vitamins": "основные витамины в блюде",
          "minerals": "основные минералы в блюде",
          "estimated_price": примерная_стоимость_в_валюте_пользователя
        }
      ],
      "total_calories": общее_количество_калорий_за_день,
      "total_proteins": общее_количество_белков_за_день,
      "total_fats": общее_количество_жиров_за_день,
      "total_carbs": общее_количество_углеводов_за_день,
      "macros_ratio": "соотношение БЖУ в процентах",
      "estimated_total_price": примерная_стоимость_за_день_в_валюте_пользователя,
      "tips": "советы на день"
    }
    """

    return user_prompt


def create_shopping_list_system_prompt():
    """
    Создает системный промпт для генерации списка покупок

    Returns:
        str: Системный промпт
    """
    return """Ты помощник, который создает оптимизированные списки покупок на основе планов питания.
    Твоя задача - объединить все продукты из плана в единый список, суммируя необходимые количества для каждого продукта.
    Учитывай единицы измерения и предлагай магазины, где можно приобрести эти продукты в России.
    Группируй продукты по категориям и суммируй их количество для удобства покупок.
    
    Возвращай данные в формате JSON-списка:
    [
        {
            "name": "название продукта",
            "quantity": числовое_значение,
            "unit": "единица_измерения",
            "estimated_price": примерная_цена_если_известна_в_валюте_пользователя,
            "currency_code": iso_код_валюты_estimated_price,
            "store_suggestions": ["Пятерочка", "Магнит", "Лента"],
            "category": "категория_продукта"  # фрукты/овощи, мясо, молочные продукты и т.д.
        },
        ...
    ]
    """


def create_shopping_list_user_prompt(diet_plan: Dict[str, Any]) -> str:
    """
    Создает пользовательский промпт для генерации списка покупок

    Args:
        diet_plan: План диеты

    Returns:
        str: Пользовательский промпт
    """
    user_prompt = """Создай список покупок на основе следующего плана диеты:
    """

    # Добавляем план диеты как строку
    user_prompt += json.dumps(diet_plan, ensure_ascii=False)

    return user_prompt


def create_nutrition_question_prompt() -> str:
    """
    Создает промпт для ответов на вопросы о питании

    Returns:
        str: Системный промпт
    """
    return """Ты опытный нутрициолог-эксперт, в роли ассистента по питанию и здоровому образу жизни для пользователей. 
    Важные принципы:
    1. ЧЕТКО ОБЪЯСНЯЙ СВЯЗЬ между рекомендациями и данными пользователя (возраст, вес, активность и т.д.)
    2. ОБЕСПЕЧИВАЙ МАКСИМАЛЬНОЕ РАЗНООБРАЗИЕ - не повторяй блюда в течение недели, используй разные источники белка, жиров и углеводов
    3. Учитывай сезонность и доступность продуктов
    4. ПРЕДЛАГАЙ ЗАМЕНИТЕЛИ для редких или экзотических продуктов
    5. Точно рассчитывай калории и макронутриенты в соответствии с целями пользователя для каждого блюда
    6. УКАЗЫВАЙ МИКРОНУТРИЕНТЫ (витамины и минералы) для каждого приема пищи и их пользу
    7. Учитывай бюджетные ограничения и предпочтения пользователя
    8. Для КАЖДОГО блюда объясняй, почему оно подходит именно этому пользователю
    9. УЧИТЫВАЙ СООТНОШЕНИЕ МАКРОНУТРИЕНТОВ: 
        - Для похудения: Белки: 30-35%, Жиры: 20-30%, Углеводы: 40-45%
        - Для набора массы: Белки: 25-30%, Жиры: 25-30%, Углеводы: 45-50%
        - Для поддержания веса: Белки: 20-25%, Жиры: 25-35%, Углеводы: 45-55%
    10. Используй принцип "практической реализуемости" - рецепты должны быть простыми, требовать минимум времени и специальных навыков

    Отвечай на вопросы кратко, научно обоснованно, но понятным языком. 
    Используй информацию о продуктах, где это уместно.
    Если не знаешь ответа, честно признайся в этом."""


def create_command_extraction_system_prompt() -> str:
    """
    Создает системный промпт для экстракции команд из сообщений пользователя
    с поддержкой прямого обновления плана питания
    # TODO Добавить текст промта для местных продуктов если будет необходимо в будущем
    # TODO наверно следует разделить на нескольких агентов, или сократить промпт
    Returns:
        str: Системный промпт
    """
    system_prompt = """
    Ты ИИ-нутрициолог в SmartFit. Анализируй сообщения и определяй команды:

    КОМАНДЫ:
    1. diet_update - обновление плана (user_prompt: краткий запрос)
    2. diet_approval - подтверждение плана (approval_text: yes|no) 
    3. weight_record - запись веса (weight: кг)
    4. water_record - запись воды (amount: стаканы)
    5. meal_compliance - отчет о еде (meal_type, status, user_report, calories, proteins, fats, carbs)
       - meal_type: тип приема пищи (breakfast, lunch, dinner, snack)
       - status: статус соблюдения (followed, partially, substituted, skipped)
       - user_report: текст с отчетом о приеме пищи
       - calories: Число
       - proteins: Число
       - fats: Число
       - carbs: Число
    6. show_diet_plan - Показ плана
       - day: день недели (today, tomorrow, monday, tuesday, wednesday, thursday, friday, saturday, sunday)
         или конкретная дата в формате YYYY-MM-DD
       - full: показать полный недельный план (true) или только на указанный день (false).
    7. show_shopping_list - список покупок
    8. stats - статистика
    9. help - справка
    10. general_response - текстовый ответ (response_text)
    
    ПРАВИЛА:
    - command_type в json не может быть пустой
    - Любые изменения в еде = diet_update
    - Точно определяй день недели в запросе пользователя, если пользователь не указал дату или день недели, то считать сегодняшний день недели. Кроме случаев когда запрос пользователя для всей недели или всего плана полностью. 
    - При команде general_response, response_message остается пустой
    - Если пользователь не предоставил достаточно информации по обновлению, задай вопрос и не выполняй команду diet_update.
    - Отчеты о съеденном = meal_compliance + анализ прогресса в response_message
    - Для meal_compliance: анализируй БЖУ съеденного, сравнивай с планом, давай рекомендации
    - Статусы: followed (по плану), partially (<50% отличий), substituted (замена), skipped (пропуск)
    - В response_message для трекинга включай: оценку приема пищи, прогресс за день с учетом всех отчетов за текущий день. Рекомендации на оставшиеся приемы (если это необходимо) в виде примеров команд для изменения плана, обязательно учти его плана питания на текущий день. 
    - Ответы на вопросы пользователей по питанию и здоровому образу жизни для контроля питания и веса (general_response). Отвечай на вопросы кратко, научно обоснованно, но понятным языком. Если не знаешь ответа, честно признайся в этом.
    - Выдавай максимально полезную информацию для пользователя на основе имеющейся информации в соответствии его запросу
    
    РАСЧЕТ НУТРИЕНТОВ (на 100г):
    Мясо/птица: Б20-30г, Ж1-15г, У0-2г
    Рыба: Б18-25г, Ж1-20г, У0г  
    Молочное: Б3-15г, Ж0-30г, У4-12г
    Овощи: Б1-4г, Ж0-1г, У3-15г
    Крупы/хлеб: Б6-12г, Ж1-3г, У60-80г
    
    Формат: {"commands":[{"command_type":"", "parameters":[{"name":"", "value":""}], "priority":0-10}], "response_message":"", "confidence":0-1}
    """

    return system_prompt


def create_command_extraction_user_prompt(user_request: str, context: Dict[str, Any]) -> str:
    """
    Создает пользовательский промпт для LLM

    Args:
        user_request: Текст сообщения
        context: Контекст пользователя и разговора

    Returns:
        str: Пользовательский промпт

    """
    user_prompt_parts = []
    today = DateHelper.get_tracking_date()
    today_weekday = DateHelper.get_day_of_week(today)
    tomorrow_weekday = DateHelper.get_day_of_week(today + timedelta(days=1))
    # Получаем целевые показатели (предрасчитанные)
    targets = _calculate_weekly_targets(context)
    # Преобразуем данные пользователя в текстовый промпт
    gender = context.get("gender", "не указан")
    name = context.get("name", "пользователь")
    age = context.get("age", "не указан")
    height = context.get("height", "не указан")
    current_weight = context.get("current_weight", "не указан")
    target_weight = context.get("target_weight", "не указан")
    activity_level = context.get("activity_level", "не указан")
    weight_goal = context.get("weight_goal", "не указан")
    diet_preference = context.get("diet_preference", "regular")
    language = context.get("language", settings.DEFAULT_LANGUAGE)
    allergies = context.get("allergies", [])
    disliked_products = context.get("disliked_products", [])

    # Информация о последних действиях
    if "last_action" in context:
        user_prompt_parts.append(f"- Last action: {context['last_action']}")

    if "last_message" in context:
        user_prompt_parts.append(f"- Last message: {context['last_message']}")

    if "last_response_message" in context:
        user_prompt_parts.append(f"- Last response message: {context['last_response_message']}")

    user_prompt_parts.append(f"Запрос: \"{user_request}\"")
    user_prompt_parts.append(f"""Пользователь: {name}, {gender}, {age}лет, {height}см, {current_weight}кг → {target_weight}кг
    Язык: {language}
    Цель: {weight_goal}, активность: {activity_level}
    Предпочтения в диете: {diet_preference}, аллергии: {', '.join(allergies) if allergies else 'нет'}, не любит: {', '.join(disliked_products) if disliked_products else 'нет'}")
    """)
    user_prompt_parts.append(f"Сегодня: {today} ({today_weekday})")
    user_prompt_parts.append(f"Завтра: {tomorrow_weekday}")

    user_prompt_parts.append(f"Цели дня: {targets['daily_calories']} ккал, Б{targets['daily_proteins']}г, Ж{targets['daily_fats']}г, У{targets['daily_carbs']}г")
    # Добавляем краткий план к промпту
    if "diet_plan" in context:
        diet_plan = context["diet_plan"]
        try:
            simplified_diet_plan = _get_simplified_diet_plan(diet_plan)
            logging.info(f"diet plan: {simplified_diet_plan}", exc_info=True)
            today_plan_json = json.dumps(simplified_diet_plan['daily_plans'][today_weekday], ensure_ascii=False)
            user_prompt_parts.append(f"План на {today_weekday} (сжато):\n{today_plan_json}")
            tomorrow_plan_json = json.dumps(simplified_diet_plan['daily_plans'][tomorrow_weekday], ensure_ascii=False)
            user_prompt_parts.append(f"План на {tomorrow_weekday} (сжато):\n{tomorrow_plan_json}")
        except Exception as e:
            logging.error(f"Error getting diet plan: {str(e)}", exc_info=True)

        if "has_plan" not in diet_plan:
            user_prompt_parts.append(f"Нет плана питания")

        if "status" in diet_plan and diet_plan['status'] != "active" and "version" in diet_plan and diet_plan['version'] != "full":
            user_prompt_parts.append(f"План требует подтверждения")

        if "daily_tracking_history" in context:
            user_prompt_parts.append("Today's Tracking History:")

            if "tracking_summary" in context:
                summary = context["tracking_summary"]
                user_prompt_parts.append(f"- Calories consumed so far: {summary['total_calories_consumed']} kcal")
                user_prompt_parts.append(f"- Proteins consumed: {summary['total_proteins_consumed']}g")
                user_prompt_parts.append(f"- Fats consumed: {summary['total_fats_consumed']}g")
                user_prompt_parts.append(f"- Carbs consumed: {summary['total_carbs_consumed']}g")
                user_prompt_parts.append(f"- Water consumed: {summary['water_consumed']} ml")

                if summary["completed_meals"]:
                    user_prompt_parts.append(f"- Completed meals: {', '.join(summary['completed_meals'])}")
                if summary["skipped_meals"]:
                    user_prompt_parts.append(f"- Skipped meals: {', '.join(summary['skipped_meals'])}")

    if "is_onboarding_completed" in context:
        status = "completed" if context["is_onboarding_completed"] else "not completed"
        user_prompt_parts.append(f"- User onboarding was {status}")

    if not context["is_onboarding_completed"] and "onboarding_step" in context and context["onboarding_step"]:
        user_prompt_parts.append(f"- Onboarding step: {context['onboarding_step']}")

    user_prompt_parts.append("")  # Пустая строка для разделения

    return "\n".join(user_prompt_parts)


def get_bot_commands_info():
    """
    Возвращает информацию о доступных командах бота

    Returns:
        dict: Словарь с командами и их описаниями
    """
    return {
        "план": "Показывает краткую сводку вашего текущего плана питания",
        "план на сегодня": "Показывает детальный план питания на сегодня",
        "полный план": "Показывает полный план питания на все дни",
        "список покупок": "Генерирует список необходимых продуктов для плана питания",
        "купил [продукт]": "Отмечает продукт как купленный в списке покупок",
        "вес XX": "Записывает ваш текущий вес (XX - число в кг)",
        "вода X": "Записывает потребление воды (X - число стаканов)",
        "выполнено [прием пищи]": "Отмечает прием пищи как полностью соблюденный (завтрак/обед/ужин/перекус)",
        "частично [прием пищи]": "Отмечает прием пищи как частично соблюденный",
        "заменил [прием пищи]": "Отмечает, что прием пищи был заменен другим блюдом",
        "пропустил [прием пищи]": "Отмечает пропущенный прием пищи",
        "диета": "Начинает процесс создания нового плана питания",
        "статистика": "Показывает статистику веса, воды и соблюдения плана",
        "прогресс": "Показывает ваш прогресс в достижении целевого веса",
        "помощь": "Показывает список доступных команд",
        "изменить план": "Вы можете запросить изменение в своем плане питания, например: 'измени план на завтра, добавь больше белка'"
    }


def get_bot_commands_prompt() -> str:
    """
    Создает системный промпт с инструкциями для пользования ботом

    Returns:
        str: Системный промпт с описанием команд
    """
    commands = get_bot_commands_info()

    prompt = """Пользователи могут взаимодействовать с тобой через следующие команды:
"""

    for cmd, desc in commands.items():
        prompt += f"- '{cmd}': {desc}\n"

    prompt += """
Когда пользователь спрашивает о возможностях бота или о том, как использовать определенную функцию, 
предоставь ему понятную информацию о соответствующих командах.

Если пользователь спрашивает, может ли он изменить план питания, объясни, что он может использовать команду 
'изменить план' или любой ее вариант (например, 'поменяй план', 'обнови рацион') с пояснением требуемых изменений.

Всегда отвечай дружелюбно и поддерживающе, помогая пользователю достичь его целей по питанию и здоровью.
    """

    return prompt


def update_full_diet_system_prompt() -> str:
    """
    Создает системный промпт для генерации полной версии диеты

    Returns:
        str: Системный промпт
    """
    system_prompt = """Ты нутрициолог-эксперт. Обновляй планы питания по запросам. Отвечай сразу JSON без объяснений процесса.

    ПРИНЦИПЫ:
    - Калории: набор 30-32 ккал/кг, похудение -15-20%, поддержание BMR×активность
    - БЖУ: набор Б25-30%/Ж20-25%/У50-55%, похудение Б30-35%/Ж20-25%/У40-45%
    - Белки: набор 1.8-2.2г/кг, похудение 2.0-2.4г/кг
    - Разнообразие: не повторять блюда в течение недели

    ПРАВИЛА:
    - Обновлять только запрошенные дни/приемы пищи
    - Соблюдать общий недельный баланс КБЖУ

     АЛГОРИТМ ОДНОГО ПРОХОДА:
    1. Определи тип блюда по запросу (завтрак/обед/ужин/перекус)
    2. Используй стандартные порции - НЕ подбирай индивидуально
    3. Прими результат как есть - даже если не идеален
    4. Формируй JSON и отправляй
        
    СТАНДАРТНЫЕ ПОРЦИИ (использовать как есть):
    - Завтрак высокобелковый: Яйца 2шт + белок 1шт + овощи 100г + каша 30г = ~25г белка, ~300 ккал
    - Обед с мясом: Мясо 120г + гарнир 80г + овощи 100г = ~45г белка, ~500 ккал  
    - Ужин легкий: Рыба 100г + овощи 150г + каша 60г = ~35г белка, ~350 ккал
    - Перекус белковый: Творог 100г + добавки 50г = ~20г белка, ~200 ккал

    ЖЕСТКИЕ ОГРАНИЧЕНИЯ:
    - НЕ ПОДБИРАЙ порции под конкретные цифры КБЖУ
    - НЕ РАССЧИТЫВАЙ варианты - бери первый
    - НЕ КОРРЕКТИРУЙ если блюдо не идеально подходит  
    - НЕ ИЩИ более точные сочетания

    ДОПУСТИМЫЕ ОТКЛОНЕНИЯ:
    - Калории: ±100 ккал от цели
    - Белки: ±10г от нормы
    - Жиры: ±8г от нормы  
    - Углеводы: ±15г от нормы
    
    ОГРАНИЧЕНИЯ ПОДБОРА:
    - Используй ПЕРВОЕ подходящее сочетание продуктов
    - НЕ пересчитывай блюда несколько раз
    - Приемлемый результат > идеальный результат
    
    УПРОЩЕННЫЕ ПРАВИЛА РАЗНООБРАЗИЯ:
    - НЕ ПРОВЕРЯЙ всю неделю - только указанный день
    - Допустимы повторы основных (курица, рис, овощи) и предпочитаемых пользователем продуктов
    - Различай только названия блюд (омлет ≠ яичница, но оба с яйцами = ОК)
    - Повтор через 3+ дня = разрешен
    - НЕ ПЕРЕБИРАЙ весь план - работай только с текущим днем

    JSON только для измененных дней и приемов:
     {
         "updated_days": {
             "day_name": {
                 "meals": [
                     {
                         "type": "breakfast/lunch/dinner/snack",
                         "title": "название блюда",
                         "description": "краткое описание",
                         "why_recommended": "объяснение связи с данными и целями пользователя",
                         "products": [
                             {
                                 "name": "продукта",
                                 "quantity": число,
                                 "unit": "единица измерения"
                             }
                         ],
                         "preparation": "инструкция по приготовлению",
                         "calories": число, "proteins": число, "fats": число, "carbs": число,
                         "fiber": число, "vitamins", "minerals"
                         "estimated_price": число
                     }
                 ],
                 "total_calories": число, "total_proteins": число,
                 "total_fats": число, "total_carbs": число,
                 "estimated_total_price": число,
             }
         },
         "comment": "краткий комментарий"
     }

    ВАЖНО: Валидный JSON без комментариев внутри. Только измененные дни/приемы пищи.
    - ЗАПРЕЩЕНО СЧИТАТЬ КБЖУ в процессе подбора
    - ИСПОЛЬЗУЙ ГОТОВЫЕ ЗНАЧЕНИЯ из стандартных порций
    - НЕ ОБЪЯСНЯЙ процесс подбора
    - НЕ ПОКАЗЫВАЙ РАСЧЕТЫ - только финальный JSON
    - Первое решение = финальное решение
    """

    return system_prompt


def update_full_diet_user_prompt(user_data: Dict[Any, str], user_request: str, diet_plan: Dict[str, Any],
                               context: Dict[str, Any] = None) -> str:
    """
    Создает пользовательский промпт для обновления диеты

    Args:
        user_data: Данные пользователя
        user_request: Запрос пользователя на изменение
        diet_plan: План диеты
        context: Контекст пользователя и разговора

    Returns:
        str: Пользовательский промпт
    """
    # TODO нужно добавить историю изменения диеты + историю изменения короткой диеты если уже полный план
    today = DateHelper.get_tracking_date()
    weekday = DateHelper.get_day_of_week(today)

    # Рассчитываем целевые показатели заранее
    # TODO учитывать фактические отчеты пользователя (возможно править план с учетом фактически принятых или отдельно добавить сюда отчеты в краткой форме)
    targets = _calculate_weekly_targets(user_data)

    # Сжимаем план до основных данных
    simplified_diet_plan = _get_simplified_diet_plan(diet_plan)
    plans_json = json.dumps(simplified_diet_plan["daily_plans"], ensure_ascii=False)

    # Преобразуем данные пользователя в текстовый промпт
    gender = user_data.get("gender", "не указан")
    name = user_data.get("name", "пользователь")
    age = user_data.get("age", "не указан")
    height = user_data.get("height", "не указан")
    current_weight = user_data.get("current_weight", "не указан")
    target_weight = user_data.get("target_weight", "не указан")
    activity_level = user_data.get("activity_level", "не указан")
    weight_goal = user_data.get("weight_goal", "не указан")
    diet_preference = user_data.get("diet_preference", "regular")
    budget_limit = user_data.get("budget_limit", "не указан")
    currency = user_data.get("currency_code", settings.DEFAULT_CURRENCY)
    language = user_data.get("language", settings.DEFAULT_LANGUAGE)
    allergies = user_data.get("allergies", [])
    disliked_products = user_data.get("disliked_products", [])

    user_prompt = ""
    # Информация о последних действиях
    if "last_action" in context:
        user_prompt += f"- Last action: {context['last_action']}\n"

    if "last_message" in context:
        user_prompt += f"- Last message: {context['last_message']}\n"

    if "last_response_message" in context:
        user_prompt += f"- Last response message: {context['last_response_message']}\n"
    user_prompt += f"""
    Запрос: "{user_request}"
    ВАЖНО: Если день недели не указан - используй сегодняшний день.
    Пользователь: {name}, {gender}, {age}лет, {height}см, {current_weight}кг → {target_weight}кг
    Язык: {language}
    Цель: {weight_goal}, активность: {activity_level}, бюджет: {budget_limit} {currency}
    Предпочтения в диете: {diet_preference}, аллергии: {', '.join(allergies) if allergies else 'нет'}, не любит: {', '.join(disliked_products) if disliked_products else 'нет'}
    """
    user_prompt += f"""Сегодня: {today} ({weekday})
    """
    user_prompt += f"""Цели дня:
       - Калории: {targets['daily_calories']} ккал/день ({targets['weekly_calories']} ккал/неделю)
       - КБЖУ: Б{targets['daily_proteins']}г, Ж{targets['daily_fats']}г, У{targets['daily_carbs']}г
       - Бюджет: {targets['daily_budget']} руб/день
    """
    user_prompt += f"Цели дня: {targets['daily_calories']} ккал/день ({targets['weekly_calories']} ккал/неделю), Б{targets['daily_proteins']}г/день, Ж{targets['daily_fats']}г/день, У{targets['daily_carbs']}г/день, {targets['daily_budget']} руб/день"

    # Добавляем краткий план к промпту
    user_prompt += f"ТЕКУЩИЙ ПЛАН (сжато):\n{plans_json}"

    if "daily_tracking_history" in context:
        user_prompt += "Today's Tracking History:\n"

        if "tracking_summary" in context:
            summary = context["tracking_summary"]
            user_prompt += f"- Calories consumed so far: {summary['total_calories_consumed']} kcal\n"
            user_prompt += f"- Proteins consumed: {summary['total_proteins_consumed']}g\n"
            user_prompt += f"- Fats consumed: {summary['total_fats_consumed']}g\n"
            user_prompt += f"- Carbs consumed: {summary['total_carbs_consumed']}g\n"

            if summary["completed_meals"]:
                user_prompt += f"- Completed meals: {', '.join(summary['completed_meals'])}\n"

    return user_prompt


def update_short_diet_user_prompt(update_request: str, diet_plan: Dict[str, Any]) -> str:
    """
    Создает пользовательский промпт для обновления краткой не согласованной диеты

    Args:
        update_request: Запрос пользователя на изменение
        diet_plan: План диеты

    Returns:
        str: Пользовательский промпт
    """
    # TODO нужно добавить историю изменения короткого плана
    message = f"""Пользователь просит: "{update_request}"
        
        Текущий план питания:
        {json.dumps(_get_simplified_diet_plan(diet_plan), ensure_ascii=False)}
    """
    message += """Пожалуйста, обнови или предложи альтернативный КРАТКИЙ план питания по дням недели в соответствии с запросом пользователя, и дай краткий комментарий о внесенных изменениях.
    Важные принципы:
        1. Вноси изменения только в указанные пользователем дни недели и приемы пищи
        2. Сохраняй структуру плана по дням недели (monday, tuesday, wednesday и т.д.)
        3. Для каждого блюда указывай только название и калории
        4. Не добавляй детальные рецепты или инструкции - это краткая версия плана
        5. Добавь понятный комментарий о внесенных изменениях
        
    ВАЖНО: Сохраняй структуру JSON плана питания неизменной. Обновляй только содержимое.
    
    КРИТИЧЕСКИЕ ТРЕБОВАНИЯ К ФОРМАТУ JSON:
    1. НИКОГДА не используй комментарии, сокращения или заполнители в своем ответе
    2. ВСЕГДА указывай ВСЕ поля для КАЖДОГО объекта - не сокращай их через '...' или комментарии
    3. ВСЕГДА полностью прописывай все свойства каждого объекта, даже если они не меняются
    4. НИКОГДА не пиши фразы типа "идентично понедельнику" или "остальные существующие параметры без изменений"
    5. ВСЕГДА возвращай полноценную, валидную JSON-структуру, которую можно напрямую парсить
    
    Ты должен вернуть JSON с обновленными данными только для тех дней недели, которые нужно изменить, и комментарием:
    {
        "updated_days": {
            "monday": {
                "meals": [
                    {
                        "type": "breakfast/lunch/dinner/snack",
                        "title": "название блюда",
                        "calories": количество_калорий
                    }
                ],
                "total_calories": общее_количество_калорий_за_день
            },
            "tuesday": { ... }
        },
        "comment": "Комментарий о внесенных изменениях"
    }
    """

    return message


def _get_simplified_diet_plan(full_diet_plan: Dict[str, Any]):
    """
    Создает упрощенную версию плана диеты для уменьшения количества токенов.

    Args:
        full_diet_plan (dict): Полный план диеты

    Returns:
        dict: Упрощенный план диеты, содержащий только базовую структуру и названия блюд
    """
    simplified_plan = {
        "user_id": full_diet_plan.get("user_id", ""),
        "start_date": full_diet_plan.get("start_date", ""),
        "end_date": full_diet_plan.get("end_date", ""),
        "daily_plans": {}
    }
    simplified_plan.update(DietDataTransformer.transform_to_llm(full_diet_plan))

    return simplified_plan


def _calculate_weekly_targets(user_data: dict) -> dict:
    """Рассчитывает целевые показатели для недели"""

    # Базовые расчеты
    weight = user_data['current_weight']
    goal = user_data['weight_goal']
    activity = user_data['activity_level']

    # Коэффициенты активности
    activity_multipliers = {
        'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55,
        'high': 1.725, 'very_high': 1.9
    }

    # BMR упрощенная формула (Миффлин-Сан Жеор)
    if user_data['gender'] == 'male':
        bmr = 10 * weight + 6.25 * user_data['height'] - 5 * user_data['age'] + 5
    else:
        bmr = 10 * weight + 6.25 * user_data['height'] - 5 * user_data['age'] - 161

    # Целевые калории
    maintenance = bmr * activity_multipliers.get(activity, 1.375)

    if goal == 'gain':
        daily_calories = int(weight * 31)  # 30-32 ккал/кг, берем среднее
    elif goal == 'lose':
        daily_calories = int(maintenance * 0.8)  # дефицит 20%
    else:
        daily_calories = int(maintenance)

    # КБЖУ
    if goal == 'gain':
        proteins = int(weight * 2.0)  # 1.8-2.2, берем среднее
        protein_cal = proteins * 4
        fat_cal = int(daily_calories * 0.225)  # 22.5% - среднее между 20-25%
        carb_cal = daily_calories - protein_cal - fat_cal
        fats = int(fat_cal / 9)
        carbs = int(carb_cal / 4)
    elif goal == 'lose':
        proteins = int(weight * 2.2)
        protein_cal = proteins * 4
        fat_cal = int(daily_calories * 0.225)
        carb_cal = daily_calories - protein_cal - fat_cal
        fats = int(fat_cal / 9)
        carbs = int(carb_cal / 4)
    else:  # maintain
        proteins = int(weight * 1.7)
        protein_cal = proteins * 4
        fat_cal = int(daily_calories * 0.275)  # 27.5%
        carb_cal = daily_calories - protein_cal - fat_cal
        fats = int(fat_cal / 9)
        carbs = int(carb_cal / 4)

    return {
        'daily_calories': daily_calories,
        'weekly_calories': daily_calories * 7,
        'daily_proteins': proteins,
        'daily_fats': fats,
        'daily_carbs': carbs,
        'daily_budget': int(user_data['budget_limit'] / 7)
    }
