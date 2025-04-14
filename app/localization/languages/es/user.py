from app.localization.base import LocalizationString, LocalizationModule

# Строки для пользователей
strings = {
    'user.not_found': LocalizationString('Lo sentimos, no se pudo encontrar la información de su usuario. Inténtelo de nuevo o póngase en contacto con el soporte.'),
}

# Создаем модуль локализации
module = LocalizationModule(strings)