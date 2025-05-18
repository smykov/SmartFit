from app.localization.base import LocalizationString, LocalizationModule

# Общие строки
strings = {
    'plan_not_found': LocalizationString('План диеты не найден'),
    # Полный план диеты
    'full': {
        'created': LocalizationString(
            '🎉 Твой план питания готов! Я подобрал блюда с учетом твоих параметров и предпочтений. Просмотри план и дай мне знать, если хочешь что-то изменить.'),
        'updating': LocalizationString(
            'Я корректирую твой план питания согласно запросу. Это займет несколько секунд.'),
        'update_failed': LocalizationString(
            'Извини, не удалось обновить план питания. Попробуй позже.'),
        'no_plan': LocalizationString(
            'У тебя пока нет активного плана питания. Напиши "диета" для создания нового плана.'),
        'creating_error': LocalizationString(
            'Ошибка при создании плана питания. Попробуйте позже.'),
        'no_updates': LocalizationString(
            'Изменения в план питания не были внесены.'),
        'recovery_generation': LocalizationString("Извините за задержку. Мы продолжаем генерацию вашего плана питания. Он будет готов в ближайшее время."),
        'summary': {
            'header': LocalizationString(
                '*📋 ПЕРСОНАЛЬНЫЙ ПЛАН ПИТАНИЯ*\n\n'),
            'deficit': LocalizationString(
                '🔥 *Расчетный дефицит калорий:* \n{deficit}\n\n'),
            'proficit': LocalizationString(
                '🔥 *Расчетный профицит калорий:* \n{proficit}\n\n'),
            'recommendations': LocalizationString(
                '📝 *Общие рекомендации:* \n{recommendations}\n\n'),
            'price': LocalizationString(
                '💰 *Примерная стоимость:* \n{price} {currency} в неделю\n\n'),
            'day_menu_example': LocalizationString(
                '📅 *Пример меню на {day_name}, {date_formatted}:*\n'),
            'meal_format': LocalizationString(
                '{emoji} *{meal_type}*: \n{title} {relevance}\n'),
            'calories_format': LocalizationString(
                '  Калории: {calories} ккал\n'),
            'why_recommended': LocalizationString(
                '  _Почему рекомендуем: {why_recommended}_\n')
        },

        'plan': {
            'header': LocalizationString('🗓️ ПЛАН ПИТАНИЯ НА НЕДЕЛЮ\n\n'),
            'day_header': LocalizationString('📆 *{day_name}, {date_formatted}*\n\n'),
            'total_calories': LocalizationString('🔥 Всего калорий: *{calories} ккал*\n'),
            'macro_ratio': LocalizationString('📊 Соотношение БЖУ: *{ratio}*\n'),
            'macros': LocalizationString('🥩 Белки: *{proteins}г* | 🧀 Жиры: *{fats}г* | 🍚 Углеводы: *{carbs}г*\n'),
            'meal_header': LocalizationString('{emoji} *{meal_type}*: {title}\n'),
            'nutrient_info': LocalizationString(
                'Пищевая ценность: {calories} ккал | Б:{proteins}г Ж:{fats}г У:{carbs}г\n'),
            'why_recommended': LocalizationString('💡 Почему рекомендуем:_ {why_recommended} _\n'),
            'day_tip': LocalizationString('\n💎 *Совет дня:* {tip}\n'),
            'price': LocalizationString(
                '💰 Примерная стоимость: {price} {currency}\n'),
            'commands_message': LocalizationString(
                '''*📱 Команды для взаимодействия с планом:*
    - Напишите 'полный план' для просмотра плана на всю неделю
    - Напишите 'план на сегодня' или 'меню на сегодня' для детального плана на сегодня
    - Напишите 'список покупок' для получения списка продуктов
    - Напишите 'выполнено/частично/заменил/пропустил завтрак/обед/ужин/перекус' для отметки о соблюдении плана
    ''')
        }
    },

    'short': {
        'created': LocalizationString(
            '🎉 Твой план питания готов! Я подобрал блюда с учетом твоих параметров и предпочтений. Просмотри план и дай мне знать, если хочешь что-то изменить.'),
        'creating_error': LocalizationString(
            'Ошибка при создании краткого плана питания. Пожалуйста, попробуйте позже.'),
        'updating': LocalizationString(
            'Я корректирую твой план питания согласно запросу. Это займет еще несколько секунд...'),
        'next_step': {
            'header': LocalizationString(
                '*👆 Это краткая версия плана. В полной версии будут:*\n'),
            'recipes': LocalizationString(
                '• Подробные рецепты и инструкции по приготовлению\n'),
            'nutrition': LocalizationString(
                '• Информация о питательных веществах для каждого блюда\n'),
            'explanations': LocalizationString(
                '• Объяснения, почему каждое блюдо рекомендовано именно вам\n'),
            'shopping': LocalizationString(
                '• Список покупок с учетом того, что у вас уже есть\n\n'),
            'invalid_version': LocalizationString(
                'План не является краткой версией'),
        },
        'summary': {
            'header': LocalizationString('План питания'),
            'info': LocalizationString('Ваш план питания на неделю:'),
            'weekday': LocalizationString('\n\n*{weekday_name}*\n'),
            'total_calories': LocalizationString('Общая калорийность: *{calories} ккал*\n'),
            'meal_format': LocalizationString('{emoji} *{meal_type}*: {title}'),
            'meal_calories': LocalizationString(' (*{calories} ккал*)')
        },
        'approved': LocalizationString('Подтверждено, генерируем полную версию плана...'),
        'approval_error': LocalizationString('Произошла ошибка при обработке подтверждения'),
        'conformation': LocalizationString(
            'Вам подходит этот план питания? Напишите "да", если устраивает, или опишите, что нужно изменить.')

    },

    # План на день
    'day': {
        'header': LocalizationString(
            '🗓️ МЕНЮ НА {day_name}, {date_formatted}:\n\n'),
        'total_calories': LocalizationString(
            '🔥 Всего калорий: {calories} ккал\n'),
        'macro_ratio': LocalizationString(
            '📊 Соотношение макронутриентов: {ratio}\n'),
        'macros': LocalizationString(
            '🥩 Белки: {proteins}г | 🧀 Жиры: {fats}г | 🍚 Углеводы: {carbs}г\n'),
        'nutrient_info': LocalizationString(
            '🔥 Пищевая ценность: {calories} ккал | Б:{proteins}г Ж:{fats}г У:{carbs}г\n'),
        'meal_header': LocalizationString(
            '🍽️ {emoji} *{meal_type}*: *{title}* {relevance}\n\n'),
        'ingredients_header': LocalizationString(
            '📋 *Ингредиенты:*\n'),
        'ingredient_format': LocalizationString(
            '• {name}: {quantity} {unit}\n'),
        'nutrition_header': LocalizationString(
            '\n📊 *Пищевая ценность:*\n'),
        'calories': LocalizationString(
            '• Калории: {calories} ккал\n'),
        'proteins': LocalizationString(
            '• Белки: {proteins} г\n'),
        'fats': LocalizationString(
            '• Жиры: {fats} г\n'),
        'carbs': LocalizationString(
            '• Углеводы: {carbs} г\n'),
        'fiber': LocalizationString(
            '• Клетчатка: {fiber} г\n'),
        'vitamins': LocalizationString(
            '• Витамины: {vitamins}\n'),
        'minerals': LocalizationString(
            '• Минералы: {minerals}\n'),
        'why_recommended': LocalizationString(
            '\n💡 *Почему рекомендуется:* {why_recommended}\n'),
        'preparation_header': LocalizationString(
            '\n👨‍🍳 *Приготовление:* {preparation}\n'),
        'tip': LocalizationString(
            '\n💎 *Совет на сегодня:* {tip}\n'),
        'creating_error': LocalizationString(
            'Ошибка при создании плана питания на день. Пожалуйста, попробуйте позже.'),
        'no_plan': LocalizationString(
            'К сожалению, на указанную дату нет плана питания.'),
        'price': LocalizationString(
            '💰 Примерная стоимость: {price} {currency}\n'),
        'tracking': {
            'header': LocalizationString(
                '*📱 Отметьте выполнение плана:*\n'),
            'followed': LocalizationString(
                '• Напишите \'выполнено завтрак/обед/ужин/перекус\' для отметки о соблюдении\n'),
            'partially': LocalizationString(
                '• Напишите \'частично завтрак/обед/ужин/перекус\' если следовали плану частично\n'),
            'substituted': LocalizationString(
                '• Напишите \'заменил завтрак/обед/ужин/перекус\' если заменили блюдо\n'),
            'skipped': LocalizationString(
                '• Напишите \'пропустил завтрак/обед/ужин/перекус\' если пропустили прием пищи\n'),
            'number_hint': LocalizationString('''\nСовет: Вы можете использовать цифры для быстрой отметки:
1 - выполнено
2 - частично 
3 - заменил
4 - пропустил

Например: "1 завтрак" или "2 обед"\n\n
Или просто описать прием пищи своими словами со списком блюд, также можете это сделать в конце дня за весь день сразу.'''),        }
    },
# TODO сделать сообщение о том, что не забыть написать отчет о приемах пищи отдельно покаждому в течении дня или в конце дня итогом за день вместо информации по командам. Также в напоминаниях это указать.
    'update': {
        'success_header': LocalizationString(
            '✅ *План питания обновлен*\n\n{comment}\n'),
        'day_updated_with_date': LocalizationString(
            '\nОбновлено меню на *{day_name}, {date_formatted}*'),
        'day_updated': LocalizationString(
            '\nОбновлено меню на *{day_name}*'),
        'unknown_day_updated': LocalizationString(
            '\nОбновлено меню на {date_str}'),
        'formatting_error': LocalizationString(
            'Ошибка при форматировании сообщения об обновлении диеты. Пожалуйста, попробуйте снова.'),
        'no_updates': LocalizationString(
            'План питания не был обновлен. Пожалуйста, уточните, что именно вы хотите изменить.'),
        'default_comment': LocalizationString(
            'План питания обновлен согласно запросу'),
        'parsing_error': LocalizationString(
            'Не удалось обработать ответ ИИ'),
        'invalid_format': LocalizationString(
            'Некорректный формат ответа от ИИ'),
        'update_failed': LocalizationString(
            'Не удалось обновить план питания'),
    },

    'ai': {
        'user_not_found': LocalizationString(
            'Извините, не удалось найти информацию о пользователе.'),
        'processing_error': LocalizationString(
            'Извините, произошла ошибка при обработке вашего вопроса. Пожалуйста, попробуйте позже.'),
    }
}

# Создаем модуль локализации
module = LocalizationModule(strings)
