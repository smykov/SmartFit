from app.localization.base import LocalizationString, LocalizationModule

# Строки для пользователей
strings = {
    'user': {
        'not_found': LocalizationString(
            'Извините, информация о вашем пользователе не найдена. Пожалуйста, попробуйте снова или обратитесь в поддержку.'),
    }
}

# Создаем модуль локализации
module = LocalizationModule(strings)
