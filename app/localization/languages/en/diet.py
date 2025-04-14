from app.localization.base import LocalizationString, LocalizationModule

# Общие строки
strings = {
    'plan_not_found': LocalizationString('Diet plan not found'),
    'plan_approved': LocalizationString('Approved, generating the full version of the plan...'),
    'plan_approval_error': LocalizationString('An error occurred while processing the approval'),

    'full': {
        'created': LocalizationString(
            '🎉 Your diet plan is ready! I have selected dishes taking into account your parameters and preferences. Check out the plan and let me know if you want to change anything.'),
        'updating': LocalizationString(
            'I\'m updating your diet plan according to your request. This will take a few moments.'),
        'update_failed': LocalizationString('Sorry, failed to update the diet plan. Please try again later.'),
        'no_plan': LocalizationString(
            'You don\'t have an active diet plan yet. Write "diet" to create a new one.'),
        'creating_error': LocalizationString(
            'An error occurred while creating the diet plan. Please try again later.'),
        'no_updates': LocalizationString('No updates were made to the diet plan.'),
        'summary': {
            'header': '*📋 PERSONAL DIET PLAN*\n\n',
            'deficit': '🔥 *Estimated calorie deficit:* \n{deficit}\n\n',
            'proficit': '🔥 *Estimated calorie surplus:* \n{proficit}\n\n',
            'recommendations': '📝 *General recommendations:* \n{recommendations}\n\n',
            'price': '💰 *Estimated cost:* \n{price} {currency} per week\n\n',
            'day_menu_example': '📅 *Sample menu for {day_name}, {date_formatted}:*\n',
            'meal_format': '{emoji} *{meal_type}*: \n{title} {relevance}\n',
            'calories_format': '  Calories: {calories} kcal\n',
            'why_recommended': '  _Why recommended: {why_recommended}_\n'
        },
        'plan': {
            'commands_message': '''*📱 Commands for interacting with the plan:*
- Type 'full plan' to view the plan for the entire week
- Type 'today\'s plan' or 'today\'s menu' for a detailed plan for today
- Type 'shopping list' to get a list of products
- Type 'completed/partially/substituted/skipped breakfast/lunch/dinner/snack' to mark plan compliance
'''
        }
    },
    'short': {
        'creating_error': 'Error creating short diet plan. Please try again later.',
        'next_step': {
            'header': '*👆 This is a brief version of the plan. The full version will include:*\n',
            'recipes': '• Detailed recipes and cooking instructions\n',
            'nutrition': '• Nutritional information for each dish\n',
            'explanations': '• Explanations of why each dish is recommended specifically for you\n',
            'shopping': '• Shopping list taking into account what you already have\n\n',
            'invalid_version': LocalizationString('Plan is not a short version'),
        }
    },
    'day': {
        'creating_error': 'Error creating day diet plan. Please try again later.',
        'no_plan': 'Unfortunately, there is no meal plan for the specified date.',
        'tracking': {
            'header': '*📱 Mark your plan execution:*\n',
            'followed': '• Type \'completed breakfast/lunch/dinner/snack\' to mark as followed\n',
            'partially': '• Type \'partially breakfast/lunch/dinner/snack\' if you partially followed the plan\n',
            'substituted': '• Type \'substituted breakfast/lunch/dinner/snack\' if you replaced the dish\n',
            'skipped': '• Type \'skipped breakfast/lunch/dinner/snack\' if you skipped the meal\n'
        }
    },
    'update': {
        "success_header": LocalizationString("✅ *Diet plan updated*\n\n{comment}\n"),
        "day_updated_with_date": LocalizationString("\nUpdated menu for *{day_name}, {date_formatted}*"),
        "day_updated": LocalizationString("\nUpdated menu for *{day_name}*"),
        "unknown_day_updated": LocalizationString("\nUpdated menu for {date_str}"),
        "formatting_error": LocalizationString("Error formatting the diet update message. Please try again."),
        "no_updates": LocalizationString(
            "No updates were made to the diet plan. Try specifying what you want to change."),
        'default_comment': LocalizationString('Diet plan updated according to request'),
        'parsing_error': LocalizationString('Failed to parse LLM response'),
        'invalid_format': LocalizationString('Invalid response format from AI'),
        'update_failed': LocalizationString('Failed to update diet plan'),
    },
    'ai': {
        'user_not_found': LocalizationString('Sorry, I could not find user information.'),
        'processing_error': LocalizationString(
            'Sorry, an error occurred while processing your question. Please try again later.'),
    }
}
# Создаем модуль локализации
module = LocalizationModule(strings)
