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


class ProductCategory(Enum):
    """Категории продуктов для списка покупок"""
    FRUITS_VEGETABLES = "Фрукты и овощи"
    MEAT_FISH = "Мясо и рыба"
    DAIRY = "Молочные продукты"
    BREAD_CEREALS = "Хлеб и крупы"
    SPICES = "Специи и приправы"
    DRINKS = "Напитки"
    OTHER = "Другое"
