from typing import Dict, Any

from main import logger

# Локализованные шаблоны сообщений
LOCALIZED_TEMPLATES = {
    "es": {  # Испанский (исходный)
        "greeting": "👋 ¡Hola! Bienvenido a GuateFit - tu asistente personal para perder peso. Te ayudaré a crear un plan de alimentación adaptado a ti, teniendo en cuenta los productos locales y tu presupuesto. ¡Comencemos con la configuración! ¿Cómo te llamas?",
        "diet_created": "🎉 ¡Tu plan de alimentación está listo! He seleccionado platos teniendo en cuenta tus parámetros y preferencias. Revisa el plan y hazme saber si quieres cambiar algo.\n\n📊 Para ver tus estadísticas y progreso, escribe 'estadísticas' o 'progreso' en cualquier momento.",
        "weight_reminder": "⚖️ ¡Hola! No olvides registrar tu peso hoy. Esto ayudará a seguir tu progreso. Simplemente escribe 'peso XX', donde XX es tu peso en kilogramos.\n\n📊 Para ver tu progreso completo, escribe 'estadísticas' o 'progreso'.",
        "water_reminder": "💧 ¡No olvides beber agua! Envía 'agua X', donde X es el número de vasos que has bebido.\n\n📊 Para ver tus estadísticas completas, escribe 'estadísticas'.",
        "weekly_report": "📊 Aquí está tu informe semanal:\n{progress}\n\n¡Excelente trabajo! ¡Sigue así! 💪",
        "onboarding_complete": "🎉 ¡Felicidades! Has completado la configuración. Ahora puedes usar comandos como 'plan', 'estadísticas', 'peso XX', 'agua X' para interactuar con GuateFit.",

        # Добавляем новые шаблоны из остальных частей кода
        "shopping_list_start": "🛒 Comenzando a generar lista de compras basada en tu plan de alimentación. Esto tomará unos segundos...",
        "shopping_list_error": "Lo siento, ha ocurrido un error al crear la lista de compras. Inténtalo de nuevo más tarde.",
        "no_diet_plan": "Aún no tienes un plan de alimentación activo. Escribe 'dieta' para crear uno nuevo.",
        "weight_recorded": "✅ ¡Excelente! He registrado tu peso: {weight} kg.",
        "water_recorded": "💧 ¡Excelente! He registrado tu consumo de agua: {amount} vasos (~{ml_amount} ml).",
        "weight_progress": "📉 Desde el inicio ya has perdido {weight_change:.1f} kg ({percentage:.1f}% de tu peso inicial)",
        "weight_goal_remaining": "🎯 Te faltan {remaining:.1f} kg para alcanzar tu peso objetivo de {target} kg",
        "diet_compliance_recorded": "Se ha registrado tu cumplimiento del plan alimenticio.",
        "diet_summary_sent": "Resumen de tu plan de alimentación enviado.",
        "help_message": "Aquí están los comandos disponibles:",
        "invalid_meal_type": "Por favor, especifica un tipo de comida válido: desayuno, almuerzo, cena o merienda."
    },
    "ru": {  # Русский
        "greeting": "👋 Привет! Добро пожаловать в GuateFit - твой персональный ассистент для похудения. Я помогу тебе создать план питания, адаптированный под тебя, учитывая местные продукты и твой бюджет. Давай начнем настройку! Как тебя зовут?",
        "diet_created": "🎉 Твой план питания готов! Я подобрал блюда с учетом твоих параметров и предпочтений. Просмотри план и дай мне знать, если хочешь что-то изменить.\n\n📊 Чтобы увидеть свою статистику и прогресс, напиши 'статистика' или 'прогресс' в любое время.",
        "weight_reminder": "⚖️ Привет! Не забудь записать свой вес сегодня. Это поможет отслеживать прогресс. Просто напиши 'вес XX', где XX - твой вес в килограммах.\n\n📊 Чтобы увидеть полный прогресс, напиши 'статистика' или 'прогресс'.",
        "water_reminder": "💧 Не забывай пить воду! Отправь 'вода X', где X - количество стаканов, которые ты выпил(а).\n\n📊 Чтобы увидеть полную статистику, напиши 'статистика'.",
        "weekly_report": "📊 Вот твой еженедельный отчет:\n{progress}\n\nОтличная работа! Продолжай в том же духе! 💪",
        "onboarding_complete": "🎉 Поздравляю! Ты завершил(а) настройку. Теперь ты можешь использовать команды, такие как 'план', 'статистика', 'вес XX', 'вода X', чтобы взаимодействовать с GuateFit.",

        # Добавляем новые шаблоны из остальных частей кода
        "shopping_list_start": "🛒 Начинаю формирование списка покупок на основе твоего плана питания. Это займет несколько секунд...",
        "shopping_list_error": "Извини, произошла ошибка при создании списка покупок. Попробуй позже.",
        "no_diet_plan": "У тебя пока нет активного плана питания. Напиши 'диета' для создания нового плана.",
        "weight_recorded": "✅ Отлично! Я записал твой вес: {weight} кг.",
        "water_recorded": "💧 Отлично! Я записал потребление воды: {amount} стаканов (~{ml_amount} мл).",
        "weight_progress": "📉 С начала ты уже сбросил(а) {weight_change:.1f} кг ({percentage:.1f}% от начального веса)",
        "weight_goal_remaining": "🎯 До целевого веса осталось: {remaining:.1f} кг (цель: {target} кг)",
        "diet_compliance_recorded": "Соблюдение плана питания записано.",
        "diet_summary_sent": "Сводка плана питания отправлена.",
        "help_message": "Вот доступные команды:",
        "invalid_meal_type": "Пожалуйста, укажите корректный тип приема пищи: завтрак, обед, ужин или перекус."
    }
}

DEFAULT_LANGUAGE = "es"


def get_message(key: str, lang: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    """
    Возвращает локализованное сообщение по ключу

    Args:
        key: Ключ сообщения
        lang: Код языка (es, ru)
        **kwargs: Параметры для форматирования

    Returns:
        str: Локализованное сообщение
    """
    # Проверяем существование языка
    if lang not in LOCALIZED_TEMPLATES:
        lang = DEFAULT_LANGUAGE

    # Получаем шаблон сообщения
    template = LOCALIZED_TEMPLATES[lang].get(key)

    # Если шаблон не найден, ищем в языке по умолчанию
    if not template and lang != DEFAULT_LANGUAGE:
        template = LOCALIZED_TEMPLATES[DEFAULT_LANGUAGE].get(key)

    # Если шаблон все еще не найден, возвращаем ключ
    if not template:
        return f"[{key}]"

    # Форматируем сообщение с переданными параметрами
    try:
        return template.format(**kwargs)
    except KeyError as e:
        # В случае ошибки форматирования, возвращаем шаблон как есть
        logger.warning(f"Missing format parameter in template {key}: {e}")
        return template
    except Exception as e:
        # Любая другая ошибка
        logger.error(f"Error formatting message {key}: {e}")
        return template


def get_user_language(user_data: Dict[str, Any]) -> str:
    """
    Определяет язык пользователя на основе его данных

    Args:
        user_data: Данные пользователя

    Returns:
        str: Код языка (es, ru)
    """
    # Получаем язык из данных пользователя, если он есть
    lang = user_data.get("language", DEFAULT_LANGUAGE)

    # Проверяем существование языка
    if lang not in LOCALIZED_TEMPLATES:
        return DEFAULT_LANGUAGE

    return lang