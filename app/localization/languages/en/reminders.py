# app/localization/languages/en/reminders.py
from app.localization.base import LocalizationString, LocalizationModule

# Строки для модуля напоминаний
strings = {
    'greeting': LocalizationString('👋 Hello'),

    'type': {
        'onboarding': LocalizationString('onboarding'),
        'weight': LocalizationString('weight'),
        'water': LocalizationString('water'),
        'breakfast': LocalizationString('breakfast'),
        'lunch': LocalizationString('lunch'),
        'dinner': LocalizationString('dinner'),
        'weekly_report': LocalizationString('weekly_report'),
        'plan_approval': LocalizationString('plan_approval'),
    },

    'weight': LocalizationString(
        '⚖️ Hi! Don\'t forget to record your weight today. This helps track your progress. Just type \'weight XX\', where XX is your weight in kilograms.\n\n📊 To see full progress, type \'stats\' or \'progress\'.'
    ),

    'water': LocalizationString(
        '💧 Don\'t forget to drink water! Send \'water X\', where X is the number of glasses you\'ve drunk.\n\n📊 To see full statistics, type \'stats\'.'
    ),

    'breakfast': LocalizationString('🍳 Good morning! Don\'t forget to mark your breakfast today.'),

    'lunch': LocalizationString('🍲 It\'s lunch time! Don\'t forget to mark your lunch today.'),

    'dinner': LocalizationString('🍽️ Good evening! Don\'t forget to mark your dinner today.'),

    'plan_approval': {
        'initial': LocalizationString(
            '👋 We\'re reminding you that you have a meal plan waiting for your approval. Would you like to review it now?'
        ),
        'same_day': LocalizationString(
            '👋 You still have a meal plan waiting for your approval from today. Would you like to review it now?'
        ),
        'days': LocalizationString(
            '👋 You have a meal plan that has been waiting for your approval for {days} days. Would you like to review it now?'
        ),
    },

    'onboarding': {
        'name': LocalizationString(
            'We need your name to continue setup. Please tell us how we should address you.'
        ),
        'basic_info': LocalizationString(
            'Let\'s continue the setup. We need some basic information about you for a personalized meal plan.'
        ),
        'weight_info': LocalizationString(
            'We need information about your weight to set up a meal plan. Let\'s continue from where we left off.'
        ),
        'almost_complete': LocalizationString(
            'You\'re almost done with the setup! Just a few more questions to complete your profile.'
        ),
        'default': LocalizationString(
            'Let\'s continue registration to create your personalized meal plan.'
        ),
    },
}

# Создаем модуль локализации
module = LocalizationModule(strings)