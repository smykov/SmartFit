# app/services/formatter/diet_formatter.py
from datetime import date
from typing import Dict, Any, List, Optional, Tuple, Set, Type

from pyexpat.errors import messages

from app.constants.localization_keys import LocalizationKeys as LK
from app.services.formatter.base_formatter import BaseFormatter
from app.services.localization.localization_interface import ILocalizationService
from app.utils.date_helper import DateHelper
from app.utils.format_helper import FormatHelper
from app.exceptions.formatter_exceptions import FormatterException


class DietFormatter(BaseFormatter):
    """Класс для форматирования планов диет"""

    def __init__(self, localization_service: ILocalizationService):
        """
        Инициализация форматтера диет

        Args:
            localization_service: Сервис локализации сообщений
        """
        super().__init__(localization_service)

    def get_diet_summary(self, diet_plan: Dict[str, Any], lang: Optional[str] = None) -> str:
        """
        Создает сводку плана диеты

        Args:
            diet_plan: План диеты
            lang: Код языка

        Returns:
            str: Отформатированная сводка плана
        """
        try:
            # Получаем персонализированное обращение
            personalized_note = diet_plan.get("personalized_note", "")

            # Формируем заголовок
            summary = self.get_localized_message(LK.Diet.Full.Summary.HEADER, lang)

            # Добавляем персонализированное обращение
            if personalized_note:
                summary += f"{personalized_note}\n\n"

            # Добавляем общую информацию о плане
            summary += self._get_plan_general_info(diet_plan, lang)

            # Примеры приемов пищи на сегодня или первый день
            today = DateHelper.get_current_date().isoformat()

            if "daily_plans" in diet_plan and diet_plan["daily_plans"]:
                # Используем сегодняшний день или первый доступный
                day_key = today if today in diet_plan["daily_plans"] else next(iter(diet_plan["daily_plans"]))
                day_plan = diet_plan["daily_plans"][day_key]

                # Получаем день недели и форматируем дату
                day_date = DateHelper.get_nearest_date_for_weekday(day_key)
                weekday_key = day_date.strftime("%A").lower()
                day_name = self.get_localized_message(
                    LK.Common.WEEKDAY_NAMES.format(weekday_key),
                    lang
                ).capitalize()

                date_format = self.get_localized_message(LK.Common.DAY_FORMAT, lang)
                date_formatted = DateHelper.format_date(day_date, date_format)

                # Добавляем пример меню на день
                summary += self.get_localized_message(
                    LK.Diet.Full.Summary.DAY_MENU_EXAMPLE,
                    lang,
                    day_name=day_name,
                    date_formatted=date_formatted
                )

                # Добавляем блюда
                if "meals" in day_plan:
                    for meal in day_plan["meals"]:
                        summary = self._add_meal_info_to_summary(summary, meal, lang)

            return self.format_for_whatsapp(summary)

        except Exception as e:
            return self.handle_exception(
                e,
                "Error creating diet summary",
                LK.Diet.Full.CREATING_ERROR,
                lang
            )

    def get_short_diet_summary(self, diet_plan: Dict[str, Any], lang: Optional[str] = None) -> str:
        """
        Создает сводку краткой версии плана диеты для согласования

        Args:
            diet_plan: План диеты
            lang: Код языка

        Returns:
            str: Отформатированная сводка плана
        """
        try:
            # Формируем заголовок
            summary = self.get_localized_message(LK.Diet.Short.Summary.HEADER, lang)

            # Добавляем персонализированное обращение
            personalized_note = diet_plan.get("personalized_note", "")
            if personalized_note:
                summary += f"{personalized_note}\n\n"

            # Информация о плане
            summary += self.get_localized_message(LK.Diet.Short.Summary.INFO, lang)

            # Формируем план по дням недели
            if "daily_plans" in diet_plan:
                for weekday, day_plan in diet_plan["daily_plans"].items():
                    # Получаем локализованное название дня недели
                    weekday_name = self.get_localized_message(
                        LK.Common.WEEKDAY_NAMES.format(weekday),
                        lang
                    ).capitalize()

                    # Добавляем заголовок дня
                    summary += self.get_localized_message(
                        LK.Diet.Short.Summary.WEEKDAY,
                        lang,
                        weekday_name=weekday_name
                    )

                    # Добавляем информацию о калориях
                    if "total_calories" in day_plan:
                        summary += self.get_localized_message(
                            LK.Diet.Short.Summary.TOTAL_CALORIES,
                            lang,
                            calories=day_plan['total_calories']
                        )

                    # Добавляем информацию о приемах пищи
                    if "meals" in day_plan:
                        for meal in day_plan["meals"]:
                            meal_type = self.get_localized_meal_type(meal.get("type", ""), lang)
                            title = meal.get("title", "")
                            calories = meal.get("calories", "")
                            emoji = self.get_meal_emoji(meal.get("type", ""), lang)

                            # Формируем строку приема пищи
                            meal_text = self.get_localized_message(
                                LK.Diet.Short.Summary.MEAL_FORMAT,
                                lang,
                                emoji=emoji,
                                meal_type=meal_type,
                                title=title
                            )

                            # Добавляем калории, если они есть
                            if calories:
                                meal_text += self.get_localized_message(
                                    LK.Diet.Short.Summary.MEAL_CALORIES,
                                    lang,
                                    calories=calories
                                )

                            summary += meal_text + "\n"

                    summary += "\n"

            return self.format_for_whatsapp(summary)

        except Exception as e:
            return self.handle_exception(
                e,
                "Error creating short diet summary",
                LK.Diet.Short.CREATING_ERROR,
                lang
            )

    def get_short_diet_next_steps(self, lang: Optional[str] = None) -> str:
        """
        Создает сводку о следующих шагах после генерации короткого плана

        Args:
            lang: Код языка

        Returns:
            str: Информация о следующих шагах
        """
        try:
            # Формируем сообщение о следующих шагах
            next_steps = self.get_localized_message(LK.Diet.Short.NextStep.HEADER, lang)
            next_steps += self.get_localized_message(LK.Diet.Short.NextStep.RECIPES, lang)
            next_steps += self.get_localized_message(LK.Diet.Short.NextStep.NUTRITION, lang)
            next_steps += self.get_localized_message(LK.Diet.Short.NextStep.EXPLANATIONS, lang)
            next_steps += self.get_localized_message(LK.Diet.Short.NextStep.SHOPPING, lang)

            return self.format_for_whatsapp(next_steps)

        except Exception as e:
            return self.handle_exception(
                e,
                "Error creating short diet next steps",
                LK.Diet.Short.CREATING_ERROR,
                lang
            )

    def get_full_diet_plan(self, diet_plan: Dict[str, Any], lang: Optional[str] = None) -> List[str]:
        """
        Создает полный план диеты на все дни для отправки пользователю.
        Возвращает список сообщений из-за ограничений длины в WhatsApp.

        Args:
            diet_plan: План диеты
            lang: Код языка

        Returns:
            List[str]: Список сообщений с планом диеты
        """
        try:
            messages = []

            # Формируем первое сообщение с общей информацией
            intro_message = self._create_full_plan_intro(diet_plan, lang)
            messages.append(
                self.format_for_whatsapp(intro_message)
            )

            # Создаем отдельное сообщение для каждого дня
            if "daily_plans" in diet_plan and diet_plan["daily_plans"]:
                # Сортируем даты
                sorted_dates = sorted(diet_plan["daily_plans"].keys())

                for day_key in sorted_dates:
                    day_messages = self._create_day_messages(diet_plan, day_key, lang, is_full_plan=True)
                    for day_message in day_messages:
                        if day_message:
                            messages.append(
                                self.format_for_whatsapp(day_message)
                            )

            return messages

        except Exception as e:
            return [self.handle_exception(
                e,
                "Error creating full diet plan",
                LK.Diet.Full.CREATING_ERROR,
                lang
            )]

    def get_day_diet_plan(self, diet_plan: Dict[str, Any], day_date: Optional[date] = None,
                          lang: Optional[str] = None) -> List[str]:
        """
        Создает детальный план диеты на конкретный день

        Args:
            diet_plan: План диеты
            day_date: Дата, на которую нужен план (по умолчанию сегодня)
            lang: Код языка

        Returns:
            List[str]: Сообщения с планом на день
        """
        try:
            # Если дата не указана, используем сегодняшнюю
            if not day_date:
                day_date = DateHelper.get_current_date()

            # Преобразуем в строку дня недели
            day_key = DateHelper.get_day_of_week(day_date)

            # Проверяем, есть ли план на указанный день
            if "daily_plans" not in diet_plan or day_key not in diet_plan["daily_plans"]:
                return [self.get_localized_message(LK.Diet.Day.NO_PLAN, lang)]

            # Создаем сообщения для дня
            messages = self._create_day_messages(diet_plan, day_key, lang, day_date=day_date)

            formatted_messages = []
            for message in messages:
                if message:
                    formatted_messages.append(self.format_for_whatsapp(message))

            return formatted_messages

        except Exception as e:
            return [self.handle_exception(
                e,
                "Error creating day diet plan",
                LK.Diet.Day.CREATING_ERROR,
                lang
            )]

    def get_diet_tracking_info_message(self, lang: Optional[str] = None) -> str:
        """
        Создает форматированный текст с информацией о командах трекинга диеты

        Args:
            lang: Код языка

        Returns:
            str: Сообщение с текстом информации по трекингу диеты
        """
        try:
            # Добавляем инструкции для отметки о соблюдении
            message = self.get_localized_message(LK.Diet.Day.Tracking.HEADER, lang)
            message += self.get_localized_message(LK.Diet.Day.Tracking.FOLLOWED, lang)
            message += self.get_localized_message(LK.Diet.Day.Tracking.PARTIALLY, lang)
            message += self.get_localized_message(LK.Diet.Day.Tracking.SUBSTITUTED, lang)
            message += self.get_localized_message(LK.Diet.Day.Tracking.SKIPPED, lang)

            return self.format_for_whatsapp(message)

        except Exception as e:
            return self.handle_exception(
                e,
                "Error creating diet tracking info message",
                LK.Diet.Day.CREATING_ERROR,
                lang
            )

    # Вспомогательные методы

    def _get_plan_general_info(self, diet_plan: Dict[str, Any], lang: Optional[str] = None) -> str:
        """
        Добавляет общую информацию о плане диеты в сообщение

        Args:
            message: Текущее сообщение
            diet_plan: План диеты
            lang: Код языка

        Returns:
            str: Обновленное сообщение
        """
        message = ""
        # Информация о калорийном дефиците
        if "caloric_deficit" in diet_plan and diet_plan["caloric_deficit"]:
            message += self.get_localized_message(
                LK.Diet.Full.Summary.DEFICIT,
                lang,
                deficit=diet_plan['caloric_deficit']
            )

        # Информация о калорийном профиците
        if "caloric_proficit" in diet_plan and diet_plan["caloric_proficit"]:
            message += self.get_localized_message(
                LK.Diet.Full.Summary.PROFICIT,
                lang,
                proficit=diet_plan['caloric_proficit']
            )

        # Общие рекомендации
        if "general_recommendations" in diet_plan and diet_plan["general_recommendations"]:
            message += self.get_localized_message(
                LK.Diet.Full.Summary.RECOMMENDATIONS,
                lang,
                recommendations=diet_plan['general_recommendations']
            )

        # Информация о стоимости
        if "estimated_weekly_price" in diet_plan and diet_plan["estimated_weekly_price"]:
            currency = diet_plan.get("currency", "рублей")
            message += self.get_localized_message(
                LK.Diet.Full.Summary.PRICE,
                lang,
                price=diet_plan['estimated_weekly_price'],
                currency=currency
            )

        return message

    def _add_meal_info_to_summary(self, summary: str, meal: Dict[str, Any], lang: Optional[str] = None) -> str:
        """
        Добавляет информацию о приеме пищи в сводку

        Args:
            summary: Текущая сводка
            meal: Данные о приеме пищи
            lang: Код языка

        Returns:
            str: Обновленная сводка
        """
        meal_type = self.get_localized_meal_type(meal.get("type", ""), lang)
        title = meal.get("title", "")
        calories = meal.get("calories", "")
        relevance = FormatHelper.get_relevance_stars(meal.get("relevance_score", 0))
        emoji = self.get_meal_emoji(meal.get("type", ""), lang)

        summary += self.get_localized_message(
            LK.Diet.Full.Summary.MEAL_FORMAT,
            lang,
            emoji=emoji,
            meal_type=meal_type,
            title=title,
            relevance=relevance
        )

        if calories:
            summary += self.get_localized_message(
                LK.Diet.Full.Summary.CALORIES_FORMAT,
                lang,
                calories=calories
            )

        # Добавляем объяснение, почему блюдо рекомендовано
        why_recommended = meal.get("why_recommended", "")
        if why_recommended:
            summary += self.get_localized_message(
                LK.Diet.Full.Summary.WHY_RECOMMENDED,
                lang,
                why_recommended=why_recommended
            )

        return summary

    def _create_full_plan_intro(self, diet_plan: Dict[str, Any], lang: Optional[str] = None) -> str:
        """
        Создает вводное сообщение для полного плана диеты

        Args:
            diet_plan: План диеты
            lang: Код языка

        Returns:
            str: Вводное сообщение
        """
        # Получаем персонализированное обращение для первого сообщения
        intro_message = self.get_localized_message(LK.Diet.Full.Plan.HEADER, lang)

        # Добавляем персонализированное обращение
        personalized_note = diet_plan.get("personalized_note", "")
        if personalized_note:
            intro_message += f"{personalized_note}\n\n"

        # Добавляем общую информацию о плане
        intro_message += self._get_plan_general_info(diet_plan, lang)

        return intro_message

    def _create_day_messages(self, diet_plan: Dict[str, Any], day_key: str, lang: Optional[str] = None,
                             is_full_plan: bool = False, day_date: Optional[date] = None) -> List[str]:
        """
        Создает сообщение с планом на день

        Args:
            diet_plan: План диеты
            day_key: Ключ дня в плане
            lang: Код языка
            is_full_plan: Флаг, указывающий, что сообщение создается для полного плана
            day_date: Конкретная дата дня

        Returns:
            List[str]: Сообщения с планом на день
        """
        day_plan = diet_plan["daily_plans"][day_key]

        # Получаем день недели и форматируем дату
        if not day_date:
            day_date = DateHelper.get_nearest_date_for_weekday(day_key)

        weekday_key = day_date.strftime("%A").lower()
        day_name = self.get_localized_message(
            f"common.weekday_names.{weekday_key}",
            lang
        ).capitalize()

        try:
            date_format = self.get_localized_message(LK.Common.DAY_FORMAT, lang)
            date_formatted = DateHelper.format_date(day_date, date_format)
        except Exception as e:
            self.logger.error(f"Error formatting date: {e}")
            # Запасной вариант форматирования
            date_formatted = day_date.strftime("%d.%m.%Y")

        # Определяем префикс ключей локализации и формат заголовка в зависимости от типа сообщения
        if is_full_plan:
            header_key = LK.Diet.Full.Plan.DAY_HEADER
            prefix = "diet.full.plan"
        else:
            header_key = LK.Diet.Day.HEADER
            prefix = "diet.day"
            # Для подробного плана дня заголовок с большими буквами
            day_name = day_name.upper()

        header = self.get_localized_message(
            header_key,
            lang,
            day_name=day_name,
            date_formatted=date_formatted
        )
        # Добавляем информацию о калориях и макронутриентах
        nutritional_info = self._get_nutritional_summary(day_plan, lang, prefix)

        messages = [header + nutritional_info]
        # Добавляем приемы пищи
        if "meals" in day_plan:
            for meal in day_plan["meals"]:
                messages.append(self._get_meal_details(meal, lang, prefix, is_full_plan))

        tips = ""
        # Добавляем советы на день, если они есть
        if "tips" in day_plan and day_plan["tips"]:
            tip_key = f"{prefix}.day_tip" if is_full_plan else f"{prefix}.tip"
            tips += self.get_localized_message(
                tip_key,
                lang,
                tip=day_plan['tips']
            )
        messages.append(tips)

        # TODO добавить список покупок на день (просто суммированный список продуктов из ингредиентов блюд)

        return messages

    def _get_nutritional_summary(self, day_plan: Dict[str, Any], lang: Optional[str] = None,
                                 prefix: str = "diet.day") -> str:
        """
        Добавляет сводку питательных веществ в сообщение

        Args:
            day_plan: План на день
            lang: Код языка
            prefix: Префикс для ключей локализации

        Returns:
            str: Обновленное сообщение
        """
        message = ""
        # Добавляем информацию о калориях
        if "total_calories" in day_plan:
            message += self.get_localized_message(
                f"{prefix}.total_calories",
                lang,
                calories=day_plan['total_calories']
            )

        # Добавляем информацию о соотношении макронутриентов
        if "macros_ratio" in day_plan and day_plan["macros_ratio"]:
            message += self.get_localized_message(
                f"{prefix}.macro_ratio",
                lang,
                ratio=day_plan['macros_ratio']
            )
        elif "total_proteins" in day_plan and "total_fats" in day_plan and "total_carbs" in day_plan:
            message += self.get_localized_message(
                f"{prefix}.macros",
                lang,
                proteins=day_plan['total_proteins'],
                fats=day_plan['total_fats'],
                carbs=day_plan['total_carbs']
            )

        return message

    def _get_meal_details(self, meal: Dict[str, Any], lang: Optional[str] = None,
                          prefix: str = "diet.day",
                          is_summary: bool = False) -> str:
        """
        Добавляет детали приема пищи в сообщение

        Args:
            meal: Данные о приеме пищи
            lang: Код языка
            prefix: Префикс для ключей локализации
            is_summary: Флаг, указывающий на сокращенный формат

        Returns:
            str: Обновленное сообщение
        """
        meal_type = self.get_localized_meal_type(meal.get("type", ""), lang)
        title = meal.get("title", "")
        description = meal.get("description", "")
        relevance = FormatHelper.get_relevance_stars(meal.get("relevance_score", 0))
        emoji = self.get_meal_emoji(meal.get("type", ""), lang)

        # Добавляем заголовок приема пищи
        message = self.get_localized_message(
            f"{prefix}.meal_header",
            lang,
            emoji=emoji,
            meal_type=meal_type,
            title=title,
            relevance=relevance
        )

        # Если это сокращенный формат или полный план, возвращаем без дополнительных деталей
        if is_summary:
            return message

        # Добавляем описание, если есть
        if description:
            message += f"{self.format_helper.apply_style(description, 'italic')}\n\n"

        # Добавляем информацию о продуктах
        if "products" in meal and meal["products"]:
            message += self.get_localized_message(f"{prefix}.ingredients_header", lang)
            for product in meal["products"]:
                name = product.get("name", "")
                quantity = product.get("quantity", "")
                unit = product.get("unit", "")
                if quantity > 0:
                    message += self.get_localized_message(
                        f"{prefix}.ingredient_format",
                        lang,
                        name=name,
                        quantity=quantity,
                        unit=unit
                    )
            message += f"\n"

        # Добавляем информацию о питательных веществах
        message += self.get_localized_message(f"{prefix}.nutrition_header", lang)

        # Добавляем калории
        if meal.get("calories"):
            message += self.get_localized_message(
                f"{prefix}.calories",
                lang,
                calories=meal['calories']
            )

        # Добавляем белки
        if meal.get("proteins"):
            message += self.get_localized_message(
                f"{prefix}.proteins",
                lang,
                proteins=meal['proteins']
            )

        # Добавляем жиры
        if meal.get("fats"):
            message += self.get_localized_message(
                f"{prefix}.fats",
                lang,
                fats=meal['fats']
            )

        # Добавляем углеводы
        if meal.get("carbs"):
            message += self.get_localized_message(
                f"{prefix}.carbs",
                lang,
                carbs=meal['carbs']
            )

        # Добавляем клетчатку
        if meal.get("fiber"):
            message += self.get_localized_message(
                f"{prefix}.fiber",
                lang,
                fiber=meal['fiber']
            )

        message += f"\n"

        # Добавляем объяснение, почему блюдо рекомендовано
        why_recommended = meal.get("why_recommended", "")
        if why_recommended:
            message += self.get_localized_message(
                f"{prefix}.why_recommended_header",
                lang,
                why_recommended=self.format_helper.apply_style(why_recommended, "italic")
            )
            message += f"\n"

        # Добавляем инструкцию по приготовлению
        preparation = self.format_for_whatsapp(meal.get("preparation", ""))
        if preparation:
            message += self.get_localized_message(
                f"{prefix}.preparation_header",
                lang,
                preparation=preparation
            )

        message += "\n"
        return message
