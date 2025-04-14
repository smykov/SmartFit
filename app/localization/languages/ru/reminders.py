from app.localization.base import LocalizationString, LocalizationModule

# Строки для напоминаний
strings = {
    'greeting': LocalizationString('👋 Привет'),
    'type.onboarding': LocalizationString('onboarding'),
    'type.weight': LocalizationString('weight'),
    'type.water': LocalizationString('water'),
    'type.breakfast': LocalizationString('breakfast'),
    'type.lunch': LocalizationString('lunch'),
    'type.dinner': LocalizationString('dinner'),
    'type.weekly_report': LocalizationString('weekly_report'),
    'type.plan_approval': LocalizationString('plan_approval'),

    'weight': LocalizationString(
        '⚖️ Привет! Не забудь записать свой вес сегодня. Это поможет отслеживать прогресс. Просто напиши \'вес XX\', где XX - твой вес в килограммах.\n\n📊 Чтобы увидеть полный прогресс, напиши \'статистика\' или \'прогресс\'.'),
    'water': LocalizationString(
        '💧 Не забывай пить воду! Отправь \'вода X\', где X - количество стаканов, которые ты выпил(а).\n\n📊 Чтобы увидеть полную статистику, напиши \'статистика\'.'),
    'breakfast': LocalizationString('🍳 Доброе утро! Не забудь отметить свой завтрак сегодня.'),
    'lunch': LocalizationString('🍲 Время обеда! Не забудь отметить свой обед сегодня.'),
    'dinner': LocalizationString('🍽️ Добрый вечер! Не забудь отметить свой ужин сегодня.'),

    'plan_approval.initial': LocalizationString(
        '👋 Напоминаем, что у тебя есть план питания, ожидающий твоего одобрения. Хочешь просмотреть его сейчас?'),
    'plan_approval.same_day': LocalizationString(
        '👋 У тебя всё ещё есть план питания, ожидающий твоего одобрения с сегодняшнего дня. Хочешь просмотреть его сейчас?'),
    'plan_approval.days': LocalizationString(
        '👋 У тебя есть план питания, который ожидает твоего одобрения уже {days} дней. Хочешь просмотреть его сейчас?'),

    'onboarding.name': LocalizationString(
        'Нам нужно твоё имя для продолжения настройки. Пожалуйста, сообщи, как к тебе обращаться.'),
    'onboarding.basic_info': LocalizationString(
        'Давай продолжим настройку. Нам нужна некоторая основная информация о тебе для создания персонализированного плана питания.'),
    'onboarding.weight_info': LocalizationString(
        'Нам нужна информация о твоем весе для настройки плана питания. Давай продолжим с того места, где мы остановились.'),
    'onboarding.almost_complete': LocalizationString(
        'Ты почти закончил(а) настройку! Осталось всего несколько вопросов для завершения твоего профиля.'),
    'onboarding.default': LocalizationString(
        'Давай продолжим регистрацию для создания твоего персонализированного плана питания.'),
}

# Создаем модуль локализации
module = LocalizationModule(strings)