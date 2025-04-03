# app/services/diet/diet_formatter.py

from datetime import datetime, date, timedelta
from typing import Dict, Any, List
import pytz

from app.localization.messages import DietMessages
from app.services.diet.base_service import BaseDietService
from app.templates.formatting_helpers import format_diet_message_for_whatsapp
from config import settings


class DietFormatter(BaseDietService):
    """Класс для форматирования планов диет и сообщений"""

    def __init__(self):
        """Инициализация форматтера диет"""
        super().__init__()
        self.messages = DietMessages()

    def get_diet_summary(self, diet_plan: Dict[str, Any]) -> tuple[str, str]:
        """
        Создает сводку плана диеты и отдельное сообщение с командами

        Args:
            diet_plan: План диеты

        Returns:
            Tuple[str, str]: (сводка плана, команды для взаимодействия)
        """
        commands_message = self.messages.get_diet_commands_message()

        try:
            # Получаем персонализированное обращение
            personalized_note = diet_plan.get("personalized_note", "")

            summary = self.messages.FULL_DIET_HEADER

            # Добавляем персонализированное обращение
            if personalized_note:
                summary += f"{personalized_note}\n\n"

            # Информация о калорийном дефиците
            if "caloric_deficit" in diet_plan and diet_plan["caloric_deficit"]:
                summary += self.messages.CALORIC_DEFICIT.format(deficit=diet_plan['caloric_deficit'])

            # Информация о калорийном профиците
            if "caloric_proficit" in diet_plan and diet_plan["caloric_proficit"]:
                summary += self.messages.CALORIC_PROFICIT.format(proficit=diet_plan['caloric_proficit'])

            # Общие рекомендации
            if "general_recommendations" in diet_plan and diet_plan["general_recommendations"]:
                summary += self.messages.GENERAL_RECOMMENDATIONS.format(
                    recommendations=diet_plan['general_recommendations']
                )

            # Информация о стоимости
            if "estimated_weekly_price" in diet_plan and diet_plan["estimated_weekly_price"]:
                summary += self.messages.ESTIMATED_PRICE.format(price=diet_plan['estimated_weekly_price'])

            # Примеры приемов пищи на сегодня или первый день
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date().isoformat()

            if "daily_plans" in diet_plan and diet_plan["daily_plans"]:
                # Используем сегодняшний день или первый доступный
                day_key = today if today in diet_plan["daily_plans"] else next(iter(diet_plan["daily_plans"]))
                day_plan = diet_plan["daily_plans"][day_key]

                # Получаем день недели и форматируем дату
                day_date = self.get_nearest_date_for_weekday(day_key)
                day_name = self.translate_day_name(day_date.strftime("%A"))
                date_formatted = day_date.strftime(self.messages.DAY_FORMAT)

                summary += self.messages.DAY_MENU_EXAMPLE.format(
                    day_name=day_name,
                    date_formatted=date_formatted
                )

                if "meals" in day_plan:
                    for meal in day_plan["meals"]:
                        meal_type = self.translate_meal_type(meal.get("type", ""))
                        title = meal.get("title", "")
                        calories = meal.get("calories", "")
                        relevance = self.get_relevance_stars(meal.get("relevance_score", 0))
                        emoji = self.create_meal_emoji(meal.get("type", ""))

                        summary += self.messages.MEAL_FORMAT.format(
                            emoji=emoji,
                            meal_type=meal_type,
                            title=title,
                            relevance=relevance
                        )

                        if calories:
                            summary += self.messages.CALORIES_FORMAT.format(calories=calories)

                        # Добавляем объяснение, почему блюдо рекомендовано
                        why_recommended = meal.get("why_recommended", "")
                        if why_recommended:
                            summary += self.messages.WHY_RECOMMENDED.format(why_recommended=why_recommended)

            return format_diet_message_for_whatsapp(summary), format_diet_message_for_whatsapp(commands_message)

        except Exception as e:
            self.logger.error(f"Error creating diet summary: {str(e)}")
            return format_diet_message_for_whatsapp(
                self.messages.ERROR_CREATE_DIET_SUMMARY), format_diet_message_for_whatsapp(
                commands_message)

    def get_short_diet_summary(self, diet_plan: Dict[str, Any]) -> str:
        """
        Создает сводку краткой версии плана диеты для согласования

        Args:
            diet_plan: План диеты

        Returns:
            str: Отформатированная сводка плана
        """
        try:
            summary = self.messages.SHORT_DIET_HEADER

            # Добавляем персонализированное обращение
            personalized_note = diet_plan.get("personalized_note", "")
            if personalized_note:
                summary += f"{personalized_note}\n\n"

            # Информация о плане
            summary += self.messages.SHORT_DIET_INFO

            # Формируем план по дням недели
            weekday_names = self.messages.get_weekday_names()

            if "daily_plans" in diet_plan:
                for weekday, day_plan in diet_plan["daily_plans"].items():
                    weekday_name = weekday_names.get(weekday, weekday.capitalize())
                    summary += self.messages.SHORT_DIET_WEEKDAY.format(weekday_name=weekday_name)

                    # Добавляем информацию о калориях
                    if "total_calories" in day_plan:
                        summary += self.messages.SHORT_DIET_TOTAL_CALORIES.format(
                            calories=day_plan['total_calories']
                        )

                    # Добавляем приемы пищи
                    if "meals" in day_plan:
                        for meal in day_plan["meals"]:
                            meal_type = self.translate_meal_type(meal.get("type", ""))
                            title = meal.get("title", "")
                            calories = meal.get("calories", "")
                            emoji = self.create_meal_emoji(meal.get("type", ""))

                            meal_text = self.messages.SHORT_DIET_MEAL_FORMAT.format(
                                emoji=emoji,
                                meal_type=meal_type,
                                title=title
                            )

                            if calories:
                                meal_text += self.messages.SHORT_DIET_MEAL_CALORIES.format(calories=calories)

                            summary += meal_text + "\n"

                    summary += "\n"

            # Добавляем информацию о следующих шагах
            summary += self.messages.SHORT_DIET_NEXT_STEPS_HEADER
            summary += self.messages.SHORT_DIET_NEXT_STEPS_RECIPES
            summary += self.messages.SHORT_DIET_NEXT_STEPS_NUTRITION
            summary += self.messages.SHORT_DIET_NEXT_STEPS_EXPLANATIONS
            summary += self.messages.SHORT_DIET_NEXT_STEPS_SHOPPING
            summary += self.messages.SHORT_DIET_CONFIRMATION

            return format_diet_message_for_whatsapp(summary)

        except Exception as e:
            self.logger.error(f"Error creating short diet summary: {str(e)}")
            return self.messages.ERROR_CREATE_SHORT_DIET_SUMMARY

    def get_full_diet_plan(self, diet_plan: Dict[str, Any]) -> List[str]:
        """
        Создает полный план диеты на все дни для отправки пользователю.
        Возвращает список сообщений из-за ограничений длины в WhatsApp.

        Args:
            diet_plan: План диеты

        Returns:
            List[str]: Список сообщений с планом диеты
        """
        try:
            messages = []

            # Получаем персонализированное обращение для первого сообщения
            intro_message = self.messages.FULL_PLAN_HEADER

            # Добавляем персонализированное обращение
            personalized_note = diet_plan.get("personalized_note", "")
            if personalized_note:
                intro_message += f"{personalized_note}\n\n"

            # Общие рекомендации
            if "general_recommendations" in diet_plan and diet_plan["general_recommendations"]:
                recommendations_format = self.messages.GENERAL_RECOMMENDATIONS.format(
                    recommendations=diet_plan["general_recommendations"])
                intro_message += recommendations_format

            # Информация о калорийном дефиците
            if "caloric_deficit" in diet_plan and diet_plan["caloric_deficit"]:
                deficit_format = self.messages.CALORIC_DEFICIT.format(deficit=diet_plan["caloric_deficit"])
                intro_message += deficit_format

            # Информация о калорийном профиците
            if "caloric_proficit" in diet_plan and diet_plan["caloric_proficit"]:
                proficit_format = self.messages.CALORIC_PROFICIT.format(proficit=diet_plan["caloric_proficit"])
                intro_message += proficit_format

            # Информация о стоимости
            if "estimated_weekly_price" in diet_plan and diet_plan["estimated_weekly_price"]:
                price_format = self.messages.ESTIMATED_PRICE.format(price=diet_plan["estimated_weekly_price"])
                intro_message += price_format

            messages.append(format_diet_message_for_whatsapp(intro_message))

            # Создаем отдельное сообщение для каждого дня
            if "daily_plans" in diet_plan and diet_plan["daily_plans"]:
                # Сортируем даты
                sorted_dates = sorted(diet_plan["daily_plans"].keys())

                for day_key in sorted_dates:
                    day_plan = diet_plan["daily_plans"][day_key]

                    # Это день недели, получаем ближайшую дату
                    day_date = self.get_nearest_date_for_weekday(day_key)
                    day_name = self.translate_day_name(day_date.strftime("%A"))
                    date_formatted = day_date.strftime(self.messages.DAY_FORMAT)

                    day_message = self.messages.FULL_PLAN_DAY_HEADER.format(
                        day_name=day_name,
                        date_formatted=date_formatted
                    )

                    # Добавляем информацию о калориях и макронутриентах
                    if "total_calories" in day_plan:
                        total_calories_format = self.messages.FULL_PLAN_TOTAL_CALORIES.format(
                            calories=day_plan['total_calories'])
                        day_message += total_calories_format

                    if "macros_ratio" in day_plan and day_plan["macros_ratio"]:
                        macro_ratio_format = self.messages.FULL_PLAN_MACRO_RATIO.format(ratio=day_plan['macros_ratio'])
                        day_message += macro_ratio_format
                    elif "total_proteins" in day_plan and "total_fats" in day_plan and "total_carbs" in day_plan:
                        macros_format = self.messages.FULL_PLAN_MACROS.format(proteins=day_plan['total_proteins'],
                                                                              fats=day_plan['total_fats'],
                                                                              carbs=day_plan['total_carbs'])
                        day_message += macros_format

                    day_message += "\n"

                    # Добавляем приемы пищи
                    if "meals" in day_plan:
                        for meal in day_plan["meals"]:
                            meal_type = self.translate_meal_type(meal.get("type", ""))
                            title = meal.get("title", "")
                            calories = meal.get("calories", "")
                            relevance = self.get_relevance_stars(meal.get("relevance_score", 0))
                            emoji = self.create_meal_emoji(meal.get("type", ""))

                            header_format = self.messages.FULL_PLAN_MEAL_HEADER.format(emoji=emoji, meal_type=meal_type,
                                                                                       title=title, relevance=relevance)
                            day_message += header_format

                            # Добавляем информацию о калориях и макронутриентах
                            nutrients_info = []
                            if calories:
                                nutrients_info.append(f"{calories} ккал")
                            if meal.get("proteins"):
                                nutrients_info.append(f"Б: {meal['proteins']}г")
                            if meal.get("fats"):
                                nutrients_info.append(f"Ж: {meal['fats']}г")
                            if meal.get("carbs"):
                                nutrients_info.append(f"У: {meal['carbs']}г")

                            if nutrients_info:
                                info_format = self.messages.FULL_PLAN_NUTRIENT_INFO.format(
                                    nutrients=", ".join(nutrients_info))
                                day_message += info_format

                            # Добавляем объяснение, почему блюдо рекомендовано
                            why_recommended = meal.get("why_recommended", "")
                            if why_recommended:
                                recommended_format = self.messages.FULL_PLAN_WHY_RECOMMENDED.format(
                                    why_recommended=why_recommended)
                                day_message += recommended_format

                            day_message += "\n"

                    # Добавляем советы на день, если они есть
                    if "tips" in day_plan and day_plan["tips"]:
                        tip_format = self.messages.FULL_PLAN_DAY_TIP.format(tip=day_plan['tips'])
                        day_message += tip_format

                    messages.append(format_diet_message_for_whatsapp(day_message))

            return messages

        except Exception as e:
            self.logger.error(f"Error creating full diet plan: {str(e)}")
            return [self.messages.ERROR_CREATE_FULL_DIET_PLAN]

    def get_day_diet_plan(self, diet_plan: Dict[str, Any], day_date: date = None) -> str:
        """
        Создает детальный план диеты на конкретный день

        Args:
            diet_plan: План диеты
            day_date: Дата, на которую нужен план (по умолчанию сегодня)

        Returns:
            str: Сообщение с планом на день
        """
        try:
            # Если дата не указана, используем сегодняшнюю
            if not day_date:
                day_date = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Преобразуем в строку
            day_key = self.get_day_of_week(day_date)

            # Проверяем, есть ли план на указанный день
            if "daily_plans" not in diet_plan or day_key not in diet_plan["daily_plans"]:
                return self.messages.NO_PLAN_FOR_DAY

            day_plan = diet_plan["daily_plans"][day_key]

            # Получаем день недели и форматируем дату
            day_name = self.translate_day_name(day_date.strftime("%A"))
            date_formatted = day_date.strftime(self.messages.DAY_FORMAT)

            message = self.messages.DAY_PLAN_HEADER.format(
                day_name=day_name.upper(),
                date_formatted=date_formatted
            )

            # Добавляем информацию о калориях и макронутриентах
            if "total_calories" in day_plan:
                message += self.messages.DAY_PLAN_TOTAL_CALORIES.format(
                    calories=day_plan['total_calories']
                )

            if "macros_ratio" in day_plan and day_plan["macros_ratio"]:
                message += self.messages.DAY_PLAN_MACRO_RATIO.format(
                    ratio=day_plan['macros_ratio']
                )
            elif "total_proteins" in day_plan and "total_fats" in day_plan and "total_carbs" in day_plan:
                message += self.messages.DAY_PLAN_MACROS.format(
                    proteins=day_plan['total_proteins'],
                    fats=day_plan['total_fats'],
                    carbs=day_plan['total_carbs']
                )

            message += "\n"

            # Добавляем приемы пищи
            if "meals" in day_plan:
                for meal in day_plan["meals"]:
                    meal_type = self.translate_meal_type(meal.get("type", ""))
                    title = meal.get("title", "")
                    description = meal.get("description", "")
                    relevance = self.get_relevance_stars(meal.get("relevance_score", 0))
                    emoji = self.create_meal_emoji(meal.get("type", ""))

                    message += self.messages.DAY_PLAN_MEAL_HEADER.format(
                        emoji=emoji,
                        meal_type=meal_type,
                        title=title,
                        relevance=relevance
                    )

                    if description:
                        message += f"{description}\n"

                    # Добавляем информацию о продуктах
                    if "products" in meal and meal["products"]:
                        message += self.messages.DAY_PLAN_INGREDIENTS_HEADER
                        for product in meal["products"]:
                            name = product.get("name", "")
                            quantity = product.get("quantity", "")
                            unit = product.get("unit", "")

                            message += self.messages.DAY_PLAN_INGREDIENT_FORMAT.format(
                                name=name,
                                quantity=quantity,
                                unit=unit
                            )

                    # Добавляем информацию о калориях и макронутриентах
                    message += self.messages.DAY_PLAN_NUTRITION_HEADER
                    if meal.get("calories"):
                        message += self.messages.DAY_PLAN_CALORIES.format(
                            calories=meal['calories']
                        )
                    if meal.get("proteins"):
                        message += self.messages.DAY_PLAN_PROTEINS.format(
                            proteins=meal['proteins']
                        )
                    if meal.get("fats"):
                        message += self.messages.DAY_PLAN_FATS.format(
                            fats=meal['fats']
                        )
                    if meal.get("carbs"):
                        message += self.messages.DAY_PLAN_CARBS.format(
                            carbs=meal['carbs']
                        )
                    if meal.get("fiber"):
                        message += self.messages.DAY_PLAN_FIBER.format(
                            fiber=meal['fiber']
                        )

                    # Добавляем объяснение, почему блюдо рекомендовано
                    why_recommended = meal.get("why_recommended", "")
                    if why_recommended:
                        message += self.messages.DAY_PLAN_WHY_RECOMMENDED_HEADER.format(
                            why_recommended=why_recommended
                        )

                    # Добавляем инструкцию по приготовлению
                    preparation = meal.get("preparation", "")
                    if preparation:
                        message += self.messages.DAY_PLAN_PREPARATION_HEADER.format(
                            preparation=preparation
                        )

                    message += "\n"

            # Добавляем советы на день, если они есть
            if "tips" in day_plan and day_plan["tips"]:
                message += self.messages.DAY_PLAN_TIP.format(
                    tip=day_plan['tips']
                )

            # Добавляем инструкции для отметки о соблюдении
            message += self.messages.DAY_PLAN_TRACKING_HEADER
            message += self.messages.DAY_PLAN_TRACKING_FOLLOWED
            message += self.messages.DAY_PLAN_TRACKING_PARTIALLY
            message += self.messages.DAY_PLAN_TRACKING_SUBSTITUTED
            message += self.messages.DAY_PLAN_TRACKING_SKIPPED

            return format_diet_message_for_whatsapp(message)

        except Exception as e:
            self.logger.error(f"Error creating day diet plan: {str(e)}")
            return self.messages.ERROR_CREATE_DAY_DIET_PLAN

    def format_shopping_list(self, shopping_list_data: Dict[str, Any]) -> str:
        """
        Форматирует список покупок для отправки пользователю

        Args:
            shopping_list_data: Данные списка покупок

        Returns:
            str: Отформатированный список покупок
        """
        try:
            message = self.messages.SHOPPING_LIST_HEADER

            # Группируем продукты по категориям
            categories = {
                "Фрукты и овощи": [],
                "Мясо и рыба": [],
                "Молочные продукты": [],
                "Хлеб и крупы": [],
                "Специи и приправы": [],
                "Напитки": [],
                "Другое": []
            }

            # Распределяем продукты по категориям
            for item in shopping_list_data.get("items", []):
                name = item.get("name", "")
                quantity = item.get("quantity", "")
                unit = item.get("unit", "")
                price = item.get("estimated_price", "")

                # Если есть категория в данных, используем её
                category = item.get("category", self._categorize_product(name))

                # Форматируем элемент списка
                item_text = f"{name}: {quantity} {unit}"
                if price:
                    item_text += f" (~{price} к.)"

                categories[category].append(item_text)

            # Формируем сообщение по категориям
            for category, items in categories.items():
                if items:
                    message += self.messages.CATEGORY_FORMAT.format(category=category)
                    for item in items:
                        message += self.messages.ITEM_FORMAT.format(item=item)
                    message += "\n"

            # Добавляем общую стоимость
            if "total_estimated_price" in shopping_list_data and shopping_list_data["total_estimated_price"]:
                message += self.messages.TOTAL_PRICE.format(price=shopping_list_data["total_estimated_price"])

            # Добавляем инструкции
            message += self.messages.SHOPPING_INSTRUCTIONS

            return format_diet_message_for_whatsapp(message)

        except Exception as e:
            self.logger.error(f"Error formatting shopping list: {str(e)}")
            return self.messages.ERROR_FORMAT_SHOPPING_LIST

    # Вспомогательные методы
    # TODO использовать локализацию для этого
    def translate_day_name(self, day_name: str) -> str:
        """
        Переводит название дня недели на русский

        Args:
            day_name: Название дня на английском (Monday, Tuesday и т.д.)

        Returns:
            str: Название дня на русском
        """
        weekday_names = self.messages.get_weekday_names()
        english_days = {
            "Monday": "monday",
            "Tuesday": "tuesday",
            "Wednesday": "wednesday",
            "Thursday": "thursday",
            "Friday": "friday",
            "Saturday": "saturday",
            "Sunday": "sunday"
        }

        # Сначала преобразуем из формата "Monday" в "monday"
        day_key = english_days.get(day_name, day_name.lower())

        # Затем получаем перевод
        return weekday_names.get(day_key, day_name)

    def translate_meal_type(self, meal_type: str) -> str:
        """
        Переводит тип приема пищи на русский

        Args:
            meal_type: Тип приема пищи на английском

        Returns:
            str: Тип приема пищи на русском
        """
        meal_types = self.messages.get_meal_types()
        return meal_types.get(meal_type.lower(), meal_type.capitalize())

    def create_meal_emoji(self, meal_type: str) -> str:
        """
        Возвращает эмодзи для типа приема пищи

        Args:
            meal_type: Тип приема пищи

        Returns:
            str: Эмодзи
        """
        meal_emojis = self.messages.get_meal_emojis()
        return meal_emojis.get(meal_type.lower(), "🍴")

    def get_relevance_stars(self, score: int) -> str:
        """
        Возвращает звездочки для отображения релевантности

        Args:
            score: Оценка релевантности (1-10)

        Returns:
            str: Строка со звездочками
        """
        if not score:
            return ""

        # Преобразуем оценку 1-10 в шкалу 1-5 звезд
        stars_count = max(1, min(5, round(score / 2)))
        return "★" * stars_count

    def get_nearest_date_for_weekday(self, weekday_name: str) -> date:
        """
        Преобразует название дня недели в дату ближайшего такого дня недели

        Args:
            weekday_name: Название дня недели на английском (monday, tuesday и т.д.)

        Returns:
            date: Дата ближайшего дня недели
        """
        # Словарь для преобразования названия дня недели в число (0 - понедельник, 6 - воскресенье)
        weekday_mapping = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6
        }

        # Получаем текущую дату
        today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

        # Получаем номер текущего дня недели (0 - понедельник, 6 - воскресенье)
        today_weekday = today.weekday()

        # Получаем номер целевого дня недели
        target_weekday = weekday_mapping.get(weekday_name.lower())

        if target_weekday is None:
            # Если передано некорректное название дня недели, возвращаем текущую дату
            return today

        # Вычисляем разницу в днях
        days_diff = (target_weekday - today_weekday) % 7

        # Если разница 0 (тот же день) и нужен следующий такой день, добавляем 7 дней
        if days_diff == 0:
            days_diff = 7

        # Вычисляем дату ближайшего дня недели
        nearest_date = today + timedelta(days=days_diff)

        return nearest_date

    def get_day_of_week(self, date_val: date = None) -> str:
        """
        Возвращает день недели для указанной даты в формате 'monday', 'tuesday' и т.д.

        Args:
            date_val: Дата (по умолчанию сегодня)

        Returns:
            str: День недели
        """
        if not date_val:
            date_val = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

        # Получаем номер дня недели (0 - понедельник, 6 - воскресенье)
        weekday = date_val.weekday()

        # Преобразуем в строковое представление
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        return days[weekday]

    def _categorize_product(self, product_name: str) -> str:
        """
        Определяет категорию продукта по его названию

        Args:
            product_name: Название продукта

        Returns:
            str: Категория продукта
        """
        name_lower = product_name.lower()
        if any(item in name_lower for item in
               ["фрукт", "овощ", "ягод", "банан", "яблок", "морковь", "картофель", "помидор", "огурец"]):
            return "Фрукты и овощи"
        elif any(item in name_lower for item in
                 ["мясо", "рыба", "курица", "говядина", "свинина", "филе", "фарш"]):
            return "Мясо и рыба"
        elif any(item in name_lower for item in ["молоко", "сыр", "творог", "йогурт", "кефир", "сметана"]):
            return "Молочные продукты"
        elif any(item in name_lower for item in
                 ["хлеб", "крупа", "рис", "овсянка", "мука", "макароны", "паста"]):
            return "Хлеб и крупы"
        elif any(item in name_lower for item in ["специя", "соль", "перец", "приправа", "соус"]):
            return "Специи и приправы"
        elif any(item in name_lower for item in ["напиток", "вода", "сок", "чай", "кофе"]):
            return "Напитки"
        else:
            return "Другое"