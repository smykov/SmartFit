from app.localization.base import LocalizationString, LocalizationModule

# Messaging strings
strings = {
    'invalidMessageFormat': LocalizationString('Неверный формат сообщения'),
    'welcomeNewUser': LocalizationString('Добро пожаловать в GuateFit! Давайте начнем с настройки вашего профиля.'),
    'messageAlreadyProcessed': LocalizationString('Это сообщение уже обработано'),
    'commandNotFound': LocalizationString('Извините, я не смог понять эту команду. Введите "помощь" для просмотра доступных команд.'),
    'unknownCommand': LocalizationString('Неизвестная команда: {text}'),
    'prerequisitesNotMet': LocalizationString('Невозможно выполнить эту команду в данный момент'),
    'processingCommand': LocalizationString('Обрабатываю вашу команду...'),
}

# Create localization module
module = LocalizationModule(strings)