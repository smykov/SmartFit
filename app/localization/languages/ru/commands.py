from app.localization.base import LocalizationString, LocalizationModule

# Строки для модуля команд
strings = {
    # Общие сообщения команд
    'general': {
        'commandNotFound': LocalizationString(
            'Команда не найдена. Напишите "помощь" для просмотра доступных команд.'),
        'executionError': LocalizationString(
            'Произошла ошибка при выполнении команды. Пожалуйста, попробуйте позже.'),
        'unknownCommand': LocalizationString(
            'Неизвестная команда. Напишите "помощь" для получения списка доступных команд.'),
        'prerequisitesNotMet': LocalizationString(
            'Необходимые условия для выполнения команды не выполнены.')
    },

    # Команда веса
    'weight': {
        'recorded': LocalizationString('✅ Отлично! Я записал ваш вес: {weight} кг.'),
        'invalidFormat': LocalizationString(
            'Пожалуйста, введите вес в формате: "вес XX", где XX - ваш вес в килограммах.'),
        'outOfRange': LocalizationString('Значение веса должно быть от 30 до 300 кг.'),
        'invalidValue': LocalizationString('Неверное значение веса. Пожалуйста, введите число.'),
        'error': LocalizationString('Произошла ошибка при записи веса. Пожалуйста, попробуйте позже.')
    },

    # Команда воды
    'water': {
        'recorded': LocalizationString(
            '💧 Отлично! Я записал ваше потребление воды: {amount} стаканов (~{ml_amount} мл).'),
        'invalidFormat': LocalizationString(
            'Пожалуйста, введите потребление воды в формате: "вода X", где X - количество выпитых стаканов.'),
        'outOfRange': LocalizationString('Количество стаканов должно быть от 0 до 20.'),
        'invalidValue': LocalizationString('Неверное значение потребления воды. Пожалуйста, введите число. Например: "вода 2".'),
        'error': LocalizationString('Произошла ошибка при записи потребления воды. Пожалуйста, попробуйте позже.')
    },

    # Команда диеты
    'diet': {
        'generationStarted': LocalizationString(
            '🔄 Начинаю генерацию вашего плана питания. Это займет некоторое время...'),
        'generationDetails': LocalizationString(
            'Я создам персонализированный план питания на основе вашего профиля, предпочтений и целей.'),
        'noDietPlan': LocalizationString('У вас еще нет активного плана питания. Напишите "диета" для создания.'),
        'noDietForToday': LocalizationString('Извините, на сегодня нет доступного плана питания.'),
        'error': LocalizationString('Произошла ошибка при обработке вашего плана питания. Попробуйте еще раз позже.')
    },

    # Команда списка покупок
    'shoppingList': {
        'generating': LocalizationString(
            '🛒 Генерирую список покупок на основе вашего плана питания. Это займет некоторое время...'),
        'error': LocalizationString(
            'Произошла ошибка при создании списка покупок. Пожалуйста, попробуйте позже.'),
        'invalidProductFormat': LocalizationString(
            'Пожалуйста, используйте формат: "купил [название продукта]" для отметки о покупке продукта.'),
        'productMarked': LocalizationString('✅ Отлично! Я отметил "{product}" как купленный.'),
        'productNotFound': LocalizationString(
            'Я не нашел "{product}" в вашем списке покупок. Проверьте название или напишите "список покупок" для просмотра полного списка.'),
        'noDietPlan': LocalizationString(
            'У вас еще нет активного плана питания. Напишите "диета" для создания.')
    },

    # Команда статистики
    'stats': {
        'error': LocalizationString('Произошла ошибка при создании вашей статистики. Пожалуйста, попробуйте позже.'),
        'defaultMessage': LocalizationString(
            'Вот ваша текущая статистика. Напишите "диета" чтобы увидеть ваш текущий план питания или "помощь" для получения списка команд.')
    },

    # Команда соблюдения плана
    'compliance': {
        'followed': LocalizationString('выполнено'),
        'partially': LocalizationString('частично'),
        'substituted': LocalizationString('заменил'),
        'skipped': LocalizationString('пропустил'),
        'invalidFormat': LocalizationString(
            'Пожалуйста, используйте формат: "[статус] [тип приема пищи]", где статус один из: выполнено, частично, заменил, пропустил.'),
        'invalidType': LocalizationString(
            'Неизвестный тип соблюдения. Пожалуйста, используйте один из: выполнено, частично, заменил, пропустил.'),
        'invalidMealType': LocalizationString(
            'Неверный тип приема пищи. Пожалуйста, укажите: завтрак, обед, ужин или перекус.'),
        'noDietPlan': LocalizationString('У вас нет активного плана питания для отслеживания приемов пищи.'),
        'recordError': LocalizationString(
            'Произошла ошибка при записи соблюдения приема пищи. Пожалуйста, попробуйте позже.'),
        'recorded': LocalizationString('Соблюдение плана для {meal_type} записано как {status}.'),
        'statusKeywords': {
            'выполнено': 'followed',
            'выполнил': 'followed',
            'выполнила': 'followed',
            'частично': 'partially',
            'заменил': 'substituted',
            'заменила': 'substituted',
            'пропустил': 'skipped',
            'пропустила': 'skipped'
        },
        'mealTypeKeywords': {
            'завтрак': 'breakfast',
            'утро': 'breakfast',
            'обед': 'lunch',
            'полдень': 'lunch',
            'ужин': 'dinner',
            'вечер': 'dinner',
            'перекус': 'snack',
            'закуска': 'snack'
        },
        'mealTypeDisplay': {
            'breakfast': 'завтрак',
            'lunch': 'обед',
            'dinner': 'ужин',
            'snack': 'перекус'
        }
    },

    # Команда языка
    'language': {
        'languagesList': LocalizationString(
            'Доступные языки:\n\n🇪🇸 Испанский: Напишите "язык es"\n🇷🇺 Русский: Напишите "язык ru"\n🇬🇧 Английский: Напишите "язык en"'),
        'unsupportedLanguage': LocalizationString('Неподдерживаемый код языка. Доступные варианты: {languages}'),
        'unavailableService': LocalizationString('Сервис локализации недоступен.'),
        'languageChanged': LocalizationString('Язык изменен на Русский!')
    },
    # Команда выбора мессенджера
    'messenger': {
        'messengerList': LocalizationString(
            'Доступные мессенджеры:\n\n WhatsApp: Напишите "мессенджер whatsapp"\n, Telegram: Напишите "мессенджер telegram"'),
        'messengerChanged': LocalizationString('Мессенджер изменен на {messenger_name}!'),
        'error': LocalizationString('Произошла ошибка при изменении мессенджера. Пожалуйста, попробуйте позже.')
    },
    # Команда помощи
    'help': {
        'helpText': LocalizationString('Вот список доступных команд:...')
    }
}

# Создаем модуль локализации
module = LocalizationModule(strings)