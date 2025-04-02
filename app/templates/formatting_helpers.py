import json
import re
from typing import Dict, Any


def format_message_with_emojis(message_type: str, content: str) -> str:
    """
    Форматирует сообщение с эмодзи для лучшей читаемости

    Args:
        message_type: Тип сообщения
        content: Содержимое сообщения

    Returns:
        str: Отформатированное сообщение
    """
    emoji_map = {
        "greeting": "👋",
        "diet_plan": "🍽️",
        "weight": "⚖️",
        "water": "💧",
        "progress": "📊",
        "tip": "💡",
        "warning": "⚠️",
        "success": "✅",
        "error": "❌",
        "question": "❓",
        "calendar": "📅",
        "shopping": "🛒",
        "recipe": "📝",
        "goal": "🎯",
        "motivation": "💪",
        "medal": "🏅",
        "time": "⏰",
        "money": "💰",
        "fire": "🔥",
        "star": "⭐",
    }

    emoji = emoji_map.get(message_type, "ℹ️")
    return f"{emoji} *{message_type.upper()}*\n{content}"


def create_meal_emoji(meal_type: str) -> str:
    """
    Возвращает эмодзи для типа приема пищи

    Args:
        meal_type: Тип приема пищи

    Returns:
        str: Эмодзи
    """
    emoji_map = {
        "breakfast": "🍳",
        "lunch": "🍲",
        "dinner": "🍽️",
        "snack": "🥪"
    }

    return emoji_map.get(meal_type.lower(), "🍴")


def format_diet_message_for_whatsapp(diet_text: str) -> str:
    """
    Форматирует текст диеты для WhatsApp

    Args:
        diet_text: Текст диеты

    Returns:
        str: Отформатированный текст
    """
    # Добавляем отступы для лучшей читаемости
    formatted_text = diet_text

    # Выделяем заголовки
    # formatted_text = re.sub(r'([*][^*\n]+[*])', r'\n\1\n', formatted_text)

    # Добавляем отступы между маркерами списка
    formatted_text = re.sub(r'(•[^\n]+)', r'\1\n', formatted_text)

    # Убираем лишние пустые строки
    formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)

    return formatted_text


def get_relevance_stars(score: int) -> str:
    """
    Возвращает звездочки для отображения релевантности

    Args:
        score: Оценка релевантности (1-10)

    Returns:
        str: Строка со звездочками
    """
    if not score:
        return ""

    # Преобразуем оценку 1-10 в шкалу 1-5 звезд
    stars_count = max(1, min(5, round(score / 2)))
    return "★" * stars_count


def translate_day_name(day_name: str) -> str:
    """
    Переводит название дня недели на русский

    Args:
        day_name: Название дня на английском

    Returns:
        str: Название дня на русском
    """
    translations = {
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье"
    }
    return translations.get(day_name, day_name)


def translate_meal_type(meal_type: str) -> str:
    """
    Переводит тип приема пищи на русский

    Args:
        meal_type: Тип приема пищи на английском

    Returns:
        str: Тип приема пищи на русском
    """
    translations = {
        "Breakfast": "Завтрак",
        "breakfast": "Завтрак",
        "Lunch": "Обед",
        "lunch": "Обед",
        "Dinner": "Ужин",
        "dinner": "Ужин",
        "Snack": "Перекус",
        "snack": "Перекус"
    }
    return translations.get(meal_type, meal_type)


def get_compliance_emoji(status: str) -> str:
    """
    Возвращает эмодзи для статуса соблюдения

    Args:
        status: Статус соблюдения

    Returns:
        str: Эмодзи
    """
    emoji_map = {
        "followed": "✅",
        "partially": "⚠️",
        "substituted": "🔄",
        "skipped": "❌",
        "not_recorded": "❓"
    }
    return emoji_map.get(status, "❓")


def clean_json_from_markdown(response: str) -> str:
    """
    Очищает JSON от markdown блоков

    Args:
        response: Ответ от API

    Returns:
        str: Очищенный JSON
    """
    # Если ответ содержит ошибку, возвращаем как есть
    if response.startswith("Error:"):
        return response

    # Проверяем различные форматы markdown для JSON
    if response.startswith("```json") and response.endswith("```"):
        response = response[7:-3].strip()
    elif response.startswith("``json") and response.endswith("``"):  # Обработка формата с двумя обратными кавычками
        response = response[6:-2].strip()
    elif response.startswith("```") and response.endswith("```"):
        response = response[3:-3].strip()
    elif response.startswith("``") and response.endswith("``"):
        response = response[2:-2].strip()
    elif response.startswith("`") and response.endswith("`"):
        response = response[1:-1].strip()

    # Проверка на наличие управляющих символов в начале
    if response and not response[0].isalnum() and not response[0] in '{["':
        response = response[1:].strip()

    # Проверка наличия JSON-структуры в начале ответа
    if not response.startswith('{') and not response.startswith('['):
        # Ищем начало JSON-структуры в тексте
        json_start = response.find('{')
        if json_start != -1:
            response = response[json_start:]
        else:
            json_start = response.find('[')
            if json_start != -1:
                response = response[json_start:]

    # Проверка на наличие дополнительного текста после JSON-структуры
    try:
        # Пытаемся распарсить как JSON для проверки
        json_obj = json.loads(response)
        # Если успешно, возвращаем исходный очищенный ответ
        return response
    except json.JSONDecodeError as e:
        # Пытаемся найти окончание JSON-структуры
        if '}' in response:
            last_brace = response.rindex('}')
            if last_brace < len(response) - 1:
                response = response[:last_brace + 1]
        elif ']' in response:
            last_bracket = response.rindex(']')
            if last_bracket < len(response) - 1:
                response = response[:last_bracket + 1]

    return response