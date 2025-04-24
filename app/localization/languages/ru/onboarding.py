from app.localization.base import LocalizationString, LocalizationModule

# Строки для модуля онбординга
strings = {
    # Приветствие и базовые сообщения онбординга
    'welcome': LocalizationString(
        '👋 Привет! Добро пожаловать в SmartFit - твой персональный ассистент для похудения. Я помогу тебе создать план питания, адаптированный под тебя, учитывая местные продукты и твой бюджет.'),

    'name': {
        'request': LocalizationString('Как тебя зовут?'),
        'example': LocalizationString('Например: Иван')
    },

    'age': {
        'request': LocalizationString('Сколько тебе лет?'),
        'example': LocalizationString('Например: 30')
    },

    'gender': {
        'request': LocalizationString("""Какой у тебя пол?
1. Мужской
2. Женский
3. Другой

Ответь номером или напиши своими словами:"""),
        'example': LocalizationString('Например: 1 или мужской'),
        'male': LocalizationString('мужской'),
        'female': LocalizationString('женский'),
        'other': LocalizationString('другой'),
        'male_short': LocalizationString('муж'),
        'female_short': LocalizationString('жен')
    },

    'height': {
        'request': LocalizationString('Какой у тебя рост в сантиметрах?'),
        'example': LocalizationString('Например: 175')
    },

    'weight': {
        'current_request': LocalizationString('Какой у тебя текущий вес в килограммах?'),
        'current_example': LocalizationString('Например: 80'),
        'target_request': LocalizationString('Какой вес ты хочешь достичь (в килограммах)?'),
        'target_example': LocalizationString('Например: 70'),
        'goal_determined_lose': LocalizationString(
            'На основе твоего текущего и целевого веса, я вижу, что твоя цель - похудеть. Я создам план диеты соответственно.'),
        'goal_determined_gain': LocalizationString(
            'На основе твоего текущего и целевого веса, я вижу, что твоя цель - набрать вес. Я создам план диеты соответственно.'),
        'goal_determined_maintain': LocalizationString(
            'Я вижу, что ты хочешь поддерживать свой текущий вес. Я настрою план питания соответствующим образом.')
    },

    'activity_level': {
        'request': LocalizationString("""Оцени свой уровень физической активности:
1. Сидячий образ жизни (мало или совсем нет физических нагрузок)
2. Легкая активность (легкие упражнения 1-3 раза в неделю)
3. Умеренная активность (умеренные упражнения 3-5 раз в неделю)
4. Высокая активность (интенсивные тренировки 6-7 раз в неделю)
5. Очень высокая активность (физическая работа или 2 тренировки в день)

Ответь номером или напиши своими словами:"""),
        'example': LocalizationString('Например: 3 или "умеренная активность"'),
        'sedentary': LocalizationString('сидячий'),
        'light': LocalizationString('легкая'),
        'moderate': LocalizationString('умеренная'),
        'high': LocalizationString('высокая'),
        'very_high': LocalizationString('очень высокая')
    },

    'weight_goal': {
        'request': LocalizationString("""Какая у тебя цель по весу?
1. Похудеть
2. Поддерживать текущий вес
3. Набрать вес

Ответь номером или напиши своими словами:"""),
        'example': LocalizationString('Например: 1 или "похудеть"'),
        'lose': LocalizationString('похудеть'),
        'maintain': LocalizationString('поддерживать'),
        'gain': LocalizationString('набрать')
    },

    'diet_preference': {
        'request': LocalizationString("""Какие у тебя предпочтения в питании?
1. Обычная диета (без ограничений)
2. Вегетарианская (без мяса, но с яйцами и молочными продуктами)
3. Веганская (только растительная пища)
4. Низкоуглеводная (ограничение углеводов)
5. Кето (высокое содержание жиров, очень низкое содержание углеводов)
6. Безглютеновая (без пшеницы, ржи и ячменя)

Ответь номером или напиши своими словами:"""),
        'example': LocalizationString('Например: 1 или "обычная"'),
        'regular': LocalizationString('обычная'),
        'vegetarian': LocalizationString('вегетарианская'),
        'vegan': LocalizationString('веганская'),
        'low_carb': LocalizationString('низкоуглеводная'),
        'keto': LocalizationString('кето'),
        'gluten_free': LocalizationString('безглютеновая')
    },

    'allergies': {
        'request': LocalizationString('Есть ли у тебя пищевые аллергии? Перечисли через запятую или напиши "нет":'),
        'example': LocalizationString('Например: "орехи, молочные продукты" или "нет"')
    },

    'disliked_products': {
        'request': LocalizationString(
            'Есть ли продукты, которые ты не любишь или не хочешь включать в диету? Перечисли через запятую или напиши "нет":'),
        'example': LocalizationString('Например: "грибы, болгарский перец" или "нет"')
    },

    'budget': {
        'request': LocalizationString('Какой у тебя недельный бюджет на продукты питания (в рублях)?'),
        'example': LocalizationString('Например: 5000 или "неограниченный"'),
        'unlimited': LocalizationString('неограничен'),
        'no_limit': LocalizationString('без ограничений'),
        'any': LocalizationString('любой')
    },
    # TODO доделать на род по полу пользователя
    'completed': LocalizationString(
        '🎉 Поздравляю! Ты завершил(а) настройку. Теперь ты можешь использовать команды, такие как "план", "статистика", "вес XX", "вода X", чтобы взаимодействовать с SmartFit.'),

    'invalid_input': LocalizationString(
        'Извини, я не смог понять твой ввод. Пожалуйста, попробуй еще раз.\n\n{step_message}'),

    'answers': {
        'yes': LocalizationString('да'),
        'no': LocalizationString('нет'),
        'none': LocalizationString('отсутствуют'),
        'no_have': LocalizationString('не имею')
    }
}

# Создаем модуль локализации
module = LocalizationModule(strings)
