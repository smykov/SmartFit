from app.localization.base import LocalizationString, LocalizationModule

# Строки для ошибок
strings = {
    'errors': {
        'general': LocalizationString('Извините, произошла ошибка. Пожалуйста, попробуйте позже.'),
        'ai_fallback_response': LocalizationString("Извините, у меня возникли технические трудности с обработкой вашего запроса. Попробуйте использовать базовые команды, например: 'план', 'вода 2', 'вес 68.5', 'помощь'."),
        'nutrition_question': LocalizationString(
            'Извините, произошла ошибка при обработке вашего вопроса о питании. Пожалуйста, попробуйте позже.'),
    }
}

# Создаем модуль локализации
module = LocalizationModule(strings)
