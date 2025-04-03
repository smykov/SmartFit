# app/localization/messages.py

from typing import Dict


class DietMessages:
    """Класс с локализованными сообщениями для работы с диетами"""

    # Общие сообщения
    NO_DIET_PLAN = "У тебя пока нет активного плана питания. Напиши 'диета' для создания нового плана."
    PLAN_GENERATION_STARTED = "🥗 Я начинаю создавать для вас краткую версию персонализированного плана питания на неделю. Это займет несколько минут."
    PLAN_GENERATION_DETAILS = "После того, как я покажу вам план, вы сможете согласовать его или запросить изменения. После согласования я подготовлю полную версию с подробными рецептами и списком покупок."
    PLAN_GENERATION_ERROR = "К сожалению, не удалось создать план диеты. Пожалуйста, попробуйте позже или обратитесь в поддержку."
    FULL_PLAN_CREATED = "🎉 Полная версия вашего плана питания готова! Вы можете посмотреть детальную информацию о каждом дне, рецепты и сформировать список покупок."
    FULL_PLAN_ERROR = "К сожалению, произошла ошибка при создании полной версии плана. Пожалуйста, попробуйте позже или обратитесь в поддержку."
    PLAN_APPROVED = "✅ Отлично! Я начинаю готовить для вас полную версию плана питания с подробными рецептами и списком покупок. Это займет несколько минут."

    # Сообщения для списка покупок
    SHOPPING_LIST_GENERATION = "🛒 Начинаю формирование списка покупок на основе вашего плана питания. Это займет несколько секунд..."
    SHOPPING_LIST_ERROR = "Извините, не удалось создать список покупок. Попробуйте позже."
    NO_SHOPPING_LIST = "Для твоего плана ещё не создан список покупок. Напиши 'список покупок' для его создания."
    PRODUCT_MARKED = "✅ Отлично! Я отметил '{product}' как купленный."
    PRODUCT_NOT_FOUND = "Я не нашел '{product}' в твоем списке покупок. Проверь название продукта или напиши 'список покупок' для просмотра полного списка."

    # Сообщения для обновления плана
    UPDATING_PLAN = "Я корректирую твой план питания согласно запросу. Это займет несколько секунд."
    UPDATE_SUCCESS = "✅ *План питания обновлен*\n\n{comment}\n"
    UPDATE_FAILED = "К сожалению, не удалось обновить план питания. Попробуй позже."
    NO_UPDATES = "Извините, не удалось внести изменения в план. Пожалуйста, попробуйте более конкретное указание, например: 'Замени обед в понедельник на курицу'."

    # Шаблоны форматирования
    FULL_DIET_HEADER = "*📋 ПЕРСОНАЛЬНЫЙ ПЛАН ПИТАНИЯ*\n\n"
    CALORIC_DEFICIT = "🔥 *Расчетный дефицит калорий:* \n{deficit}\n\n"
    CALORIC_PROFICIT = "🔥 *Расчетный профицит калорий:* \n{proficit}\n\n"
    GENERAL_RECOMMENDATIONS = "📝 *Общие рекомендации:* \n{recommendations}\n\n"
    ESTIMATED_PRICE = "💰 *Примерная стоимость:* \n{price} кетцалей в неделю\n\n"
    DAY_MENU_EXAMPLE = "📅 *Пример меню на {day_name}, {date_formatted}:*\n"
    MEAL_FORMAT = "{emoji} *{meal_type}*: \n{title} {relevance}\n"
    CALORIES_FORMAT = "  Калории: {calories} ккал\n"
    WHY_RECOMMENDED = "  Почему рекомендуем: {why_recommended}_\n"

    # Форматы даты и названия дней недели
    DAY_FORMAT = "%d.%m.%Y"

    # Словарь дней недели
    @staticmethod
    def get_weekday_names() -> Dict[str, str]:
        return {
            "monday": "Понедельник",
            "tuesday": "Вторник",
            "wednesday": "Среда",
            "thursday": "Четверг",
            "friday": "Пятница",
            "saturday": "Суббота",
            "sunday": "Воскресенье"
        }

    # Словарь типов приема пищи
    @staticmethod
    def get_meal_types() -> Dict[str, str]:
        return {
            "breakfast": "Завтрак",
            "lunch": "Обед",
            "dinner": "Ужин",
            "snack": "Перекус"
        }

    # Эмодзи для приемов пищи
    @staticmethod
    def get_meal_emojis() -> Dict[str, str]:
        return {
            "breakfast": "🍳",
            "lunch": "🍲",
            "dinner": "🍽️",
            "snack": "🥪"
        }

    # Форматы для списка покупок
    SHOPPING_LIST_HEADER = "*🛒 СПИСОК ПОКУПОК*\n\n"
    CATEGORY_FORMAT = "*{category}:*\n"
    ITEM_FORMAT = "• {item}\n"
    TOTAL_PRICE = "*Общая стоимость:* ~{price} кетцалей\n\n"
    SHOPPING_INSTRUCTIONS = "Отправьте 'купил [название продукта]' чтобы отметить покупку.\n"

    @staticmethod
    def get_diet_commands_message() -> str:
        """
        Возвращает сообщение с командами для взаимодействия с планом диеты

        Returns:
            str: Сообщение с командами
        """
        return """*📱 Команды для взаимодействия с планом:*
    - Напиши 'полный план' для просмотра плана на всю неделю
    - Напиши 'план на сегодня' или 'меню на сегодня' для детального плана на сегодня
    - Напиши 'список покупок' для получения списка продуктов
    - Напиши 'выполнено/частично/заменил/пропустил завтрак/обед/ужин/перекус' для отметки о соблюдении плана
    """

    @staticmethod
    def get_plan_approval_prompt() -> str:
        """
        Возвращает текст для запроса на согласование плана диеты

        Returns:
            str: Текст запроса
        """
        return """
    👆 Это краткая версия вашего персонализированного плана питания на неделю.
    
    Пожалуйста, подтвердите план или запросите изменения:
    - Напишите "согласен", "ок" или "да", чтобы подтвердить план
    - Или укажите, что именно вы хотели бы изменить, например:
      "Замени обед во вторник"
      "Не хочу рыбу в понедельник"
      "Больше белка в завтраках"
    
    После вашего подтверждения я подготовлю полную версию плана с подробными рецептами и списком покупок!
    """

    # константы для DietFormatter
    SHORT_DIET_HEADER = "*📋 ПЛАН ПИТАНИЯ НА НЕДЕЛЮ (краткая версия)*\n\n"
    SHORT_DIET_INFO = "Это краткая версия плана для согласования. После вашего подтверждения я подготовлю полную версию с подробными рецептами и списком покупок.\n\n"
    SHORT_DIET_WEEKDAY = "*📅 {weekday_name}*\n"
    SHORT_DIET_TOTAL_CALORIES = "Всего калорий: {calories} ккал\n"
    SHORT_DIET_MEAL_FORMAT = "{emoji} *{meal_type}*: {title}"
    SHORT_DIET_MEAL_CALORIES = " ({calories} ккал)"
    SHORT_DIET_NEXT_STEPS_HEADER = "*👆 Это краткая версия плана. В полной версии будут:*\n"
    SHORT_DIET_NEXT_STEPS_RECIPES = "• Подробные рецепты и инструкции по приготовлению\n"
    SHORT_DIET_NEXT_STEPS_NUTRITION = "• Информация о питательных веществах для каждого блюда\n"
    SHORT_DIET_NEXT_STEPS_EXPLANATIONS = "• Объяснения, почему каждое блюдо рекомендовано именно вам\n"
    SHORT_DIET_NEXT_STEPS_SHOPPING = "• Список покупок с учетом того, что у вас уже есть\n\n"
    SHORT_DIET_CONFIRMATION = "Пожалуйста, подтвердите план или запросите изменения."

    FULL_PLAN_HEADER = "*📋 ПОЛНЫЙ ПЛАН ПИТАНИЯ НА НЕДЕЛЮ*\n\n"
    FULL_PLAN_DAY_HEADER = "*📅 {day_name}, {date_formatted}*\n"
    FULL_PLAN_TOTAL_CALORIES = "Всего калорий: {calories} ккал\n"
    FULL_PLAN_MACRO_RATIO = "Соотношение БЖУ: {ratio}\n"
    FULL_PLAN_MACROS = "Белки: {proteins}г, Жиры: {fats}г, Углеводы: {carbs}г\n"
    FULL_PLAN_MEAL_HEADER = "{emoji} *{meal_type}*: {title} {relevance}\n"
    FULL_PLAN_NUTRIENT_INFO = "  {nutrients}\n"
    FULL_PLAN_WHY_RECOMMENDED = "  _Почему: {why_recommended}_\n"
    FULL_PLAN_DAY_TIP = "💡 *Совет дня:* {tip}\n"

    DAY_PLAN_HEADER = "*📅 ПЛАН ПИТАНИЯ НА {day_name}, {date_formatted}*\n\n"
    DAY_PLAN_TOTAL_CALORIES = "*Всего калорий:* {calories} ккал\n"
    DAY_PLAN_MACRO_RATIO = "*Соотношение БЖУ:* {ratio}\n"
    DAY_PLAN_MACROS = "*Макронутриенты:* Белки: {proteins}г, Жиры: {fats}г, Углеводы: {carbs}г\n"
    DAY_PLAN_MEAL_HEADER = "{emoji} *{meal_type}*: {title} {relevance}\n"
    DAY_PLAN_INGREDIENTS_HEADER = "  *Ингредиенты:*\n"
    DAY_PLAN_INGREDIENT_FORMAT = "  • {name}: {quantity} {unit}\n"
    DAY_PLAN_NUTRITION_HEADER = "  *Пищевая ценность:*\n"
    DAY_PLAN_CALORIES = "  • Калории: {calories} ккал\n"
    DAY_PLAN_PROTEINS = "  • Белки: {proteins}г\n"
    DAY_PLAN_FATS = "  • Жиры: {fats}г\n"
    DAY_PLAN_CARBS = "  • Углеводы: {carbs}г\n"
    DAY_PLAN_FIBER = "  • Клетчатка: {fiber}г\n"
    DAY_PLAN_WHY_RECOMMENDED_HEADER = "  *Почему рекомендуем:*\n  _{why_recommended}_\n"
    DAY_PLAN_PREPARATION_HEADER = "  *Способ приготовления:*\n  {preparation}\n"
    DAY_PLAN_TIP = "💡 *Совет дня:* {tip}\n\n"
    DAY_PLAN_TRACKING_HEADER = "*📱 Отметьте выполнение плана:*\n"
    DAY_PLAN_TRACKING_FOLLOWED = "• Напишите 'выполнено завтрак/обед/ужин/перекус' для отметки о соблюдении\n"
    DAY_PLAN_TRACKING_PARTIALLY = "• Напишите 'частично завтрак/обед/ужин/перекус' если следовали плану частично\n"
    DAY_PLAN_TRACKING_SUBSTITUTED = "• Напишите 'заменил завтрак/обед/ужин/перекус' если заменили блюдо\n"
    DAY_PLAN_TRACKING_SKIPPED = "• Напишите 'пропустил завтрак/обед/ужин/перекус' если пропустили прием пищи\n"

    ERROR_CREATE_DIET_SUMMARY = "План питания создан. Напишите 'план' для получения подробной информации."
    ERROR_CREATE_SHORT_DIET_SUMMARY = "План питания создан. Пожалуйста, подтвердите его или запросите изменения."
    ERROR_CREATE_FULL_DIET_PLAN = "Ошибка при создании полного плана питания. Попробуйте позже."
    ERROR_CREATE_DAY_DIET_PLAN = "Ошибка при создании плана питания на день. Попробуйте позже."
    ERROR_FORMAT_SHOPPING_LIST = "Ошибка при форматировании списка покупок. Попробуйте позже."
    NO_PLAN_FOR_DAY = "К сожалению, на указанную дату нет плана питания."
