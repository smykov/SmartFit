from app.localization.base import LocalizationString, LocalizationModule

# Strings for commands module
strings = {
    # General command messages
    'general': {
        'commandNotFound': LocalizationString(
            'Command not found. Type "help" to see available commands.'),
        'executionError': LocalizationString(
            'An error occurred while executing the command. Please try again later.'),
        'unknownCommand': LocalizationString(
            'Unknown command. Type "help" to get a list of available commands.'),
        'prerequisitesNotMet': LocalizationString(
            'The prerequisites for executing the command are not met.')
    },

    # Weight command
    'weight.recorded': LocalizationString('✅ Great! I recorded your weight: {weight} kg.'),
    'weight.invalidFormat': LocalizationString(
        'Please enter your weight in the format: "weight XX", where XX is your weight in kilograms.'),
    'weight.outOfRange': LocalizationString('The weight value must be between 30 and 300 kg.'),
    'weight.invalidValue': LocalizationString('Invalid weight value. Please enter a number.'),
    'weight.error': LocalizationString('An error occurred while recording your weight. Please try again later.'),

    # Water command
    'water.recorded': LocalizationString('💧 Great! I recorded your water intake: {amount} glasses (~{ml_amount} ml).'),
    'water.recorded': LocalizationString('💧 Great! I recorded your water intake: {amount} glasses (~{ml_amount} ml).'),
    'water.invalidFormat': LocalizationString(
        'Please enter your water intake in the format: "water X", where X is the number of glasses you drank.'),
    'water.outOfRange': LocalizationString('The number of glasses must be between 0 and 20.'),
    'water.invalidValue': LocalizationString('Invalid water intake value. Please enter a number.'),
    'water.error': LocalizationString('An error occurred while recording your water intake. Please try again later.'),

    # Help command
    'help.helpText': LocalizationString('''*📱 AVAILABLE COMMANDS:\n
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

    # Diet command
    'diet.generationStarted': LocalizationString(
        '🔄 Starting to generate your diet plan based on your preferences. This will take a few moments...'),
    'diet.generationDetails': LocalizationString(
        'This may take a minute. I\'ll prepare a personalized diet plan for you using local products and considering your goals.'),
    'diet.noDietPlan': LocalizationString('You don\'t have an active diet plan yet. Type "diet" to create one.'),
    'diet.noDietForToday': LocalizationString('Sorry, there is no diet plan available for today.'),

    # Shopping list command
    'shoppingList.generating': LocalizationString(
        '🛒 Generating shopping list based on your diet plan. This will take a few moments...'),
    'shoppingList.error': LocalizationString(
        'An error occurred while generating the shopping list. Please try again later.'),
    'shoppingList.invalidProductFormat': LocalizationString(
        'Please use the format: "bought [product name]" to mark a product as purchased.'),
    'shoppingList.productMarked': LocalizationString('✅ Great! I\'ve marked "{product}" as purchased.'),
    'shoppingList.productNotFound': LocalizationString(
        'I couldn\'t find "{product}" in your shopping list. Check the name or type "shopping list" to see the full list.'),
    'shoppingList.noDietPlan': LocalizationString(
        'You don\'t have an active diet plan yet. Type "diet" to create one.'),

    # Stats command
    'stats.error': LocalizationString('An error occurred while generating your statistics. Please try again later.'),
    'stats.default_message': LocalizationString(
        'Here are your current statistics. Type "diet" to see your current diet plan or "help" for more commands.'),

    # Compliance command
    'compliance.invalidFormat': LocalizationString(
        'Please use the format: "[status] [meal type]", where status is one of: completed, partially, substituted, skipped and breakfast, lunch, dinner, snack.'),
    'compliance.invalidType': LocalizationString(
        'Unknown compliance type. Please use one of: "completed", "partially", "substituted", or "skipped".'),
    'compliance.invalidMealType': LocalizationString(
        'Invalid meal type. Please specify: breakfast, lunch, dinner, or snack.'),
    'compliance.noDietPlan': LocalizationString('You don\'t have an active diet plan for tracking meals.'),
    'compliance.recordError': LocalizationString(
        'An error occurred while recording meal compliance. Please try again later.'),
    'compliance.recorded': LocalizationString('Meal compliance for {meal_type} has been recorded as {status}.'),
    'compliance.statusKeywords': LocalizationString({
        'completed': 'followed',
        'complete': 'followed',
        'followed': 'followed',
        'partially': 'partially',
        'partial': 'partially',
        'substituted': 'substituted',
        'substitute': 'substituted',
        'replaced': 'substituted',
        'skipped': 'skipped',
        'skip': 'skipped'
    }),

    'compliance.mealTypeKeywords': LocalizationString({
        'breakfast': 'breakfast',
        'morning': 'breakfast',
        'lunch': 'lunch',
        'noon': 'lunch',
        'dinner': 'dinner',
        'evening': 'dinner',
        'supper': 'dinner',
        'snack': 'snack',
        'snacks': 'snack'
    }),

    'compliance.mealTypeDisplay': LocalizationString({
        'breakfast': 'breakfast',
        'lunch': 'lunch',
        'dinner': 'dinner',
        'snack': 'snack'
    }),
    # Language command
    'language.languagesList': LocalizationString(
        'Available languages:\n\n🇪🇸 Spanish: Write "language es"\n🇷🇺 Russian: Write "language ru"\n🇬🇧 English: Write "language en"'),
    'language.unsupportedLanguage': LocalizationString('Unsupported language code. Available options: {languages}'),
    'language.unavailableService': LocalizationString('Localization service is not available.'),
    'language.languageChanged': LocalizationString('Language changed to English!'),
}

# Create localization module
module = LocalizationModule(strings)