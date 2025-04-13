from app.localization.base import LocalizationString, LocalizationModule

# Общие строки
strings = {
    'yes': LocalizationString('Yes'),
    'no': LocalizationString('No'),
    'save': LocalizationString('Save'),
    'cancel': LocalizationString('Cancel'),
    'error': LocalizationString('Error'),
    'success': LocalizationString('Success'),
    'weekday_names.monday': LocalizationString('Monday'),
    'weekday_names.tuesday': LocalizationString('Tuesday'),
    'weekday_names.wednesday': LocalizationString('Wednesday'),
    'weekday_names.thursday': LocalizationString('Thursday'),
    'weekday_names.friday': LocalizationString('Friday'),
    'weekday_names.saturday': LocalizationString('Saturday'),
    'weekday_names.sunday': LocalizationString('Sunday'),
    'meal_types.breakfast': LocalizationString('Breakfast'),
    'meal_types.lunch': LocalizationString('Lunch'),
    'meal_types.dinner': LocalizationString('Dinner'),
    'meal_types.snack': LocalizationString('Snack'),
    'meal_emojis.breakfast': LocalizationString('🍳'),
    'meal_emojis.lunch': LocalizationString('🍲'),
    'meal_emojis.dinner': LocalizationString('🍽️'),
    'meal_emojis.snack': LocalizationString('🥪'),
    'day_format': LocalizationString('%d.%m.%Y'),
    'help_commands_list': LocalizationString('''*📱 AVAILABLE COMMANDS:\n
- *plan*: Shows a summary of your current diet plan\n
- *today's plan*: Shows detailed meal plan for today\n
- *full plan*: Shows the complete meal plan for all days\n
- *shopping list*: Generates a list of necessary products for your diet plan\n\n
- *bought [product]*: Marks a product as purchased in the shopping list\n
- *weight XX*: Records your current weight (XX - number in kg)\n
- *water X*: Records water consumption (X - number of glasses)\n
- *completed [meal]*: Marks a meal as fully followed (breakfast/lunch/dinner/snack)\n
- *partially [meal]*: Marks a meal as partially followed\n
- *substituted [meal]*: Marks that a meal was replaced with another dish\n
- *skipped [meal]*: Marks a skipped meal\n
- *diet*: Starts the process of creating a new diet plan\n
- *stats*: Shows statistics of weight, water and meal plan compliance\n
- *progress*: Shows your progress towards target weight\n
- *help*: Shows a list of available commands\n
- *update plan*: You can request a change in your meal plan, for example: 'update plan for tomorrow, add more protein'\n
'''),
    # Примеры с плюральными формами
    'days_remaining': LocalizationString(
        '{count} days remaining',
        plural_forms={
            'one': '{count} day remaining',
            'few': '{count} days remaining',
            'many': '{count} days remaining'
        }
    ),
    # Пример с контекстными вариантами
    'weight_progress': LocalizationString(
        'You have {change} weight',
        context_variants={
            'lost': 'You have lost {change} kg. Keep it up!',
            'gained': 'You have gained {change} kg. Keep working!'
        }
    ),
}

# Создаем модуль локализации
module = LocalizationModule(strings)