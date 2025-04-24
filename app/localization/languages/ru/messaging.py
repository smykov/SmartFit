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
    'delayedMassage': LocalizationString('Отложенное сообщение: '),
    'error': LocalizationString('Извините, произошла при обработки входящего сообщения. Пожалуйста, попробуйте позже.'),
    # Keys for message processor
    'userNotFound': LocalizationString('Пользователь не найден'),
    'noPendingPlan': LocalizationString('Ожидающий план диеты не найден'),
    'noDietPlan': LocalizationString('У вас нет активного плана диеты. Используйте команду "диета" для создания.'),
    'updatingPlan': LocalizationString('Обновляю ваш план диеты...'),
    'updateFailed': LocalizationString('Не удалось обновить план диеты. Пожалуйста, попробуйте снова.'),

}

# Create localization module
module = LocalizationModule(strings)