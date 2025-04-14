from app.localization.base import LocalizationString, LocalizationModule

# Строки для ошибок
strings = {
    'errors.general': LocalizationString('Lo sentimos, se ha producido un error. Por favor, inténtelo de nuevo más tarde.'),
    'errors.nutrition_question': LocalizationString('Lo siento, encontré un error al procesar tu pregunta sobre nutrición. Por favor, inténtalo de nuevo más tarde.'),
}

# Создаем модуль локализации
module = LocalizationModule(strings)