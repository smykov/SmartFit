from app.localization.base import LocalizationString, LocalizationModule

# Строки для модуля трекинга
strings = {
    # Сообщения для весовых данных
    'weight.recorded': LocalizationString('✅ Great! I have recorded your weight: {weight} kg.'),
    'weight.progress': LocalizationString(
        '📉 Since the beginning, you have already lost {weight_change:.1f} kg ({percentage:.1f}% of your initial weight)'),
    'weight.change': LocalizationString(
        '📈 Since the beginning, you have gained {weight_change:.1f} kg ({percentage:.1f}% of your initial weight)'),
    'weight.goal_remaining': LocalizationString(
        '🎯 You need {remaining:.1f} kg more to reach your target weight of {target} kg'),
    'weight.goal_percentage': LocalizationString('\n📊 You have completed {percentage:.1f}% of your goal!\n\n'),
    'weight.keep_tracking': LocalizationString('Keep tracking your progress regularly! 💪'),

    # Сообщения для воды
    'water.recorded': LocalizationString(
        '💧 Excellent! I have recorded your water intake: {amount} glasses (~{ml_amount} ml)'),
    'water.daily_total': LocalizationString('\nToday you have drunk in total: {current_intake} ml\n'),
    'water.goal_percentage': LocalizationString('This is {percentage:.1f}% of your daily goal of {goal} ml\n\n'),
    'water.motivation': LocalizationString(
        'Keep it up! Regular water consumption helps control hunger and improves overall well-being.'),

    # Сообщения для соблюдения диеты
    'compliance.followed': LocalizationString('✅ Excellent! {meal_type} completed according to plan.'),
    'compliance.partially': LocalizationString('⚠️ Good! {meal_type} partially followed the plan.'),
    'compliance.substituted': LocalizationString('🔄 Understood! {meal_type} was replaced with another dish.'),
    'compliance.skipped': LocalizationString('❌ Noted! {meal_type} was skipped.'),
    'compliance.generic_status': LocalizationString('Status recorded for meal: {meal_type}.'),
    'compliance.overall_score': LocalizationString('\n\nOverall plan compliance for today: {score:.1f}%'),
    'compliance.score_components': LocalizationString('Score components: status {status_score}%, nutrients {nutrients_score}%'),
    'compliance.excellent': LocalizationString('\n\n👍 Great work! Keep it up.'),
    'compliance.good': LocalizationString('\n\n👍 Good result! Try to follow the plan.'),
    'compliance.keep_trying': LocalizationString('\n\n💪 Don\'t give up! Every day is a new opportunity.'),

    # Keys for calorie information
    'compliance.calories_info': LocalizationString('Consumed {calories} calories'),
    'compliance.excess': LocalizationString('excess +{percent}%'),
    'compliance.deficit': LocalizationString('deficit -{percent}%'),
    'compliance.on_target': LocalizationString('on target'),

    # Keys for calorie recommendations
    'compliance.calories_exceeded_significantly': LocalizationString(
        '⚠️ You consumed {percent}% more calories than recommended ({actual} instead of {planned} calories). Consider reducing portions in your next meals today.'),
    'compliance.calories_exceeded_slightly': LocalizationString(
        'ℹ️ You consumed slightly more calories than recommended ({actual} instead of {planned} calories). This is within normal range, but keep an eye on your total calorie intake for the day.'),
    'compliance.calories_on_target': LocalizationString(
        '✅ Great job! Your calorie intake is on target ({actual} out of {planned} calories).'),
    'compliance.calories_under': LocalizationString(
        'ℹ️ You consumed {percent}% fewer calories than recommended ({actual} instead of {planned} calories). To reach your goals, it\'s important to consume adequate amounts of food.'),

    # Keys for macronutrients
    'compliance.proteins': LocalizationString('Protein'),
    'compliance.fats': LocalizationString('Fats'),
    'compliance.carbs': LocalizationString('Carbs'),
    'compliance.macros_imbalance': LocalizationString(
        '⚖️ Pay attention to your macronutrient balance: {imbalances}. For optimal results, try to maintain the recommended ratio of proteins, fats, and carbs.'),

    # Сообщения для статистики
    'stats.header': LocalizationString('*📊 STATISTICS AND PROGRESS*\n\n'),
    'stats.weight_section': LocalizationString('*⚖️ Weight progress:*\n'),
    'stats.weight_initial': LocalizationString('• Initial weight: {weight} kg\n'),
    'stats.weight_current': LocalizationString('• Current weight: {weight} kg\n'),
    'stats.weight_target': LocalizationString('• Target weight: {weight} kg\n\n'),
    'stats.weight_change_negative': LocalizationString('• Change: -{change:.1f} kg 👍\n'),
    'stats.weight_change_positive': LocalizationString('• Change: +{change:.1f} kg\n'),
    'stats.weight_change_neutral': LocalizationString('• Change: 0 kg (stable weight)\n'),
    'stats.weight_goal_remaining': LocalizationString('• Remaining to goal: {remaining:.1f} kg\n'),
    'stats.weight_goal_percentage': LocalizationString('• Goal completion: {percentage:.1f}%\n\n'),
    'stats.water_section': LocalizationString('*💧 Water consumption today:*\n'),
    'stats.water_consumed': LocalizationString('• Consumed: {intake} ml\n'),
    'stats.water_goal': LocalizationString('• Goal: {goal} ml\n'),
    'stats.water_percentage': LocalizationString('• Completed: {percentage:.1f}%\n\n'),
    'stats.compliance_section': LocalizationString('*🍽️ Meal plan compliance:*\n'),
    'stats.compliance_overall': LocalizationString('\nOverall compliance: {score:.1f}%\n\n'),
    'stats.score_components_average': LocalizationString('Average components: status {status_score}%, nutrients {nutrients_score}%'),
    'stats.motivation': LocalizationString('💪 *Keep it up!* You are on your way to your goal.'),
    'stats.weekly_report_header': LocalizationString('📊 *Weekly Progress Report for {user_name}*\n\n'),
    'stats.weight_no_data': LocalizationString('⚖️ *Weight:* No data for the last week\n'),

    'stats.water_days_tracked': LocalizationString('• Days tracked: {days}/7\n'),
    'stats.water_average': LocalizationString('• Average consumption: {avg:.1f} l/day\n'),
    'stats.water_excellent': LocalizationString('• Status: Excellent! You are reaching your water goal 👍\n'),
    'stats.water_good': LocalizationString('• Status: Good, but you could increase your water intake\n'),
    'stats.water_insufficient': LocalizationString('• Status: Insufficient water intake, try to drink more\n'),
    'stats.water_no_data': LocalizationString('💧 *Water Consumption:* No data for the last week\n'),

    'stats.goal_section': LocalizationString('🎯 *Progress Towards Goal:*\n'),
    'stats.goal_target': LocalizationString('• Target weight: {target} kg\n'),
    'stats.goal_remaining': LocalizationString('• Remaining: {remaining:.1f} kg\n'),
    'stats.goal_percentage': LocalizationString('• Progress: {percentage:.1f}% complete\n'),
    'stats.last_week': LocalizationString('the last week'),

    'stats.report_error': LocalizationString('Weekly report is unavailable. Please try again later.'),
}

# Создаем модуль локализации
module = LocalizationModule(strings)
