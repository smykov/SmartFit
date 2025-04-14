# Обновленный класс TrackingFormatter

import logging
from typing import Dict, Any, Optional, List

from app.constants.localization_keys import LocalizationKeys as LK
from app.models.tracking import MealComplianceStatus
from app.services.formatter.base_formatter import BaseFormatter
from app.services.localization.localization_interface import ILocalizationService
from app.utils.date_helper import DateHelper


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
                                      lang: Optional[str] = None) -> str:
        """
        Форматирует сообщение о записи потребления воды

        Args:
            amount: Количество стаканов
            ml_amount: Количество в миллилитрах
            status: Статус трекинга
            lang: Код языка

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

            message += self.get_localized_message(LK.Tracking.Water.MOTIVATION, lang)

            return self.format_for_whatsapp(message)

        except Exception as e:
            return self.handle_exception(
                e,
                "Error formatting water recorded message",
                "tracking.water_recorded",
                lang
            )

    def format_compliance_message(self, meal_type: str, status: str,
                                  compliance_data: Optional[Dict[str, Any]] = None,
                                  lang: Optional[str] = None) -> str:
        """
        Форматирует сообщение о соблюдении режима питания

        Args:
            meal_type: Тип приема пищи
            status: Статус соблюдения
            compliance_data: Общие данные о соблюдении
            lang: Код языка

        Returns:
            str: Отформатированное сообщение
        """
        try:
            meal_type_display = self.get_localized_meal_type(meal_type, lang)

            # Формируем сообщение в зависимости от статуса
            if status == MealComplianceStatus.FOLLOWED:
                message = self.get_localized_message(
                    LK.Tracking.Compliance.FOLLOWED,
                    lang,
                    meal_type=meal_type_display
                )
            elif status == MealComplianceStatus.PARTIALLY:
                message = self.get_localized_message(
                    LK.Tracking.Compliance.PARTIALLY,
                    lang,
                    meal_type=meal_type_display
                )
            elif status == MealComplianceStatus.SUBSTITUTED:
                message = self.get_localized_message(
                    LK.Tracking.Compliance.SUBSTITUTED,
                    lang,
                    meal_type=meal_type_display
                )
            elif status == MealComplianceStatus.SKIPPED:
                message = self.get_localized_message(
                    LK.Tracking.Compliance.SKIPPED,
                    lang,
                    meal_type=meal_type_display
                )
            else:
                message = self.get_localized_message(
                    LK.Tracking.Compliance.GENERIC_STATUS,
                    lang,
                    meal_type=meal_type_display
                )

            # Добавляем информацию о общем соблюдении
            if compliance_data and "overall_score" in compliance_data:
                message += self.get_localized_message(
                    LK.Tracking.Compliance.OVERALL_SCORE,
                    lang,
                    score=compliance_data['overall_score']
                )

                # Добавляем мотивацию в зависимости от процента соблюдения
                if compliance_data["overall_score"] >= 80:
                    message += self.get_localized_message(LK.Tracking.Compliance.EXCELLENT, lang)
                elif compliance_data["overall_score"] >= 50:
                    message += self.get_localized_message(LK.Tracking.Compliance.GOOD, lang)
                else:
                    message += self.get_localized_message(LK.Tracking.Compliance.KEEP_TRYING, lang)

            return self.format_for_whatsapp(message)

        except Exception as e:
            return self.handle_exception(
                e,
                "Error formatting compliance message",
                "tracking.compliance_recorded",
                lang
            )

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
                "tracking.stats_error",
                lang
            )