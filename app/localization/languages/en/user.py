from app.localization.base import LocalizationString, LocalizationModule

# Строки для пользователей
strings = {
    'user.not_found': LocalizationString('Sorry, your user information could not be found. Please try again or contact support.'),
}

# Создаем модуль локализации
module = LocalizationModule(strings)