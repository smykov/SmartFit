# Обновленный класс TrackingFormatter

from typing import Dict, Any, Optional

from app.constants.localization_keys import LocalizationKeys as LK
from app.models.tracking import MealComplianceStatus
from app.services.formatter.base_formatter import BaseFormatter
from app.services.localization.localization_interface import ILocalizationService


class TrackingFormatter(BaseFormatter):
    """Класс для форматирования данных трекинга"""

    def __init__(self, localization_service: ILocalizationService):
        """
        Инициализация форматтера трекинга

        Args:
            localization_service: Сервис локализации сообщений
        """
        super().__init__(localization_service)

    def format_weight_recorded_message(self, weight: float, progress: Optional[Dict[str, Any]] = None,
                                       lang: Optional[str] = None) -> str:
        """
        Форматирует сообщение о записи веса

        Args:
            weight: Записанный вес
            progress: Информация о прогрессе
            lang: Код языка

        Returns:
            str: Отформатированное сообщение
        """
        try:
            message = self.get_localized_message(LK.Tracking.Weight.RECORDED, lang, weight=weight)

            if progress:
                if progress.get("total_weight_change", 0) < 0:
                    message += self.get_localized_message(
                        LK.Tracking.Weight.PROGRESS,
                        lang,
                        weight_change=abs(progress.get("total_weight_change", 0)),
                        percentage=abs(progress.get("weight_change_percentage", 0))
                    )
                else:
                    # Если вес увеличился
                    message += self.get_localized_message(
                        LK.Tracking.Weight.WEIGHT_CHANGE,
                        lang,
                        weight_change=progress.get("total_weight_change", 0),
                        percentage=abs(progress.get("weight_change_percentage", 0))
                    )

                message += self.get_localized_message(
                    LK.Tracking.Weight.GOAL_REMAINING,
                    lang,
                    remaining=abs(progress.get("remaining_to_goal", 0)),
                    target=progress.get("target_weight", 0)
                )

                message += self.get_localized_message(
                    LK.Tracking.Weight.GOAL_PERCENTAGE,
                    lang,
                    percentage=progress.get("goal_completion_percentage", 0)
                )

            message += self.get_localized_message(LK.Tracking.Weight.KEEP_TRACKING, lang)

            return self.format_for_whatsapp(message)

        except Exception as e:
            return self.handle_exception(
                e,
                "Error formatting weight recorded message",
                "tracking.weight_recorded",
                lang
            )

    def format_water_recorded_message(self, amount: float, ml_amount: float,
                                      status: Optional[Dict[str, Any]] = None,
                                      lang: Optional[str] = None,
                                      weekly_avg: float = 0,
                                      days_tracked: int = 0) -> str:
        """
        Форматирует сообщение о записи потребления воды

        Args:
            amount: Количество стаканов
            ml_amount: Количество в миллилитрах
            status: Статус трекинга
            lang: Код языка
            weekly_avg: Среднее потребление воды за неделю (мл)
            days_tracked: Количество дней с отслеживанием воды

        Returns:
            str: Отформатированное сообщение
        """
        try:
            message = self.get_localized_message(
                LK.Tracking.Water.RECORDED,
                lang,
                amount=amount,
                ml_amount=ml_amount
            )

            if status:
                message += self.get_localized_message(
                    LK.Tracking.Water.DAILY_TOTAL,
                    lang,
                    current_intake=status.get('current_water_intake', 0)
                )

                message += self.get_localized_message(
                    LK.Tracking.Water.GOAL_PERCENTAGE,
                    lang,
                    percentage=status.get('water_percentage', 0),
                    goal=status.get('water_goal', 0)
                )

            # Добавляем информацию о средних показателях за неделю
            if days_tracked > 0 and weekly_avg > 0:
                message += self.get_localized_message(
                    LK.Tracking.Water.WEEKLY_AVERAGE,
                    lang,
                    avg_ml=round(weekly_avg),
                    days=days_tracked
                )

            message += self.get_localized_message(LK.Tracking.Water.MOTIVATION, lang)

            return self.format_for_whatsapp(message)

        except Exception as e:
            return self.handle_exception(
                e,
                "Error formatting water recorded message",
                LK.Tracking.Water.RECORDED,
                lang
            )

    def format_compliance_message(self, meal_type: str, status: str,
                                  compliance_data: Optional[Dict[str, Any]] = None,
                                  lang: Optional[str] = None,
                                  nutrients_consumed: Optional[Dict[str, float]] = None,
                                  planned_meal: Optional[Dict[str, Any]] = None) -> str:
        """
        Форматирует сообщение о соблюдении плана питания

        Args:
            meal_type: Тип приема пищи
            status: Статус соблюдения
            compliance_data: Общие данные о соблюдении
            lang: Код языка
            nutrients_consumed: Данные о потреблённых нутриентах
            planned_meal: Запланированный приём пищи

        Returns:
            str: Отформатированное сообщение
        """
        try:
            # Базовое сообщение о статусе
            status_key = self._get_status_key(status)
            status_message = self.get_localized_message(
                status_key, lang, meal_type=meal_type
            )

            # Добавляем информацию о калориях и других нутриентах, если она доступна
            calories_message = ''
            if nutrients_consumed and 'calories' in nutrients_consumed:
                # Базовая информация о калориях
                calorie_info = self.get_localized_message(
                    LK.Tracking.Compliance.CALORIES_INFO,
                    lang,
                    calories=round(nutrients_consumed['calories'])
                )
                calories_message = f"\n{calorie_info}"

                # Если доступны данные о запланированном приёме пищи, добавляем сравнение
                if planned_meal and 'calories' in planned_meal:
                    planned_calories = planned_meal['calories']
                    calorie_ratio = nutrients_consumed['calories'] / planned_calories if planned_calories > 0 else 1.0

                    # Добавляем информацию о процентном соотношении
                    if calorie_ratio > 1.1:
                        calories_message += f" ({self.get_localized_message(LK.Tracking.Compliance.EXCESS, lang, percent=round((calorie_ratio - 1) * 100))})"
                    elif calorie_ratio < 0.9:
                        calories_message += f" ({self.get_localized_message(LK.Tracking.Compliance.DEFICIT, lang, percent=round((1 - calorie_ratio) * 100))})"
                    else:
                        calories_message += f" ({self.get_localized_message(LK.Tracking.Compliance.ON_TARGET, lang)})"

            # Добавляем информацию о БЖУ, если доступна
            bju_info = []
            bju_message = ''

            for nutrient, key in [
                ('proteins', LK.Tracking.Compliance.PROTEINS),
                ('fats', LK.Tracking.Compliance.FATS),
                ('carbs', LK.Tracking.Compliance.CARBS)
            ]:
                if nutrient in nutrients_consumed:
                    # TODO добавить %% от нормы к нутриентам
                    name = self.get_localized_message(key, lang)
                    value = round(nutrients_consumed[nutrient], 1)
                    bju_info.append(f"{name}: {value} г")

            if bju_info:
                bju_message += f"\n{' | '.join(bju_info)}"

            overall_score = compliance_data.get('overall_score', 0)
            # Добавляем общую статистику соблюдения за день
            overall_message = f"\n{self.get_localized_message(LK.Tracking.Compliance.OVERALL_SCORE, lang, score=round(overall_score, 1))}"

            # Добавляем мотивационное сообщение
            motivation_message = ""
            if overall_score >= 80:
                motivation_message += f"\n{self.get_localized_message(LK.Tracking.Compliance.EXCELLENT, lang)}"
            elif overall_score >= 50:
                motivation_message += f"\n{self.get_localized_message(LK.Tracking.Compliance.GOOD, lang)}"
            else:
                motivation_message += f"\n{self.get_localized_message(LK.Tracking.Compliance.KEEP_TRYING, lang)}"

            return f"{status_message}\n{calories_message}\n{bju_message}\n{overall_message}\n{motivation_message}"

        except Exception as e:
            self.logger.error(f"Error formatting compliance message: {str(e)}")
            # В случае ошибки возвращаем простое сообщение
            return self.get_localized_message(LK.Tracking.Compliance.GENERIC_STATUS, lang, meal_type=meal_type,
                                              status=status)

    def _get_status_key(self, status: str) -> str:
        """
        Определяет ключ локализации для статуса соблюдения

        Args:
            status: Статус соблюдения

        Returns:
            str: Ключ локализации
        """
        if status == MealComplianceStatus.FOLLOWED.value:
            return LK.Tracking.Compliance.FOLLOWED
        elif status == MealComplianceStatus.PARTIALLY.value:
            return LK.Tracking.Compliance.PARTIALLY
        elif status == MealComplianceStatus.SUBSTITUTED.value:
            return LK.Tracking.Compliance.SUBSTITUTED
        elif status == MealComplianceStatus.SKIPPED.value:
            return LK.Tracking.Compliance.SKIPPED
        else:
            return LK.Tracking.Compliance.GENERIC_STATUS

    def format_stats_message(self, weight_progress: Optional[Dict[str, Any]],
                             today_status: Optional[Dict[str, Any]],
                             compliance_data: Optional[Dict[str, Any]],
                             lang: Optional[str] = None) -> str:
        """
        Форматирует сообщение со статистикой

        Args:
            weight_progress: Прогресс по весу
            today_status: Статус трекинга на сегодня
            compliance_data: Данные о соблюдении плана
            lang: Код языка

        Returns:
            str: Отформатированное сообщение
        """
        try:
            message = self.get_localized_message(LK.Tracking.Stats.HEADER, lang)

            # Прогресс по весу
            if weight_progress:
                message += self.get_localized_message(LK.Tracking.Stats.WEIGHT_SECTION, lang)
                message += self.get_localized_message(
                    LK.Tracking.Stats.WEIGHT_INITIAL,
                    lang,
                    weight=weight_progress.get('start_weight', 0)
                )
                message += self.get_localized_message(
                    LK.Tracking.Stats.WEIGHT_CURRENT,
                    lang,
                    weight=weight_progress.get('current_weight', 0)
                )
                message += self.get_localized_message(
                    LK.Tracking.Stats.WEIGHT_TARGET,
                    lang,
                    weight=weight_progress.get('target_weight', 0)
                )

                weight_change = weight_progress.get('total_weight_change', 0)
                if weight_change < 0:
                    message += self.get_localized_message(
                        LK.Tracking.Stats.WEIGHT_CHANGE_NEGATIVE,
                        lang,
                        change=abs(weight_change)
                    )
                elif weight_change > 0:
                    message += self.get_localized_message(
                        LK.Tracking.Stats.WEIGHT_CHANGE_POSITIVE,
                        lang,
                        change=weight_change
                    )
                else:
                    message += self.get_localized_message(LK.Tracking.Stats.WEIGHT_CHANGE_NEUTRAL, lang)

                message += self.get_localized_message(
                    LK.Tracking.Stats.WEIGHT_GOAL_REMAINING,
                    lang,
                    remaining=abs(weight_progress.get('remaining_to_goal', 0))
                )
                message += self.get_localized_message(
                    LK.Tracking.Stats.WEIGHT_GOAL_PERCENTAGE,
                    lang,
                    percentage=weight_progress.get('goal_completion_percentage', 0)
                )

                message += "\n"

            # Анализ потребления воды
            if today_status:
                message += self.get_localized_message(LK.Tracking.Stats.WATER_SECTION, lang)
                message += self.get_localized_message(
                    LK.Tracking.Stats.WATER_CONSUMED,
                    lang,
                    intake=today_status.get('current_water_intake', 0)
                )
                message += self.get_localized_message(
                    LK.Tracking.Stats.WATER_GOAL,
                    lang,
                    goal=today_status.get('water_goal', 0)
                )
                message += self.get_localized_message(
                    LK.Tracking.Stats.WATER_PERCENTAGE,
                    lang,
                    percentage=today_status.get('water_percentage', 0)
                )

                message += "\n"

            # Соблюдение плана питания
            if compliance_data and "meals" in compliance_data and compliance_data["meals"]:
                message += self.get_localized_message(LK.Tracking.Stats.COMPLIANCE_SECTION, lang)

                emoji_map = {
                    "followed": "✅",
                    "partially": "⚠️",
                    "substituted": "🔄",
                    "skipped": "❌",
                    "not_recorded": "❓"
                }

                for meal_type, status in compliance_data["meals"].items():
                    # Получаем локализованный тип приема пищи
                    meal_type_ru = self.get_localized_meal_type(meal_type, lang)
                    emoji = emoji_map.get(status, "❓")
                    message += f"• {meal_type_ru}: {emoji}\n"

                if "overall_score" in compliance_data:
                    message += self.get_localized_message(
                        LK.Tracking.Stats.COMPLIANCE_OVERALL,
                        lang,
                        score=compliance_data['overall_score']
                    )

            # Добавляем мотивационное сообщение
            message += self.get_localized_message(LK.Tracking.Stats.MOTIVATION, lang)

            return self.format_for_whatsapp(message)

        except Exception as e:
            return self.handle_exception(
                e,
                "Error formatting stats message",
                LK.Commands.Stats.ERROR,
                lang
            )

    def format_compliance_report(self,
                                 date_range: str,
                                 compliance_data: Optional[Dict[str, Any]],
                                 lang: Optional[str] = None) -> str:
        """
        Форматирует отчет о соблюдении плана за указанный период

        Args:
            date_range: Строка с описанием периода
            compliance_data: Список данных о соблюдении плана
            lang: Код языка

        Returns:
            str: Отформатированный отчет
        """
        try:
            # Базовый заголовок
            message = self.get_localized_message(
                LK.Tracking.Stats.COMPLIANCE_REPORT_HEADER,
                lang,
                date_range=date_range
            )

            # Если данных нет
            if not compliance_data or len(compliance_data) == 0:
                message += "\n" + self.get_localized_message(
                    LK.Tracking.Stats.NO_COMPLIANCE_DATA,
                    lang
                )
                return self.format_for_whatsapp(message)

            # Расчет общих показателей
            total_days = len(compliance_data)
            total_score = sum(
                item.get("overall_score", 0) for item in compliance_data) / total_days if total_days > 0 else 0

            # Суммарные данные по нутриентам
            total_calories = {
                "planned": 0,
                "consumed": 0
            }
            total_proteins = {
                "planned": 0,
                "consumed": 0
            }
            total_fats = {
                "planned": 0,
                "consumed": 0
            }
            total_carbs = {
                "planned": 0,
                "consumed": 0
            }

            # Собираем данные по всем дням
            for day_data in compliance_data:
                # Суммируем данные по всем приемам пищи в день
                day_meals = day_data.get("meals", {})

                for meal_type, meal_data in day_meals.items():
                    # Запланированные нутриенты
                    planned_meal = meal_data.get("planned_meal", {})
                    total_calories["planned"] += planned_meal.get("calories", 0)
                    total_proteins["planned"] += planned_meal.get("proteins", 0)
                    total_fats["planned"] += planned_meal.get("fats", 0)
                    total_carbs["planned"] += planned_meal.get("carbs", 0)

                    # Фактически потребленные нутриенты
                    total_calories["consumed"] += meal_data.get("calories_consumed", 0)
                    total_proteins["consumed"] += meal_data.get("proteins_consumed", 0)
                    total_fats["consumed"] += meal_data.get("fats_consumed", 0)
                    total_carbs["consumed"] += meal_data.get("carbs_consumed", 0)

            # Процент соответствия по нутриентам
            calorie_adherence = (total_calories["consumed"] / total_calories["planned"] * 100) if total_calories[
                                                                                                      "planned"] > 0 else 0
            protein_adherence = (total_proteins["consumed"] / total_proteins["planned"] * 100) if total_proteins[
                                                                                                      "planned"] > 0 else 0
            fat_adherence = (total_fats["consumed"] / total_fats["planned"] * 100) if total_fats["planned"] > 0 else 0
            carb_adherence = (total_carbs["consumed"] / total_carbs["planned"] * 100) if total_carbs["planned"] > 0 else 0

            # Добавляем общую статистику соблюдения
            message += f"\n{self.get_localized_message(LK.Tracking.Stats.OVERALL_ADHERENCE, lang, score=round(total_score, 1))}"

            # Добавляем статистику по калориям
            message += f"\n\n{self.get_localized_message(LK.Tracking.Stats.CALORIE_ADHERENCE, lang)}"
            message += f"\n{self.get_localized_message(LK.Tracking.Stats.PLANNED_CALORIES, lang, calories=round(total_calories['planned']))}"
            message += f"\n{self.get_localized_message(LK.Tracking.Stats.CONSUMED_CALORIES, lang, calories=round(total_calories['consumed']))}"
            message += f"\n{self.get_localized_message(LK.Tracking.Stats.ADHERENCE_PERCENTAGE, lang, percent=round(calorie_adherence, 1))}"

            # Добавляем статистику по макронутриентам
            message += f"\n\n{self.get_localized_message(LK.Tracking.Stats.MACROS_ADHERENCE, lang)}"

            # Белки
            message += f"\n{self.get_localized_message(LK.Tracking.Stats.PROTEIN_ADHERENCE, lang, percent=round(protein_adherence, 1))}"

            # Жиры
            message += f"\n{self.get_localized_message(LK.Tracking.Stats.FAT_ADHERENCE, lang, percent=round(fat_adherence, 1))}"

            # Углеводы
            message += f"\n{self.get_localized_message(LK.Tracking.Stats.CARB_ADHERENCE, lang, percent=round(carb_adherence, 1))}"

            # Добавляем рекомендации на основе данных
            message += f"\n\n{self.get_localized_message(LK.Tracking.Stats.RECOMMENDATIONS, lang)}"

            # Формируем рекомендации по калориям
            if calorie_adherence < 80:
                message += f"\n• {self.get_localized_message(LK.Tracking.Stats.LOW_CALORIE_RECOMMENDATION, lang)}"
            elif calorie_adherence > 120:
                message += f"\n• {self.get_localized_message(LK.Tracking.Stats.HIGH_CALORIE_RECOMMENDATION, lang)}"

            # Формируем рекомендации по белкам
            if protein_adherence < 80:
                message += f"\n• {self.get_localized_message(LK.Tracking.Stats.LOW_PROTEIN_RECOMMENDATION, lang)}"
            elif protein_adherence > 120:
                message += f"\n• {self.get_localized_message(LK.Tracking.Stats.HIGH_PROTEIN_RECOMMENDATION, lang)}"

            # Формируем рекомендации по жирам
            if fat_adherence > 130:
                message += f"\n• {self.get_localized_message(LK.Tracking.Stats.HIGH_FAT_RECOMMENDATION, lang)}"

            # Формируем рекомендации по углеводам
            if carb_adherence > 130:
                message += f"\n• {self.get_localized_message(LK.Tracking.Stats.HIGH_CARB_RECOMMENDATION, lang)}"
            elif carb_adherence < 70:
                message += f"\n• {self.get_localized_message(LK.Tracking.Stats.LOW_CARB_RECOMMENDATION, lang)}"

            # Мотивационное сообщение в зависимости от общего соблюдения
            if total_score >= 80:
                message += f"\n\n{self.get_localized_message(LK.Tracking.Stats.HIGH_SCORE_MOTIVATION, lang)}"
            elif total_score >= 50:
                message += f"\n\n{self.get_localized_message(LK.Tracking.Stats.MEDIUM_SCORE_MOTIVATION, lang)}"
            else:
                message += f"\n\n{self.get_localized_message(LK.Tracking.Stats.LOW_SCORE_MOTIVATION, lang)}"

            return self.format_for_whatsapp(message)

        except Exception as e:
            self.logger.error(f"Error formatting compliance report: {str(e)}")
            return self.get_localized_message(LK.Tracking.Stats.REPORT_ERROR, lang)