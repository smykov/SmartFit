from app.localization.base import LocalizationString, LocalizationModule

# Общие строки
strings = {
    'yes': LocalizationString('Да'),
    'no': LocalizationString('Нет'),
    'save': LocalizationString('Сохранить'),
    'cancel': LocalizationString('Отмена'),
    'error': LocalizationString('Ошибка'),
    'success': LocalizationString('Успешно'),
    'weekday_names.monday': LocalizationString('Понедельник'),
    'weekday_names.tuesday': LocalizationString('Вторник'),
    'weekday_names.wednesday': LocalizationString('Среда'),
    'weekday_names.thursday': LocalizationString('Четверг'),
    'weekday_names.friday': LocalizationString('Пятница'),
    'weekday_names.saturday': LocalizationString('Суббота'),
    'weekday_names.sunday': LocalizationString('Воскресенье'),
    'meal_types.breakfast': LocalizationString('Завтрак'),
    'meal_types.lunch': LocalizationString('Обед'),
    'meal_types.dinner': LocalizationString('Ужин'),
    'meal_types.snack': LocalizationString('Перекус'),
    'meal_emojis.breakfast': LocalizationString('🍳'),
    'meal_emojis.lunch': LocalizationString('🍲'),
    'meal_emojis.dinner': LocalizationString('🍽️'),
    'meal_emojis.snack': LocalizationString('🥪'),
    'day_format': LocalizationString('%d.%m.%Y'),
    'help_commands_list': LocalizationString('''*📱 ДОСТУПНЫЕ КОМАНДЫ:\n
- *план*: Показывает краткую сводку вашего текущего плана питания\n
- *план на сегодня*: Показывает детальный план питания на сегодня\n
- *полный план*: Показывает полный план питания на все дни\n
- *список покупок*: Генерирует список необходимых продуктов для плана питания\n\n
- *купил [продукт]*: Отмечает продукт как купленный в списке покупок\n
- *вес XX*: Записывает ваш текущий вес (XX - число в кг)\n
- *вода X*: Записывает потребление воды (X - число стаканов)\n
- *выполнено [прием пищи]*: Отмечает прием пищи как полностью соблюденный (завтрак/обед/ужин/перекус)\n
- *частично [прием пищи]*: Отмечает прием пищи как частично соблюденный\n
- *заменил [прием пищи]*: Отмечает, что прием пищи был заменен другим блюдом\n
- *пропустил [прием пищи]*: Отмечает пропущенный прием пищи\n
- *диета*: Начинает процесс создания нового плана питания\n
- *статистика*: Показывает статистику веса, воды и соблюдения плана\n
- *прогресс*: Показывает ваш прогресс в достижении целевого веса\n
- *помощь*: Показывает список доступных команд\n
- *изменить план*: Вы можете запросить изменение в своем плане питания, например: 'измени план на завтра, добавь больше белка'\n
'''),
    # Примеры с плюральными формами
    'days_remaining': LocalizationString(
        '{count} дней осталось',
        plural_forms={
            'one': '{count} день остался',
            'few': '{count} дня осталось',
            'many': '{count} дней осталось'
        }
    ),
    # Пример с контекстными вариантами
    'weight_progress': LocalizationString(
        'Вы изменили вес на {change} кг',
        context_variants={
            'lost': 'Вы похудели на {change} кг. Продолжайте в том же духе!',
            'gained': 'Вы набрали {change} кг. Продолжайте работать над собой!'
        }
    ),
}

# Создаем модуль локализации
module = LocalizationModule(strings)