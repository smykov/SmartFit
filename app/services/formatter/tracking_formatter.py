# app/services/formatter/tracking_formatter.py
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
            message = f"✅ Отлично! Я записал твой вес: {weight} кг.\n\n"
            
            if progress:
                if progress.get("total_weight_change", 0) < 0:
                    message += self.get_localized_message(
                        "tracking.weight_progress",
                        lang,
                        weight_change=abs(progress.get("total_weight_change", 0)),
                        percentage=abs(progress.get("weight_change_percentage", 0))
                    )
                else:
                    # Если вес увеличился
                    message += f"📈 С начала ты уже набрал {progress.get('total_weight_change', 0):.1f} кг "
                    message += f"({abs(progress.get('weight_change_percentage', 0)):.1f}% от начального веса)\n\n"
                
                message += self.get_localized_message(
                    "tracking.weight_goal_remaining",
                    lang,
                    remaining=abs(progress.get("remaining_to_goal", 0)),
                    target=progress.get("target_weight", 0)
                )
                
                message += f"\n📊 Ты выполнил {progress.get('goal_completion_percentage', 0):.1f}% своей цели!\n\n"
                
            message += "Продолжай отслеживать прогресс регулярно! 💪"
            
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
                "tracking.water_recorded",
                lang,
                amount=amount,
                ml_amount=ml_amount
            )
            
            if status:
                message += f"\nСегодня ты выпил всего: {status.get('current_water_intake', 0)} мл\n"
                message += f"Это {status.get('water_percentage', 0):.1f}% от дневной цели в {status.get('water_goal', 0)} мл\n\n"
                
            message += "Продолжай в том же духе! Регулярное потребление воды помогает контролировать голод и улучшает общее самочувствие."
            
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
            meal_type_display = meal_type.capitalize()
            
            # Формируем сообщение в зависимости от статуса
            if status == MealComplianceStatus.FOLLOWED:
                message = f"✅ Отлично! {meal_type_display} выполнен по плану."
            elif status == MealComplianceStatus.PARTIALLY:
                message = f"⚠️ Хорошо! {meal_type_display} частично выполнен по плану."
            elif status == MealComplianceStatus.SUBSTITUTED:
                message = f"🔄 Понятно! {meal_type_display} заменен на другое блюдо."
            elif status == MealComplianceStatus.SKIPPED:
                message = f"❌ Отмечено! {meal_type_display} пропущен."
            else:
                message = f"Записан статус для приема пищи: {meal_type_display}."
                
            # Добавляем информацию о общем соблюдении
            if compliance_data and "overall_score" in compliance_data:
                message += f"\n\nОбщее соблюдение плана на сегодня: {compliance_data['overall_score']:.1f}%"
                
                # Добавляем мотивацию в зависимости от процента соблюдения
                if compliance_data["overall_score"] >= 80:
                    message += "\n\n👍 Отличная работа! Продолжай в том же духе."
                elif compliance_data["overall_score"] >= 50:
                    message += "\n\n👍 Хороший результат! Старайся следовать плану."
                else:
                    message += "\n\n💪 Не сдавайся! Каждый день - это новая возможность."
                    
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
            message = f"*📊 СТАТИСТИКА И ПРОГРЕСС*\n\n"
            
            # Прогресс по весу
            if weight_progress:
                message += f"*⚖️ Прогресс по весу:*\n"
                message += f"• Начальный вес: {weight_progress.get('start_weight', 0)} кг\n"
                message += f"• Текущий вес: {weight_progress.get('current_weight', 0)} кг\n"
                message += f"• Целевой вес: {weight_progress.get('target_weight', 0)} кг\n\n"
                
                weight_change = weight_progress.get('total_weight_change', 0)
                if weight_change < 0:
                    message += f"• Изменение: -{abs(weight_change):.1f} кг 👍\n"
                elif weight_change > 0:
                    message += f"• Изменение: +{weight_change:.1f} кг\n"
                else:
                    message += "• Изменение: 0 кг (вес стабилен)\n"
                    
                message += f"• Осталось до цели: {abs(weight_progress.get('remaining_to_goal', 0)):.1f} кг\n"
                message += f"• Процент выполнения: {weight_progress.get('goal_completion_percentage', 0):.1f}%\n\n"
                
            # Статус воды на сегодня
            if today_status:
                message += f"*💧 Потребление воды сегодня:*\n"
                message += f"• Выпито: {today_status.get('current_water_intake', 0)} мл\n"
                message += f"• Цель: {today_status.get('water_goal', 0)} мл\n"
                message += f"• Выполнено: {today_status.get('water_percentage', 0):.1f}%\n\n"
                
            # Соблюдение плана питания
            if compliance_data and "meals" in compliance_data and compliance_data["meals"]:
                message += f"*🍽️ Соблюдение плана питания:*\n"
                
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
                    message += f"\nОбщее соблюдение: {compliance_data['overall_score']:.1f}%\n\n"
                    
            # Добавляем мотивационное сообщение
            message += "💪 *Продолжай в том же духе!* Ты на пути к своей цели."
            
            return self.format_for_whatsapp(message)
            
        except Exception as e:
            return self.handle_exception(
                e,
                "Error formatting stats message",
                "tracking.stats_error",
                lang
            )
