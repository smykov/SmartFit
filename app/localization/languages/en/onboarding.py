# app/localization/languages/en/onboarding.py
from app.localization.base import LocalizationString, LocalizationModule

# Strings for onboarding module
strings = {
    # Welcome and basic onboarding messages
    'welcome': LocalizationString(
        '👋 Welcome to GuateFit - your personal assistant for weight loss. I will help you create a personalized diet plan based on your preferences, local products, and budget.'),
    'nameRequest': LocalizationString('What is your name?'),
    'ageRequest': LocalizationString('How old are you?'),
    'ageRequestExample': LocalizationString('For example: 30'),
    'genderRequest': LocalizationString('What is your gender? (male/female/other):'),
    'genderRequestExample': LocalizationString('For example: male'),
    'heightRequest': LocalizationString('What is your height in centimeters?'),
    'heightRequestExample': LocalizationString('For example: 175'),
    'currentWeightRequest': LocalizationString('What is your current weight in kilograms?'),
    'currentWeightRequestExample': LocalizationString('For example: 80'),
    'targetWeightRequest': LocalizationString('What weight do you want to achieve (in kilograms)?'),
    'activityLevelRequest': LocalizationString('''Rate your level of physical activity:
1. Sedentary lifestyle (little or no physical activity)
2. Light activity (light exercises 1-3 times a week)
3. Moderate activity (moderate exercises 3-5 times a week)
4. High activity (intensive training 6-7 times a week)
5. Very high activity (physical work or 2 workouts a day)

Reply with a number or describe in your own words:'''),
    'weightGoalRequest': LocalizationString('''What is your weight goal?
1. Lose weight
2. Maintain current weight
3. Gain weight

Reply with a number or describe in your own words:'''),
    'dietPreferenceRequest': LocalizationString('''What are your dietary preferences?
1. Regular diet (no restrictions)
2. Vegetarian (no meat, but eggs and dairy are allowed)
3. Vegan (only plant-based foods)
4. Low-carb (carbohydrate restriction)
5. Keto (high fat, very low carbohydrate)
6. Gluten-free (no wheat, rye, or barley)

Reply with a number or describe in your own words:'''),
    'allergiesRequest': LocalizationString(
        'Do you have any food allergies? List them separated by commas or write "no":'),
    'dislikedProductsRequest': LocalizationString(
        'Are there products you don\'t like or don\'t want to include in your diet? List them separated by commas or write "no":'),
    'budgetRequest': LocalizationString('What is your weekly food budget (in quetzales)?'),
    'completed': LocalizationString(
        '🎉 Congratulations! You have completed the setup. Now you can use commands like "plan", "stats", "weight XX", "water X" to interact with GuateFit.'),
    'invalidInput': LocalizationString('❌ Invalid input. Please try again.\n\n{step_message}'),

    # Weight goal determination messages
    'weightGoalDeterminedLose': LocalizationString(
        'I see that you want to lose weight. I\'ll customize your diet plan accordingly.'),
    'weightGoalDeterminedGain': LocalizationString(
        'I see that you want to gain weight. I\'ll customize your diet plan accordingly.'),
    'weightGoalDeterminedMaintain': LocalizationString(
        'I see that you want to maintain your current weight. I\'ll customize your diet plan accordingly.'),

    'answers.yes': LocalizationString('yes'),
    'answers.no': LocalizationString('no'),
    'answers.none': LocalizationString('none'),
    'answers.no_have': LocalizationString("don't have"),

    'gender.male': LocalizationString('male'),
    'gender.female': LocalizationString('female'),
    'gender.other': LocalizationString('other'),
    'gender.male_short': LocalizationString('m'),
    'gender.female_short': LocalizationString('f'),

    'activity_level.sedentary': LocalizationString('sedentary'),
    'activity_level.light': LocalizationString('light'),
    'activity_level.moderate': LocalizationString('moderate'),
    'activity_level.high': LocalizationString('high'),
    'activity_level.very_high': LocalizationString('very high'),

    'weight_goal.lose': LocalizationString('lose'),
    'weight_goal.maintain': LocalizationString('maintain'),
    'weight_goal.gain': LocalizationString('gain'),

    'diet_preference.regular': LocalizationString('regular'),
    'diet_preference.vegetarian': LocalizationString('vegetarian'),
    'diet_preference.vegan': LocalizationString('vegan'),
    'diet_preference.low_carb': LocalizationString('low carb'),
    'diet_preference.keto': LocalizationString('keto'),
    'diet_preference.gluten_free': LocalizationString('gluten free'),

    'budget.unlimited': LocalizationString('unlimited'),
    'budget.no_limit': LocalizationString('no limit'),
    'budget.any': LocalizationString('any'),

}

# Create localization module
module = LocalizationModule(strings)