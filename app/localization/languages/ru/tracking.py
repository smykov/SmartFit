from app.localization.base import LocalizationString, LocalizationModule

# Строки для модуля трекинга (русский)
strings = {
    # Сообщения для весовых данных
    'weight': {
        'recorded': LocalizationString('✅ Отлично! Я записал твой вес: {weight} кг.'),
        # использовать контекст
        'progress': LocalizationString(
            '📉 С начала ты уже похудел(а) на {weight_change:.1f} кг ({percentage:.1f}% от начального веса)'),
        'change': LocalizationString(
            '📈 С начала ты уже набрал(а) {weight_change:.1f} кг ({percentage:.1f}% от начального веса)'),
        'goal_remaining': LocalizationString('🎯 До целевого веса осталось: {remaining:.1f} кг (цель: {target} кг)'),
        'goal_percentage': LocalizationString('\n📊 Ты выполнил(а) {percentage:.1f}% своей цели!\n\n'),
        'keep_tracking': LocalizationString('Продолжай отслеживать прогресс регулярно! 💪'),
    },

    # Сообщения для воды
    'water': {
        'recorded': LocalizationString(
            '💧 Отлично! Я записал потребление воды: {amount} стаканов (~{ml_amount} мл)',
            plural_forms={
                'one': '💧 Отлично! Я записал потребление воды: {amount} стакан (~{ml_amount} мл)',
                'few': '💧 Отлично! Я записал потребление воды: {amount} стакана (~{ml_amount} мл)',
                'many': '💧 Отлично! Я записал потребление воды: {amount} стаканов (~{ml_amount} мл)'
            }
        ),
        'daily_total': LocalizationString('\nСегодня ты выпил(а) всего: {current_intake} мл\n'),
        'goal_percentage': LocalizationString('Это {percentage:.1f}% от дневной цели в {goal} мл\n\n'),
        'motivation': LocalizationString(
            'Продолжай в том же духе! Регулярное потребление воды помогает контролировать голод и улучшает общее самочувствие.'),
    },

    # Сообщения для соблюдения диеты
    'compliance': {
        'followed': LocalizationString('✅ Отлично! {meal_type} выполнен по плану.'),
        'partially': LocalizationString('⚠️ Хорошо! {meal_type} частично выполнен по плану.'),
        'substituted': LocalizationString('🔄 Понятно! {meal_type} заменен на другое блюдо.'),
        'skipped': LocalizationString('❌ Отмечено! {meal_type} пропущен.'),
        'generic_status': LocalizationString('Записан статус для приема пищи: {meal_type}.'),
        'overall_score': LocalizationString('\n\nОбщее соблюдение плана на сегодня: {score:.1f}%'),
        'excellent': LocalizationString('\n\n👍 Отличная работа! Продолжай в том же духе.'),
        'good': LocalizationString('\n\n👍 Хороший результат! Старайся следовать плану.'),
        'keep_trying': LocalizationString('\n\n💪 Не сдавайся! Каждый день - это новая возможность.'),
    },

    # Сообщения для статистики
    'stats': {
        'header': LocalizationString('*📊 СТАТИСТИКА И ПРОГРЕСС*\n\n'),
        'weight_section': LocalizationString('*⚖️ Прогресс по весу:*\n'),
        'weight_initial': LocalizationString('• Начальный вес: {weight} кг\n'),
        'weight_current': LocalizationString('• Текущий вес: {weight} кг\n'),
        'weight_target': LocalizationString('• Целевой вес: {weight} кг\n\n'),
        'weight_change_negative': LocalizationString('• Изменение: -{change:.1f} кг 👍\n'),
        'weight_change_positive': LocalizationString('• Изменение: +{change:.1f} кг\n'),
        'weight_change_neutral': LocalizationString('• Изменение: 0 кг (вес стабилен)\n'),
        'weight_goal_remaining': LocalizationString('• Осталось до цели: {remaining:.1f} кг\n'),
        'weight_goal_percentage': LocalizationString('• Процент выполнения: {percentage:.1f}%\n\n'),
        'water_section': LocalizationString('*💧 Потребление воды сегодня:*\n'),
        'water_consumed': LocalizationString('• Выпито: {intake} мл\n'),
        'water_goal': LocalizationString('• Цель: {goal} мл\n'),
        'water_percentage': LocalizationString('• Выполнено: {percentage:.1f}%\n\n'),
        'compliance_section': LocalizationString('*🍽️ Соблюдение плана питания:*\n'),
        'compliance_overall': LocalizationString('\nОбщее соблюдение: {score:.1f}%\n\n'),
        'motivation': LocalizationString('💪 *Продолжай в том же духе!* Ты на пути к своей цели.'),
        'weekly_report_header': LocalizationString('📊 *Еженедельный отчет о прогрессе для {user_name}*\n\n'),
        'weight_no_data': LocalizationString('⚖️ *Вес:* Нет данных за последнюю неделю\n'),
        'water_days_tracked': LocalizationString('• Дней отслеживания: {days}/7\n'),
        'water_average': LocalizationString('• Среднее потребление: {avg:.1f} л/день\n'),
        'water_excellent': LocalizationString('• Статус: Отлично! Ты достигаешь целевого потребления воды 👍\n'),
        'water_good': LocalizationString('• Статус: Хорошо, но можно увеличить потребление воды\n'),
        'water_insufficient': LocalizationString('• Статус: Недостаточное потребление воды, старайся пить больше\n'),
        'water_no_data': LocalizationString('💧 *Потребление воды:* Нет данных за последнюю неделю\n'),
        'goal_section': LocalizationString('🎯 *Прогресс к цели:*\n'),
        'goal_target': LocalizationString('• Целевой вес: {target} кг\n'),
        'goal_remaining': LocalizationString('• Осталось: {remaining:.1f} кг\n'),
        'goal_percentage': LocalizationString('• Прогресс: {percentage:.1f}% выполнено\n'),
        'report_error': LocalizationString('Еженедельный отчет недоступен. Пожалуйста, попробуйте позже.'),
    },
}

# Создаем модуль локализации
module = LocalizationModule(strings)