from app.localization.base import LocalizationString, LocalizationModule

# Строки для модуля трекинга (русский)
strings = {
    # Сообщения для весовых данных
    'weight.recorded': LocalizationString('✅ Отлично! Я записал твой вес: {weight} кг.'),
    'weight.progress': LocalizationString(
        '📉 С начала ты уже похудел(а) на {weight_change:.1f} кг ({percentage:.1f}% от начального веса)'),
    'weight.change': LocalizationString(
        '📈 С начала ты уже набрал(а) {weight_change:.1f} кг ({percentage:.1f}% от начального веса)'),
    'weight.goal_remaining': LocalizationString('🎯 До целевого веса осталось: {remaining:.1f} кг (цель: {target} кг)'),
    'weight.goal_percentage': LocalizationString('\n📊 Ты выполнил(а) {percentage:.1f}% своей цели!\n\n'),
    'weight.keep_tracking': LocalizationString('Продолжай отслеживать прогресс регулярно! 💪'),

    # Сообщения для воды
    'water.recorded': LocalizationString('💧 Отлично! Я записал потребление воды: {amount} стаканов (~{ml_amount} мл)'),
    'water.daily_total': LocalizationString('\nСегодня ты выпил(а) всего: {current_intake} мл\n'),
    'water.goal_percentage': LocalizationString('Это {percentage:.1f}% от дневной цели в {goal} мл\n\n'),
    'water.motivation': LocalizationString(
        'Продолжай в том же духе! Регулярное потребление воды помогает контролировать голод и улучшает общее самочувствие.'),

    # Сообщения для соблюдения диеты
    'compliance.followed': LocalizationString('✅ Отлично! {meal_type} выполнен по плану.'),
    'compliance.partially': LocalizationString('⚠️ Хорошо! {meal_type} частично выполнен по плану.'),
    'compliance.substituted': LocalizationString('🔄 Понятно! {meal_type} заменен на другое блюдо.'),
    'compliance.skipped': LocalizationString('❌ Отмечено! {meal_type} пропущен.'),
    'compliance.generic_status': LocalizationString('Записан статус для приема пищи: {meal_type}.'),
    'compliance.overall_score': LocalizationString('\n\nОбщее соблюдение плана на сегодня: {score:.1f}%'),
    'compliance.excellent': LocalizationString('\n\n👍 Отличная работа! Продолжай в том же духе.'),
    'compliance.good': LocalizationString('\n\n👍 Хороший результат! Старайся следовать плану.'),
    'compliance.keep_trying': LocalizationString('\n\n💪 Не сдавайся! Каждый день - это новая возможность.'),

    # Сообщения для статистики
    'stats.header': LocalizationString('*📊 СТАТИСТИКА И ПРОГРЕСС*\n\n'),
    'stats.weight_section': LocalizationString('*⚖️ Прогресс по весу:*\n'),
    'stats.weight_initial': LocalizationString('• Начальный вес: {weight} кг\n'),
    'stats.weight_current': LocalizationString('• Текущий вес: {weight} кг\n'),
    'stats.weight_target': LocalizationString('• Целевой вес: {weight} кг\n\n'),
    'stats.weight_change_negative': LocalizationString('• Изменение: -{change:.1f} кг 👍\n'),
    'stats.weight_change_positive': LocalizationString('• Изменение: +{change:.1f} кг\n'),
    'stats.weight_change_neutral': LocalizationString('• Изменение: 0 кг (вес стабилен)\n'),
    'stats.weight_goal_remaining': LocalizationString('• Осталось до цели: {remaining:.1f} кг\n'),
    'stats.weight_goal_percentage': LocalizationString('• Процент выполнения: {percentage:.1f}%\n\n'),
    'stats.water_section': LocalizationString('*💧 Потребление воды сегодня:*\n'),
    'stats.water_consumed': LocalizationString('• Выпито: {intake} мл\n'),
    'stats.water_goal': LocalizationString('• Цель: {goal} мл\n'),
    'stats.water_percentage': LocalizationString('• Выполнено: {percentage:.1f}%\n\n'),
    'stats.compliance_section': LocalizationString('*🍽️ Соблюдение плана питания:*\n'),
    'stats.compliance_overall': LocalizationString('\nОбщее соблюдение: {score:.1f}%\n\n'),
    'stats.motivation': LocalizationString('💪 *Продолжай в том же духе!* Ты на пути к своей цели.'),
    'stats.weekly_report_header': LocalizationString('📊 *Еженедельный отчет о прогрессе для {user_name}*\n\n'),
    'stats.weight_no_data': LocalizationString('⚖️ *Вес:* Нет данных за последнюю неделю\n'),

    'stats.water_days_tracked': LocalizationString('• Дней отслеживания: {days}/7\n'),
    'stats.water_average': LocalizationString('• Среднее потребление: {avg:.1f} л/день\n'),
    'stats.water_excellent': LocalizationString('• Статус: Отлично! Ты достигаешь целевого потребления воды 👍\n'),
    'stats.water_good': LocalizationString('• Статус: Хорошо, но можно увеличить потребление воды\n'),
    'stats.water_insufficient': LocalizationString('• Статус: Недостаточное потребление воды, старайся пить больше\n'),
    'stats.water_no_data': LocalizationString('💧 *Потребление воды:* Нет данных за последнюю неделю\n'),

    'stats.goal_section': LocalizationString('🎯 *Прогресс к цели:*\n'),
    'stats.goal_target': LocalizationString('• Целевой вес: {target} кг\n'),
    'stats.goal_remaining': LocalizationString('• Осталось: {remaining:.1f} кг\n'),
    'stats.goal_percentage': LocalizationString('• Прогресс: {percentage:.1f}% выполнено\n'),

    'stats.report_error': LocalizationString('Еженедельный отчет недоступен. Пожалуйста, попробуйте позже.'),
}

# Создаем модуль локализации
module = LocalizationModule(strings)