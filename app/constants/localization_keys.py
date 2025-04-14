# app/constants/localization_keys.py
from enum import Enum


class LocalizationKeys:
    """Константы для ключей локализации"""

    class User:
        """Ключи локализации для пользователей"""
        NOT_FOUND = "user.not_found"

    class Common:
        """Общие ключи локализации"""
        WEEKDAY_NAMES = "common.weekday_names.{}"
        MEAL_TYPES = "common.meal_types.{}"
        MEAL_EMOJIS = "common.meal_emojis.{}"
        DAY_FORMAT = "diet.common.day_format"
        HELP_COMMANDS_LIST = "help_commands_list"

    class Diet:
        """Ключи локализации для диет"""

        class Update:
            """Ключи локализации для обновления плана диеты"""
            SUCCESS_HEADER = "diet.update.success_header"
            DAY_UPDATED_WITH_DATE = "diet.update.day_updated_with_date"
            DAY_UPDATED = "diet.update.day_updated"
            UNKNOWN_DAY_UPDATED = "diet.update.unknown_day_updated"
            FORMATTING_ERROR = "diet.update.formatting_error"
            NO_UPDATES = "diet.update.no_updates"
            DEFAULT_COMMENT = "diet.update.default_comment"
            PARSING_ERROR = "diet.update.parsing_error"
            INVALID_FORMAT = "diet.update.invalid_format"
            UPDATE_FAILED = "diet.update.update_failed"

        class AI:
            """Ключи для ИИ-ответов на вопросы о питании"""
            USER_NOT_FOUND = "diet.ai.user_not_found"
            PROCESSING_ERROR = "diet.ai.processing_error"

        class Full:
            """Ключи для полной версии диеты"""

            class Summary:
                """Ключи для сводки полного плана"""
                HEADER = "diet.full.summary.header"
                DEFICIT = "diet.full.summary.deficit"
                PROFICIT = "diet.full.summary.proficit"
                RECOMMENDATIONS = "diet.full.summary.recommendations"
                PRICE = "diet.full.summary.price"
                DAY_MENU_EXAMPLE = "diet.full.summary.day_menu_example"
                MEAL_FORMAT = "diet.full.summary.meal_format"
                CALORIES_FORMAT = "diet.full.summary.calories_format"
                WHY_RECOMMENDED = "diet.full.summary.why_recommended"

            class Plan:
                """Ключи для полного плана"""
                HEADER = "diet.full.plan.header"
                DAY_HEADER = "diet.full.plan.day_header"
                TOTAL_CALORIES = "diet.full.plan.total_calories"
                MACRO_RATIO = "diet.full.plan.macro_ratio"
                MACROS = "diet.full.plan.macros"
                MEAL_HEADER = "diet.full.plan.meal_header"
                NUTRIENT_INFO = "diet.full.plan.nutrient_info"
                WHY_RECOMMENDED = "diet.full.plan.why_recommended"
                DAY_TIP = "diet.full.plan.day_tip"
                COMMANDS_MESSAGE = "diet.full.plan.commands_message"

            # Сообщения статуса
            CREATED = "diet.full.created"
            UPDATING = "diet.full.updating"
            UPDATE_FAILED = "diet.full.update_failed"
            NO_PLAN = "diet.full.no_plan"
            CREATING_ERROR = "diet.full.creating_error"
            NO_UPDATES = "diet.full.no_updates"

        class Short:
            """Ключи для краткой версии диеты"""

            class Summary:
                """Ключи для сводки краткого плана"""
                HEADER = "diet.short.summary.header"
                INFO = "diet.short.summary.info"
                WEEKDAY = "diet.short.summary.weekday"
                TOTAL_CALORIES = "diet.short.summary.total_calories"
                MEAL_FORMAT = "diet.short.summary.meal_format"
                MEAL_CALORIES = "diet.short.summary.meal_calories"

            class NextStep:
                """Ключи для следующих шагов"""
                HEADER = "diet.short.next_step.header"
                RECIPES = "diet.short.next_step.recipes"
                NUTRITION = "diet.short.next_step.nutrition"
                EXPLANATIONS = "diet.short.next_step.explanations"
                SHOPPING = "diet.short.next_step.shopping"

            # Сообщения статуса и подтверждения
            CREATED = "diet.short.created"
            UPDATING = "diet.short.updating"
            UPDATE_FAILED = "diet.short.update_failed"
            NO_PLAN = "diet.short.no_plan"
            CREATING_ERROR = "diet.short.creating_error"
            APPROVAL_SUCCESS = "diet.short.approval_success"
            APPROVAL_ERROR = "diet.short.approval_error"
            DISAPPROVAL = "diet.short.disapproval"
            CONFORMATION = "diet.short.conformation"
            INVALID_VERSION = "diet.short.invalid_version"

        class Day:
            """Ключи для плана на день"""
            HEADER = "diet.day.header"
            TOTAL_CALORIES = "diet.day.total_calories"
            MACRO_RATIO = "diet.day.macro_ratio"
            MACROS = "diet.day.macros"
            MEAL_HEADER = "diet.day.meal_header"
            INGREDIENTS_HEADER = "diet.day.ingredients_header"
            INGREDIENT_FORMAT = "diet.day.ingredient_format"
            NUTRITION_HEADER = "diet.day.nutrition_header"
            CALORIES = "diet.day.calories"
            PROTEINS = "diet.day.proteins"
            FATS = "diet.day.fats"
            CARBS = "diet.day.carbs"
            FIBER = "diet.day.fiber"
            WHY_RECOMMENDED_HEADER = "diet.day.why_recommended_header"
            PREPARATION_HEADER = "diet.day.preparation_header"
            TIP = "diet.day.tip"

            class Tracking:
                """Ключи для трекинга плана"""
                HEADER = "diet.day.tracking.header"
                FOLLOWED = "diet.day.tracking.followed"
                PARTIALLY = "diet.day.tracking.partially"
                SUBSTITUTED = "diet.day.tracking.substituted"
                SKIPPED = "diet.day.tracking.skipped"

            # Сообщения статуса
            NO_PLAN = "diet.day.no_plan"
            CREATING_ERROR = "diet.day.creating_error"

    class Shopping:
        """Ключи для списка покупок"""
        HEADER = "shopping.header"
        ITEMS_COUNT = "diet.shopping.items_count"
        CATEGORY_FORMAT = "shopping.category_format"
        CATEGORY_WITH_COUNT_FORMAT = "diet.shopping.category_with_count_format"
        SHOPPING_PROGRESS = "diet.shopping.shopping_progress"
        ITEM_FORMAT = "shopping.item_format"
        ITEM_INFO_FORMAT = "shopping.item_info_format"  # Новый ключ
        PRICE_FORMAT = "shopping.price_format"  # Новый ключ
        PURCHASED_ITEM_FORMAT = "shopping.purchased_item_format"  # Новый ключ
        TOTAL_PRICE = "shopping.total_price"
        INSTRUCTIONS = "shopping.instructions"
        GENERATING = "shopping.generating"
        ERROR = "shopping.error"
        FORMATTING_ERROR = "shopping.formatting_error"
        PRODUCT_MARKED = "shopping.product_marked"
        PRODUCT_NOT_FOUND = "shopping.product_not_found"
        NO_LIST = "shopping.no_list"
        DIET_PLAN_NOT_FOUND = "shopping.diet_plan_not_found"
        PARSING_ERROR = "shopping.parsing_error"
        SAVE_FAILED = "shopping.save_failed"
        GENERATING_ERROR = "shopping.generating_error"
        MARKING_ERROR = "shopping.marking_error"
        NO_DIET_PLAN = "shopping.no_diet_plan"

    class Onboarding:
        """Ключи для онбординга"""
        WELCOME = "onboarding.welcome"
        NAME_REQUEST = "onboarding.nameRequest"
        NAME_REQUEST_EXAMPLE = "onboarding.nameRequestExample"
        AGE_REQUEST = "onboarding.ageRequest"
        AGE_REQUEST_EXAMPLE = "onboarding.ageRequestExample"
        GENDER_REQUEST = "onboarding.genderRequest"
        GENDER_REQUEST_EXAMPLE = "onboarding.genderRequestExample"
        HEIGHT_REQUEST = "onboarding.heightRequest"
        HEIGHT_REQUEST_EXAMPLE = "onboarding.heightRequestExample"
        CURRENT_WEIGHT_REQUEST = "onboarding.currentWeightRequest"
        CURRENT_WEIGHT_REQUEST_EXAMPLE = "onboarding.currentWeightRequestExample"
        TARGET_WEIGHT_REQUEST = "onboarding.targetWeightRequest"
        TARGET_WEIGHT_REQUEST_EXAMPLE = "onboarding.targetWeightRequestExample"
        ACTIVITY_LEVEL_REQUEST = "onboarding.activityLevelRequest"
        ACTIVITY_LEVEL_REQUEST_EXAMPLE = "onboarding.activityLevelRequestExample"
        WEIGHT_GOAL_REQUEST = "onboarding.weightGoalRequest"
        WEIGHT_GOAL_REQUEST_EXAMPLE = "onboarding.weightGoalRequestExample"
        DIET_PREFERENCE_REQUEST = "onboarding.dietPreferenceRequest"
        DIET_PREFERENCE_REQUEST_EXAMPLE = "onboarding.dietPreferenceRequestExample"
        ALLERGIES_REQUEST = "onboarding.allergiesRequest"
        ALLERGIES_REQUEST_EXAMPLE = "onboarding.allergiesRequestExample"
        DISLIKED_PRODUCTS_REQUEST = "onboarding.dislikedProductsRequest"
        DISLIKED_PRODUCTS_REQUEST_EXAMPLE = "onboarding.dislikedProductsRequestExample"
        BUDGET_REQUEST = "onboarding.budgetRequest"
        BUDGET_REQUEST_EXAMPLE = "onboarding.budgetRequestExample"
        COMPLETED = "onboarding.completed"
        INVALID_INPUT = "onboarding.invalidInput"
        WEIGHT_GOAL_DETERMINED_LOSE = "onboarding.weightGoalDeterminedLose"
        WEIGHT_GOAL_DETERMINED_GAIN = "onboarding.weightGoalDeterminedGain"
        WEIGHT_GOAL_DETERMINED_MAINTAIN = "onboarding.weightGoalDeterminedMaintain"

        class Answers:
            YES = "onboarding.answers.yes"
            NO = "onboarding.answers.no"
            NONE = "onboarding.answers.none"
            NO_HAVE = "onboarding.answers.no_have"

        class Gender:
            MALE = "onboarding.gender.male"
            FEMALE = "onboarding.gender.female"
            OTHER = "onboarding.gender.other"
            MALE_SHORT = "onboarding.gender.male_short"
            FEMALE_SHORT = "onboarding.gender.female_short"

        class ActivityLevel:
            SEDENTARY = "onboarding.activity_level.sedentary"
            LIGHT = "onboarding.activity_level.light"
            MODERATE = "onboarding.activity_level.moderate"
            HIGH = "onboarding.activity_level.high"
            VERY_HIGH = "onboarding.activity_level.very_high"

        class WeightGoal:
            LOSE = "onboarding.weight_goal.lose"
            MAINTAIN = "onboarding.weight_goal.maintain"
            GAIN = "onboarding.weight_goal.gain"

        class DietPreference:
            REGULAR = "onboarding.diet_preference.regular"
            VEGETARIAN = "onboarding.diet_preference.vegetarian"
            VEGAN = "onboarding.diet_preference.vegan"
            LOW_CARB = "onboarding.diet_preference.low_carb"
            KETO = "onboarding.diet_preference.keto"
            GLUTEN_FREE = "onboarding.diet_preference.gluten_free"

        class Budget:
            UNLIMITED = "onboarding.budget.unlimited"
            NO_LIMIT = "onboarding.budget.no_limit"
            ANY = "onboarding.budget.any"

    class Commands:
        """Ключи для команд"""

        class General:
            COMMAND_NOT_FOUND = "commands.general.commandNotFound"
            EXECUTION_ERROR = "commands.general.executionError"
            UNKNOWN_COMMAND = "commands.general.unknownCommand"
            PREREQUISITES_NOT_MET = "commands.general.prerequisitesNotMet"

        class Weight:
            RECORDED = "commands.weight.recorded"
            INVALID_FORMAT = "commands.weight.invalidFormat"
            OUT_OF_RANGE = "commands.weight.outOfRange"
            INVALID_VALUE = "commands.weight.invalidValue"
            ERROR = "commands.weight.error"

        class Water:
            RECORDED = "commands.water.recorded"
            INVALID_FORMAT = "commands.water.invalidFormat"
            OUT_OF_RANGE = "commands.water.outOfRange"
            INVALID_VALUE = "commands.water.invalidValue"
            ERROR = "commands.water.error"

        class Help:
            HELP_TEXT = "commands.help.helpText"

        class Diet:
            DIET_GENERATION_STARTED = "commands.diet.generationStarted"
            DIET_GENERATION_DETAILS = "commands.diet.generationDetails"
            NO_DIET_PLAN = "commands.diet.noDietPlan"
            NO_DIET_FOR_TODAY = "commands.diet.noDietForToday"
            ERROR = "commands.diet.error"

        class ShoppingList:
            GENERATING = "commands.shoppingList.generating"
            ERROR = "commands.shoppingList.error"
            INVALID_PRODUCT_FORMAT = "commands.shoppingList.invalidProductFormat"
            PRODUCT_MARKED = "commands.shoppingList.productMarked"
            PRODUCT_NOT_FOUND = "commands.shoppingList.productNotFound"
            NO_DIET_PLAN = "commands.shoppingList.noDietPlan"

        class Stats:
            ERROR = "commands.stats.error"

        class Compliance:
            INVALID_FORMAT = "commands.compliance.invalidFormat"
            INVALID_TYPE = "commands.compliance.invalidType"
            INVALID_MEAL_TYPE = "commands.compliance.invalidMealType"
            NO_DIET_PLAN = "commands.compliance.noDietPlan"
            RECORD_ERROR = "commands.compliance.recordError"
            RECORDED = "commands.compliance.recorded"

        class Language:
            LANGUAGES_LIST = "commands.language.languagesList"
            UNSUPPORTED_LANGUAGE = "commands.language.unsupportedLanguage"
            UNAVAILABLE_SERVICE = "commands.language.unavailableService"
            LANGUAGE_CHANGED = "commands.language.languageChanged"

    class Messaging:
        """Ключи для сообщений процессора сообщений"""
        DELAYED_MESSAGE = "messaging.delayedMassage"
        INVALID_MESSAGE_FORMAT = "messaging.invalidMessageFormat"
        WELCOME_NEW_USER = "messaging.welcomeNewUser"
        MESSAGE_ALREADY_PROCESSED = "messaging.messageAlreadyProcessed"

    class Tracking:
        """Ключи для трекинга"""

        class Weight:
            """Ключи для сообщений о весе"""
            RECORDED = "tracking.weight.recorded"
            PROGRESS = "tracking.weight.progress"
            WEIGHT_CHANGE = "tracking.weight.change"
            GOAL_REMAINING = "tracking.weight.goal_remaining"
            GOAL_PERCENTAGE = "tracking.weight.goal_percentage"
            KEEP_TRACKING = "tracking.weight.keep_tracking"

        class Water:
            """Ключи для сообщений о воде"""
            RECORDED = "tracking.water.recorded"
            DAILY_TOTAL = "tracking.water.daily_total"
            GOAL_PERCENTAGE = "tracking.water.goal_percentage"
            MOTIVATION = "tracking.water.motivation"

        class Compliance:
            """Ключи для сообщений о соблюдении диеты"""
            FOLLOWED = "tracking.compliance.followed"
            PARTIALLY = "tracking.compliance.partially"
            SUBSTITUTED = "tracking.compliance.substituted"
            SKIPPED = "tracking.compliance.skipped"
            GENERIC_STATUS = "tracking.compliance.generic_status"
            OVERALL_SCORE = "tracking.compliance.overall_score"
            EXCELLENT = "tracking.compliance.excellent"
            GOOD = "tracking.compliance.good"
            KEEP_TRYING = "tracking.compliance.keep_trying"

        class Stats:
            """Ключи для статистики трекинга"""
            HEADER = "tracking.stats.header"
            WEIGHT_SECTION = "tracking.stats.weight_section"
            WEIGHT_INITIAL = "tracking.stats.weight_initial"
            WEIGHT_CURRENT = "tracking.stats.weight_current"
            WEIGHT_TARGET = "tracking.stats.weight_target"
            WEIGHT_CHANGE_NEGATIVE = "tracking.stats.weight_change_negative"
            WEIGHT_CHANGE_POSITIVE = "tracking.stats.weight_change_positive"
            WEIGHT_CHANGE_NEUTRAL = "tracking.stats.weight_change_neutral"
            WEIGHT_GOAL_REMAINING = "tracking.stats.weight_goal_remaining"
            WEIGHT_GOAL_PERCENTAGE = "tracking.stats.weight_goal_percentage"
            WATER_SECTION = "tracking.stats.water_section"
            WATER_CONSUMED = "tracking.stats.water_consumed"
            WATER_GOAL = "tracking.stats.water_goal"
            WATER_PERCENTAGE = "tracking.stats.water_percentage"
            COMPLIANCE_SECTION = "tracking.stats.compliance_section"
            COMPLIANCE_OVERALL = "tracking.stats.compliance_overall"
            MOTIVATION = "tracking.stats.motivation"
            WEEKLY_REPORT_HEADER = "tracking.stats.weekly_report_header"
            WEIGHT_NO_DATA = "tracking.stats.weight_no_data"
            WATER_DAYS_TRACKED = "tracking.stats.water_days_tracked"
            WATER_AVERAGE = "tracking.stats.water_average"
            WATER_EXCELLENT = "tracking.stats.water_excellent"
            WATER_GOOD = "tracking.stats.water_good"
            WATER_INSUFFICIENT = "tracking.stats.water_insufficient"
            WATER_NO_DATA = "tracking.stats.water_no_data"
            GOAL_SECTION = "tracking.stats.goal_section"
            GOAL_TARGET = "tracking.stats.goal_target"
            GOAL_REMAINING = "tracking.stats.goal_remaining"
            GOAL_PERCENTAGE = "tracking.stats.goal_percentage"
            REPORT_ERROR = "tracking.stats.report_error"

    class Reminders:
        """Ключи для напоминаний"""
        GREETING = "reminders.greeting"
        REMINDER_TYPE_ONBOARDING = "reminders.type.onboarding"
        REMINDER_TYPE_WEIGHT = "reminders.type.weight"
        REMINDER_TYPE_WATER = "reminders.type.water"
        REMINDER_TYPE_BREAKFAST = "reminders.type.breakfast"
        REMINDER_TYPE_LUNCH = "reminders.type.lunch"
        REMINDER_TYPE_DINNER = "reminders.type.dinner"
        REMINDER_TYPE_WEEKLY_REPORT = "reminders.type.weekly_report"
        REMINDER_TYPE_PLAN_APPROVAL = "reminders.type.plan_approval"

        WEIGHT_REMINDER = "reminders.weight"
        WATER_REMINDER = "reminders.water"
        BREAKFAST_REMINDER = "reminders.breakfast"
        LUNCH_REMINDER = "reminders.lunch"
        DINNER_REMINDER = "reminders.dinner"

        PLAN_APPROVAL_REMINDER_INITIAL = "reminders.plan_approval.initial"
        PLAN_APPROVAL_REMINDER_SAME_DAY = "reminders.plan_approval.same_day"
        PLAN_APPROVAL_REMINDER_DAYS = "reminders.plan_approval.days"

        class Onboarding:
            """Ключи для напоминаний онбординга"""
            NAME = "reminders.onboarding.name"
            BASIC_INFO = "reminders.onboarding.basic_info"
            WEIGHT_INFO = "reminders.onboarding.weight_info"
            ALMOST_COMPLETE = "reminders.onboarding.almost_complete"
            DEFAULT = "reminders.onboarding.default"

    class Errors:
        """Ключи локализации для ошибок"""
        GENERAL_ERROR = "errors.general"
        NUTRITION_QUESTION_ERROR = "errors.nutrition_question"


class ProductCategory(Enum):
    """Категории продуктов для списка покупок"""
    FRUITS_VEGETABLES = "Фрукты и овощи"
    MEAT_FISH = "Мясо и рыба"
    DAIRY = "Молочные продукты"
    BREAD_CEREALS = "Хлеб и крупы"
    SPICES = "Специи и приправы"
    DRINKS = "Напитки"
    OTHER = "Другое"
