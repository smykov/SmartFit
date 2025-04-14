from app.localization.base import LocalizationString, LocalizationModule

# Строки для напоминаний
strings = {
    'greeting': LocalizationString('👋 Hello'),
    'type.onboarding': LocalizationString('onboarding'),
    'type.weight': LocalizationString('weight'),
    'type.water': LocalizationString('water'),
    'type.breakfast': LocalizationString('breakfast'),
    'type.lunch': LocalizationString('lunch'),
    'type.dinner': LocalizationString('dinner'),
    'type.weekly_report': LocalizationString('weekly_report'),
    'type.plan_approval': LocalizationString('plan_approval'),

    'weight': LocalizationString(
        '⚖️ Hello! Don\'t forget to record your weight today. This will help track your progress. Simply type \'weight XX\', where XX is your weight in kilograms.\n\n📊 To see your full progress, type \'stats\' or \'progress\'.'),
    'water': LocalizationString(
        '💧 Don\'t forget to drink water! Send \'water X\', where X is the number of glasses you have drunk.\n\n📊 To see your complete statistics, type \'stats\'.'),
    'breakfast': LocalizationString('🍳 Good morning! Don\'t forget to record your breakfast compliance today.'),
    'lunch': LocalizationString('🍲 It\'s lunch time! Don\'t forget to record your lunch compliance today.'),
    'dinner': LocalizationString('🍽️ Good evening! Don\'t forget to record your dinner compliance today.'),

    'plan_approval.initial': LocalizationString(
        '👋 Just a reminder that you have a diet plan waiting for your approval. Would you like to review it now?'),
    'plan_approval.same_day': LocalizationString(
        '👋 You still have a diet plan waiting for your approval from earlier today. Would you like to review it now?'),
    'plan_approval.days': LocalizationString(
        '👋 You have a diet plan that has been waiting for your approval for {days} days. Would you like to review it now?'),

    'onboarding.name': LocalizationString(
        'We need your name to continue with the setup. Please let us know what to call you.'),
    'onboarding.basic_info': LocalizationString(
        'Let\'s continue with your setup. We need some basic information about you to create a personalized diet plan.'),
    'onboarding.weight_info': LocalizationString(
        'We need information about your weight to customize your diet plan. Let\'s continue where we left off.'),
    'onboarding.almost_complete': LocalizationString(
        'You\'re almost done with the setup! Just a few more questions to complete your profile.'),
    'onboarding.default': LocalizationString(
        'Let\'s continue with your registration to create your personalized diet plan.'),
}

# Создаем модуль локализации
module = LocalizationModule(strings)