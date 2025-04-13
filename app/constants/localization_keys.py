# app/constants/localization_keys.py
from enum import Enum


class LocalizationKeys:
    """Константы для ключей локализации"""

    class Common:
        """Общие ключи локализации"""
        WEEKDAY_NAMES = "common.weekday_names.{}"
        MEAL_TYPES = "common.meal_types.{}"
        MEAL_EMOJIS = "common.meal_emojis.{}"
        DAY_FORMAT = "diet.common.day_format"
        HELP_COMMANDS_LIST = "help_commands_list"

    class Diet:
        """Ключи локализации для диет"""

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
        HEADER = "diet.shopping.header"
        CATEGORY_FORMAT = "diet.shopping.category_format"
        ITEM_FORMAT = "diet.shopping.item_format"
        TOTAL_PRICE = "diet.shopping.total_price"
        INSTRUCTIONS = "diet.shopping.instructions"
        GENERATING = "diet.shopping.generating"
        ERROR = "diet.shopping.error"
        FORMATTING_ERROR = "diet.shopping.formatting_error"
        PRODUCT_MARKED = "diet.shopping.product_marked"
        PRODUCT_NOT_FOUND = "diet.shopping.product_not_found"
        NO_LIST = "diet.shopping.no_list"

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


class ProductCategory(Enum):
    """Категории продуктов для списка покупок"""
    FRUITS_VEGETABLES = "Фрукты и овощи"
    MEAT_FISH = "Мясо и рыба"
    DAIRY = "Молочные продукты"
    BREAD_CEREALS = "Хлеб и крупы"
    SPICES = "Специи и приправы"
    DRINKS = "Напитки"
    OTHER = "Другое"
