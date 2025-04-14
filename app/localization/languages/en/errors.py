from app.localization.base import LocalizationString, LocalizationModule

# Строки для ошибок
strings = {
    'errors.general': LocalizationString('Sorry, an error occurred. Please try again later.'),
    'errors.nutrition_question': LocalizationString('Sorry, I encountered an error while processing your nutrition question. Please try again later.'),
}

# Создаем модуль локализации
module = LocalizationModule(strings)