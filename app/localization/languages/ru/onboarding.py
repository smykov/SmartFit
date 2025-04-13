# app/localization/languages/ru/onboarding.py
from app.localization.base import LocalizationString, LocalizationModule

# Строки для модуля онбординга
strings = {
    # Приветствие и базовые сообщения онбординга
    'welcome': LocalizationString(
        '👋 Привет! Добро пожаловать в GuateFit - твой персональный ассистент для похудения. Я помогу тебе создать план питания, адаптированный под тебя, учитывая местные продукты и твой бюджет.'),
    'nameRequest': LocalizationString('Как тебя зовут?'),
    'nameRequestExample': LocalizationString('Например: Иван'),
    'ageRequest': LocalizationString('Сколько тебе лет?'),
    'ageRequestExample': LocalizationString('Например: 30'),
    'genderRequest': LocalizationString('Какой у тебя пол? (мужской/женский/другой):'),
    'genderRequestExample': LocalizationString('Например: мужской'),
    'heightRequest': LocalizationString('Какой у тебя рост в сантиметрах?'),
    'heightRequestExample': LocalizationString('Например: 175'),
    'currentWeightRequest': LocalizationString('Какой у тебя текущий вес в килограммах?'),
    'currentWeightRequestExample': LocalizationString('Например: 80'),
    'targetWeightRequest': LocalizationString('Какой вес ты хочешь достичь (в килограммах)?'),
    'targetWeightRequestExample': LocalizationString('Например: 70'),
    'activityLevelRequest': LocalizationString("""Оцени свой уровень физической активности:
1. Сидячий образ жизни (мало или совсем нет физических нагрузок)
2. Легкая активность (легкие упражнения 1-3 раза в неделю)
3. Умеренная активность (умеренные упражнения 3-5 раз в неделю)
4. Высокая активность (интенсивные тренировки 6-7 раз в неделю)
5. Очень высокая активность (физическая работа или 2 тренировки в день)

Ответь номером или напиши своими словами:"""),
    'activityLevelRequestExample': LocalizationString('Например: 3 или "умеренная активность"'),
    'weightGoalRequest': LocalizationString("""Какая у тебя цель по весу?
1. Похудеть
2. Поддерживать текущий вес
3. Набрать вес

Ответь номером или напиши своими словами:"""),
    'weightGoalRequestExample': LocalizationString('Например: 1 или "похудеть"'),
    'dietPreferenceRequest': LocalizationString("""Какие у тебя предпочтения в питании?
1. Обычная диета (без ограничений)
2. Вегетарианская (без мяса, но с яйцами и молочными продуктами)
3. Веганская (только растительная пища)
4. Низкоуглеводная (ограничение углеводов)
5. Кето (высокое содержание жиров, очень низкое содержание углеводов)
6. Безглютеновая (без пшеницы, ржи и ячменя)

Ответь номером или напиши своими словами:"""),
    'dietPreferenceRequestExample': LocalizationString('Например: 1 или "обычная"'),
    'allergiesRequest': LocalizationString('Есть ли у тебя пищевые аллергии? Перечисли через запятую или напиши "нет":'),
    'allergiesRequestExample': LocalizationString('Например: "орехи, молочные продукты" или "нет"'),
    'dislikedProductsRequest': LocalizationString('Есть ли продукты, которые ты не любишь или не хочешь включать в диету? Перечисли через запятую или напиши "нет":'),
    'dislikedProductsRequestExample': LocalizationString('Например: "грибы, болгарский перец" или "нет"'),
    'budgetRequest': LocalizationString('Какой у тебя недельный бюджет на продукты питания (в кетцалях)?'),
    'budgetRequestExample': LocalizationString('Например: 500 или "неограниченный"'),
    'completed': LocalizationString('🎉 Поздравляю! Ты завершил(а) настройку. Теперь ты можешь использовать команды, такие как "план", "статистика", "вес XX", "вода X", чтобы взаимодействовать с GuateFit.'),
    'invalidInput': LocalizationString('Извини, я не смог понять твой ввод. Пожалуйста, попробуй еще раз.\n\n{step_message}'),
    'weightGoalDeterminedLose': LocalizationString('На основе твоего текущего и целевого веса, я вижу, что твоя цель - похудеть. Я создам план диеты соответственно.'),
    'weightGoalDeterminedGain': LocalizationString('На основе твоего текущего и целевого веса, я вижу, что твоя цель - набрать вес. Я создам план диеты соответственно.'),
    'weightGoalDeterminedMaintain': LocalizationString(
        'Я вижу, что ты хочешь поддерживать свой текущий вес. Я настрою план питания соответствующим образом.'),

    'answers.yes': LocalizationString('да'),
    'answers.no': LocalizationString('нет'),
    'answers.none': LocalizationString('отсутствуют'),
    'answers.no_have': LocalizationString('не имею'),

    'gender.male': LocalizationString('мужской'),
    'gender.female': LocalizationString('женский'),
    'gender.other': LocalizationString('другой'),
    'gender.male_short': LocalizationString('муж'),
    'gender.female_short': LocalizationString('жен'),

    'activity_level.sedentary': LocalizationString('сидячий'),
    'activity_level.light': LocalizationString('легкая'),
    'activity_level.moderate': LocalizationString('умеренная'),
    'activity_level.high': LocalizationString('высокая'),
    'activity_level.very_high': LocalizationString('очень высокая'),

    'weight_goal.lose': LocalizationString('похудеть'),
    'weight_goal.maintain': LocalizationString('поддерживать'),
    'weight_goal.gain': LocalizationString('набрать'),

    'diet_preference.regular': LocalizationString('обычная'),
    'diet_preference.vegetarian': LocalizationString('вегетарианская'),
    'diet_preference.vegan': LocalizationString('веганская'),
    'diet_preference.low_carb': LocalizationString('низкоуглеводная'),
    'diet_preference.keto': LocalizationString('кето'),
    'diet_preference.gluten_free': LocalizationString('безглютеновая'),

    'budget.unlimited': LocalizationString('неограничен'),
    'budget.no_limit': LocalizationString('без ограничений'),
    'budget.any': LocalizationString('любой'),
}

# Создаем модуль локализации
module = LocalizationModule(strings)