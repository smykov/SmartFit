from app.localization.base import LocalizationString, LocalizationModule

# Общие строки
strings = {
    'plan_not_found': LocalizationString('План диеты не найден'),
    'plan_approved': LocalizationString('Подтверждено, генерируем полную версию плана...'),
    'plan_approval_error': LocalizationString('Произошла ошибка при обработке подтверждения'),
    'full': {
        'created': LocalizationString(
            '🎉 Твой план питания готов! Я подобрал блюда с учетом твоих параметров и предпочтений. Просмотри план и дай мне знать, если хочешь что-то изменить.'),
        'updating': LocalizationString(
            'Я корректирую твой план питания согласно запросу. Это займет несколько секунд.'),
        'update_failed': LocalizationString('Извини, не удалось обновить план питания. Попробуй позже.'),
        'no_plan': LocalizationString(
            'У тебя пока нет активного плана питания. Напиши "диета" для создания нового плана.'),
        'creating_error': LocalizationString('Ошибка при создании плана питания. Попробуйте позже.'),
        'no_updates': LocalizationString('Изменения в план питания не были внесены.'),
        'summary': {
            'header': '*📋 ПЕРСОНАЛЬНЫЙ ПЛАН ПИТАНИЯ*\n\n',
            'deficit': '🔥 *Расчетный дефицит калорий:* \n{deficit}\n\n',
            'proficit': '🔥 *Расчетный профицит калорий:* \n{proficit}\n\n',
            'recommendations': '📝 *Общие рекомендации:* \n{recommendations}\n\n',
            'price': '💰 *Примерная стоимость:* \n{price} {currency} в неделю\n\n',
            'day_menu_example': '📅 *Пример меню на {day_name}, {date_formatted}:*\n',
            'meal_format': '{emoji} *{meal_type}*: \n{title} {relevance}\n',
            'calories_format': '  Калории: {calories} ккал\n',
            'why_recommended': '  _Почему рекомендуем: {why_recommended}_\n'
        },
        'plan': {
            'commands_message': '''*📱 Команды для взаимодействия с планом:*
    - Напишите 'полный план' для просмотра плана на всю неделю
    - Напишите 'план на сегодня' или 'меню на сегодня' для детального плана на сегодня
    - Напишите 'список покупок' для получения списка продуктов
    - Напишите 'выполнено/частично/заменил/пропустил завтрак/обед/ужин/перекус' для отметки о соблюдении плана
    '''
        }
    },
    'short': {
        'creating_error': 'Ошибка при создании краткого плана питания. Пожалуйста, попробуйте позже.',
        'next_step': {
            'header': '*👆 Это краткая версия плана. В полной версии будут:*\n',
            'recipes': '• Подробные рецепты и инструкции по приготовлению\n',
            'nutrition': '• Информация о питательных веществах для каждого блюда\n',
            'explanations': '• Объяснения, почему каждое блюдо рекомендовано именно вам\n',
            'shopping': '• Список покупок с учетом того, что у вас уже есть\n\n',
            'invalid_version': LocalizationString('План не является краткой версией'),
        }
    },
    'day': {
        'creating_error': 'Ошибка при создании плана питания на день. Пожалуйста, попробуйте позже.',
        'no_plan': 'К сожалению, на указанную дату нет плана питания.',
        'tracking': {
            'header': '*📱 Отметьте выполнение плана:*\n',
            'followed': '• Напишите \'выполнено завтрак/обед/ужин/перекус\' для отметки о соблюдении\n',
            'partially': '• Напишите \'частично завтрак/обед/ужин/перекус\' если следовали плану частично\n',
            'substituted': '• Напишите \'заменил завтрак/обед/ужин/перекус\' если заменили блюдо\n',
            'skipped': '• Напишите \'пропустил завтрак/обед/ужин/перекус\' если пропустили прием пищи\n'
        }
    },
    'update': {
        "success_header": LocalizationString("✅ *План питания обновлен*\n\n{comment}\n"),
        "day_updated_with_date": LocalizationString("\nОбновлено меню на *{day_name}, {date_formatted}*"),
        "day_updated": LocalizationString("\nОбновлено меню на *{day_name}*"),
        "unknown_day_updated": LocalizationString("\nОбновлено меню на {date_str}"),
        "formatting_error": LocalizationString(
            "Ошибка при форматировании сообщения об обновлении диеты. Пожалуйста, попробуйте снова."),
        "no_updates": LocalizationString(
            "План питания не был обновлен. Пожалуйста, уточните, что именно вы хотите изменить."),
        'default_comment': LocalizationString('План питания обновлен согласно запросу'),
        'parsing_error': LocalizationString('Не удалось обработать ответ ИИ'),
        'invalid_format': LocalizationString('Некорректный формат ответа от ИИ'),
        'update_failed': LocalizationString('Не удалось обновить план питания'),
    },
    'ai': {
        'ai.user_not_found': LocalizationString('Извините, не удалось найти информацию о пользователе.'),
        'ai.processing_error': LocalizationString(
            'Извините, произошла ошибка при обработке вашего вопроса. Пожалуйста, попробуйте позже.'),
    }
}
# Создаем модуль локализации
module = LocalizationModule(strings)
