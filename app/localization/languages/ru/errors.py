from app.localization.base import LocalizationString, LocalizationModule

# Строки для ошибок
strings = {
    'errors.general': LocalizationString('Извините, произошла ошибка. Пожалуйста, попробуйте позже.'),
    'errors.nutrition_question': LocalizationString('Извините, произошла ошибка при обработке вашего вопроса о питании. Пожалуйста, попробуйте позже.'),
}

# Создаем модуль локализации
module = LocalizationModule(strings)