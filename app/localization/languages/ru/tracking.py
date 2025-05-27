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
        'weekly_average': LocalizationString(
            '📊 Средний показатель: {avg_ml} мл/день за последние {days} дней\n'),
    },

    # Сообщения для соблюдения диеты
    'compliance': {
        'followed': LocalizationString('✅ Отлично! {meal_type} выполнен по плану.'),
        'partially': LocalizationString('⚠️ Хорошо! {meal_type} частично выполнен по плану.'),
        'substituted': LocalizationString('🔄 {meal_type} заменен на другое блюдо.'),
        'skipped': LocalizationString('❌ {meal_type} пропущен.'),
        'generic_status': LocalizationString('Записан статус для приема пищи: {meal_type}.'),
        'overall_score': LocalizationString('Общее соблюдение плана на сегодня: {score:.1f}%'),
        'score_components': LocalizationString(
            'Компоненты оценки: выполнение {status_score}%, нутриенты {nutrients_score}%'),
        'excellent': LocalizationString('👍 Отличная работа! Продолжай в том же духе.'),
        'good': LocalizationString('👍 Хороший результат! Старайся следовать плану.'),
        'keep_trying': LocalizationString('💪 Не сдавайся! Каждый день - это новая возможность.'),

        # ключи для информации о калориях
        'calories_info': LocalizationString('Принято {calories} ккал'),
        'excess': LocalizationString('превышение +{percent}%'),
        'deficit': LocalizationString('недобор -{percent}%'),
        'on_target': LocalizationString('в пределах нормы'),

        # Ключи для рекомендаций по калориям
        'calories_exceeded_significantly': LocalizationString(
            '⚠️ Вы употребили на {percent}% больше калорий, чем рекомендовано ({actual} вместо {planned} ккал). Рекомендуем уменьшить порции в следующих приемах пищи сегодня.'),
        'calories_exceeded_slightly': LocalizationString(
            'ℹ️ Вы употребили немного больше калорий, чем рекомендовано ({actual} вместо {planned} ккал). Это в пределах нормы, но следите за общим количеством калорий в течение дня.'),
        'calories_on_target': LocalizationString(
            '✅ Отличная работа! Калорийность соответствует плану ({actual} из {planned} ккал).'),
        'calories_under': LocalizationString(
            'ℹ️ Вы употребили на {percent}% меньше калорий, чем рекомендовано ({actual} вместо {planned} ккал). Для достижения ваших целей важно потреблять достаточное количество пищи.'),
        # Ключи для истории трекинга
        "daily_progress": LocalizationString(
            "📊 Прогресс за день: {consumed_calories}/{planned_calories} ккал ({progress_percentage}%). Осталось: {remaining_calories} ккал"),
        "calories_exceeded_today": LocalizationString(
            "⚠️ Превышение калорий за день: +{excess_calories} ккал. Рекомендую облегчить оставшиеся приемы пищи"),
        "calories_remaining_today": LocalizationString(
            "✅ Осталось до цели: {remaining_calories} ккал, {remaining_proteins}г белков, {remaining_fats}г жиров, {remaining_carbs}г углеводов"),
        "completed_meals_today": LocalizationString("✅ Выполненные приемы пищи: {completed_meals}"),
        "reduce_next_meals": LocalizationString(
            "💡 Рекомендую уменьшить порции следующих приемов ({next_meals}) на {reduction_percent}%"),
        "slightly_reduce_next_meals": LocalizationString(
            "💡 Слегка уменьшите порции в: {next_meals} (на {reduction_percent}%)"),
        "increase_next_meals": LocalizationString(
            "💡 Можете увеличить порции в: {next_meals} (+{additional_calories} ккал)"),
        "suggest_diet_update_reduce": LocalizationString(
            "💬 Для корректировки напишите: 'измени {meal_type} - меньше калорий'"),
        "suggest_diet_update_increase": LocalizationString(
            "💬 Для корректировки напишите: 'измени {meal_type} - больше калорий'"),

        # Ключи для макронутриентов
        'proteins': LocalizationString('Белки'),
        'fats': LocalizationString('Жиры'),
        'carbs': LocalizationString('Углеводы'),
        'macros_imbalance': LocalizationString(
            '⚖️ Обратите внимание на баланс БЖУ: {imbalances}. Для оптимальных результатов старайтесь придерживаться рекомендованного соотношения макронутриентов.')
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
        'water_section_today': LocalizationString('*💧 Потребление воды сегодня:*\n'),
        'water_section_period': LocalizationString('💧 Потребление воды за период:\n'),
        'water_consumed': LocalizationString('• Выпито: {intake} мл\n'),
        'water_goal': LocalizationString('• Цель: {goal} мл\n'),
        'water_percentage': LocalizationString('• Выполнено: {percentage:.1f}%\n\n'),
        'compliance_section': LocalizationString('*🍽️ Соблюдение плана питания:*\n'),
        'compliance_overall': LocalizationString('\nОбщее соблюдение: {score:.1f}%\n\n'),
        'score_components_average': LocalizationString(
            'Средние показатели: выполнение {status_score}%, нутриенты {nutrients_score}%'),
        'motivation': LocalizationString('💪 *Продолжай в том же духе!* Ты на пути к своей цели.'),
        'weekly_report_header': LocalizationString('📊 *Еженедельный отчет о прогрессе для {user_name}*\n\n'),
        'weight_no_data': LocalizationString('⚖️ *Вес:* Нет данных за последнюю неделю\n'),
        'water_days_tracked': LocalizationString('Дней отслеживания: {days}/7\n'),
        'water_average': LocalizationString('Среднее потребление: {avg:.1f} л/день\n'),
        'water_excellent': LocalizationString('Статус: Отлично! Ты достигаешь целевого потребления воды 👍\n'),
        'water_good': LocalizationString('Статус: Хорошо, но можно увеличить потребление воды\n'),
        'water_insufficient': LocalizationString('Статус: Недостаточное потребление воды, старайся пить больше\n'),
        'water_no_data': LocalizationString('💧 *Потребление воды:* Нет данных за последнюю неделю\n'),
        'goal_section': LocalizationString('🎯 *Прогресс к цели:*\n'),
        'goal_target': LocalizationString('• Целевой вес: {target} кг\n'),
        'goal_remaining': LocalizationString('• Осталось: {remaining:.1f} кг\n'),
        'goal_percentage': LocalizationString('• Прогресс: {percentage:.1f}% выполнено\n'),
        'report_error': LocalizationString('Еженедельный отчет недоступен. Пожалуйста, попробуйте позже.'),

        'compliance_report_header': LocalizationString('*📊 Отчет о соблюдении плана за {date_range}*\n'),
        'no_compliance_data': LocalizationString('За этот период нет данных о соблюдении плана.'),
        'overall_adherence': LocalizationString('Общий процент соблюдения плана: {score}%'),
        'calorie_adherence': LocalizationString('📈 Соблюдение по калориям:'),
        'planned_calories': LocalizationString('Запланировано: {calories} ккал'),
        'consumed_calories': LocalizationString('Фактически: {calories} ккал'),
        'adherence_percentage': LocalizationString('Соответствие: {percent}%'),
        'macros_adherence': LocalizationString('📊 Соблюдение по макронутриентам:'),
        'protein_adherence': LocalizationString('Белки: {percent}% от плана'),
        'fat_adherence': LocalizationString('Жиры: {percent}% от плана'),
        'carb_adherence': LocalizationString('Углеводы: {percent}% от плана'),
        'recommendations': LocalizationString('💡 Рекомендации:'),
        'low_calorie_recommendation': LocalizationString(
            'Старайтесь придерживаться рекомендованной калорийности. Недостаточное потребление калорий может замедлить метаболизм и снизить эффективность диеты.'),
        'high_calorie_recommendation': LocalizationString(
            'Для достижения ваших целей важно контролировать общее потребление калорий. Попробуйте уменьшить размеры порций или выбирать менее калорийные продукты.'),
        'low_protein_recommendation': LocalizationString(
            'Увеличьте потребление белка для поддержания мышечной массы и лучшего контроля аппетита. Хорошие источники: мясо, рыба, яйца, бобовые, творог.'),
        'high_protein_recommendation': LocalizationString(
            'Вы потребляете больше белка, чем рекомендовано. Для большинства людей достаточно 1.6-2.2 г белка на кг веса.'),
        'high_fat_recommendation': LocalizationString(
            'Обратите внимание на потребление жиров. Отдавайте предпочтение полезным ненасыщенным жирам из орехов, авокадо и оливкового масла вместо насыщенных.'),
        'high_carb_recommendation': LocalizationString(
            'Для лучшего контроля веса попробуйте уменьшить потребление простых углеводов (сахар, белый хлеб, сладости) в пользу сложных (овощи, цельнозерновые продукты).'),
        'low_carb_recommendation': LocalizationString(
            'Умеренное потребление углеводов важно для энергии и нормального функционирования организма. Добавьте в рацион больше сложных углеводов - фруктов, овощей, круп.'),
        'high_score_motivation': LocalizationString(
            '🌟 Отличная работа! Вы очень близки к своей цели. Продолжайте придерживаться плана, и вы обязательно достигнете желаемых результатов!'),
        'medium_score_motivation': LocalizationString(
            '👍 Вы на правильном пути! Небольшие корректировки в питании помогут вам приблизиться к оптимальному результату. Не останавливайтесь!'),
        'low_score_motivation': LocalizationString(
            '💪 Не расстраивайтесь! Каждый день - это новая возможность. Попробуйте составить более реалистичный план питания или постепенно адаптируйтесь к текущему.'),
        'last_week': LocalizationString('последнюю неделю'),
    },
}

# Создаем модуль локализации
module = LocalizationModule(strings)
