from app.localization.base import LocalizationString, LocalizationModule

# Строки для модуля команд
strings = {
    # Общие сообщения команд
    'general.commandNotFound': LocalizationString(
        'Команда не найдена. Напишите "помощь" для просмотра доступных команд.'),
    'general.executionError': LocalizationString(
        'Произошла ошибка при выполнении команды. Пожалуйста, попробуйте позже.'),

    # Команда веса
    'weight.recorded': LocalizationString('✅ Отлично! Я записал ваш вес: {weight} кг.'),
    'weight.invalidFormat': LocalizationString(
        'Пожалуйста, введите вес в формате: "вес XX", где XX - ваш вес в килограммах.'),
    'weight.outOfRange': LocalizationString('Значение веса должно быть от 30 до 300 кг.'),
    'weight.invalidValue': LocalizationString('Неверное значение веса. Пожалуйста, введите число.'),
    'weight.error': LocalizationString('Произошла ошибка при записи веса. Пожалуйста, попробуйте позже.'),

    # Команда воды
    'water.recorded': LocalizationString(
        '💧 Отлично! Я записал ваше потребление воды: {amount} стаканов (~{ml_amount} мл).'),
    'water.invalidFormat': LocalizationString(
        'Пожалуйста, введите потребление воды в формате: "вода X", где X - количество выпитых стаканов.'),
    'water.outOfRange': LocalizationString('Количество стаканов должно быть от 0 до 20.'),
    'water.invalidValue': LocalizationString('Неверное значение потребления воды. Пожалуйста, введите число.'),
    'water.error': LocalizationString('Произошла ошибка при записи потребления воды. Пожалуйста, попробуйте позже.'),

    # Команда диеты
    'diet.generationStarted': LocalizationString(
        '🔄 Начинаю генерацию вашего плана питания. Это займет некоторое время...'),
    'diet.generationDetails': LocalizationString(
        'Я создам персонализированный план питания на основе вашего профиля, предпочтений и целей.'),
    'diet.noDietPlan': LocalizationString('У вас еще нет активного плана питания. Напишите "диета" для создания.'),
    'diet.noDietForToday': LocalizationString('Извините, на сегодня нет доступного плана питания.'),
    'diet.error': LocalizationString('Произошла ошибка при обработке вашего плана питания. Попробуйте еще раз позже.'),

    # Команда списка покупок
    'shoppingList.generating': LocalizationString(
        '🛒 Генерирую список покупок на основе вашего плана питания. Это займет некоторое время...'),
    'shoppingList.error': LocalizationString(
        'Произошла ошибка при создании списка покупок. Пожалуйста, попробуйте позже.'),
    'shoppingList.invalidProductFormat': LocalizationString(
        'Пожалуйста, используйте формат: "купил [название продукта]" для отметки о покупке продукта.'),
    'shoppingList.productMarked': LocalizationString('✅ Отлично! Я отметил "{product}" как купленный.'),
    'shoppingList.productNotFound': LocalizationString(
        'Я не нашел "{product}" в вашем списке покупок. Проверьте название или напишите "список покупок" для просмотра полного списка.'),
    'shoppingList.noDietPlan': LocalizationString(
        'У вас еще нет активного плана питания. Напишите "диета" для создания.'),

    # Команда статистики
    'stats.error': LocalizationString('Произошла ошибка при создании вашей статистики. Пожалуйста, попробуйте позже.'),
    'stats.default_message': LocalizationString(
        'Вот ваша текущая статистика. Напишите "диета" чтобы увидеть ваш текущий план питания или "помощь" для получения списка команд.'),

    # Команда соблюдения плана
    'compliance.invalidFormat': LocalizationString(
        'Пожалуйста, используйте формат: "[статус] [тип приема пищи]", где статус один из: выполнено, частично, заменил, пропустил.'),
    'compliance.invalidType': LocalizationString(
        'Неизвестный тип соблюдения. Пожалуйста, используйте один из: выполнено, частично, заменил, пропустил.'),
    'compliance.invalidMealType': LocalizationString(
        'Неверный тип приема пищи. Пожалуйста, укажите: завтрак, обед, ужин или перекус.'),
    'compliance.noDietPlan': LocalizationString('У вас нет активного плана питания для отслеживания приемов пищи.'),
    'compliance.recordError': LocalizationString(
        'Произошла ошибка при записи соблюдения приема пищи. Пожалуйста, попробуйте позже.'),
    'compliance.recorded': LocalizationString('Соблюдение плана для {meal_type} записано как {status}.'),
    'compliance.statusKeywords': LocalizationString({
        'выполнено': 'followed',
        'выполнил': 'followed',
        'выполнила': 'followed',
        'частично': 'partially',
        'заменил': 'substituted',
        'заменила': 'substituted',
        'пропустил': 'skipped',
        'пропустила': 'skipped'
    }),

    'compliance.mealTypeKeywords': LocalizationString({
        'завтрак': 'breakfast',
        'утро': 'breakfast',
        'обед': 'lunch',
        'полдень': 'lunch',
        'ужин': 'dinner',
        'вечер': 'dinner',
        'перекус': 'snack',
        'закуска': 'snack'
    }),

    'compliance.mealTypeDisplay': LocalizationString({
        'breakfast': 'завтрак',
        'lunch': 'обед',
        'dinner': 'ужин',
        'snack': 'перекус'
    }),
    # Команда языка
    'language.languagesList': LocalizationString(
        'Доступные языки:\n\n🇪🇸 Испанский: Напишите "язык es"\n🇷🇺 Русский: Напишите "язык ru"\n🇬🇧 Английский: Напишите "язык en"'),
    'language.unsupportedLanguage': LocalizationString('Неподдерживаемый код языка. Доступные варианты: {languages}'),
    'language.unavailableService': LocalizationString('Сервис локализации недоступен.'),
    'language.languageChanged': LocalizationString('Язык изменен на Русский!'),
}

# Создаем модуль локализации
module = LocalizationModule(strings)