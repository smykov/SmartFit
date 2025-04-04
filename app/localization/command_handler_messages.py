from datetime import datetime
from typing import Dict, Any, List, Optional

from app.models.tracking import MealComplianceStatus
from app.templates.prompts import format_help_message


class CommandHandlerMessages:
    """Класс с локализованными сообщениями для обработчика команд"""

    # Общие сообщения
    NO_DIET_PLAN = "У тебя пока нет активного плана питания. Напиши 'диета' для создания нового плана."
    NO_PENDING_DIET_PLAN = "У тебя нет плана питания, ожидающего согласования. Напиши 'диета' для создания нового плана."
    COMMAND_NOT_FOUND = "Извините, я не распознал команду. Напишите 'помощь' для просмотра списка доступных команд."
    PREREQUISITES_NOT_MET = "Не удалось выполнить команду. Сначала нужно {requirement}."
    
    # Сообщения для обновления плана питания
    UPDATING_PLAN = "Я корректирую твой план питания согласно запросу. Это займет несколько секунд."
    UPDATE_FAILED = "К сожалению, не удалось обновить план питания. Попробуй позже."
    UPDATE_ERROR = "Извини, произошла ошибка при обновлении плана питания. Попробуй позже."
    INVALID_UPDATE_FORMAT = "Пожалуйста, укажите, что именно вы хотите изменить в плане. Например: 'Замени обед в понедельник на курицу'."
    
    # Сообщения для создания диеты
    DIET_GENERATION_STARTED = "🥗 Я начинаю создавать для вас краткую версию персонализированного плана питания на неделю. Это займет несколько минут."
    DIET_GENERATION_DETAILS = "После того, как я покажу вам план, вы сможете согласовать его или запросить изменения. После согласования я подготовлю полную версию с подробными рецептами и списком покупок."
    NO_DIET_FOR_TODAY = "У вас пока нет плана питания на сегодня. Напишите 'диета' для создания плана."
    NO_DIET_FOR_TOMORROW = "У вас пока нет плана питания на завтра. Напишите 'диета' для создания плана."
    
    # Сообщения для согласования плана
    PLAN_APPROVAL_SUCCESS = "✅ Отлично! Я начинаю готовить для вас полную версию плана питания с подробными рецептами и списком покупок. Это займет несколько минут."
    PLAN_APPROVAL_ERROR = "Извините, произошла ошибка при согласовании плана. Попробуйте позже."
    PLAN_DISAPPROVAL = "Понятно. Пожалуйста, уточните, что именно вы хотели бы изменить в плане. Например: 'Замени обед в понедельник' или 'Хочу больше белка'."
    
    # Сообщения для команды веса
    INVALID_WEIGHT_FORMAT = "Пожалуйста, укажите вес в формате 'вес XX.X', где XX.X - ваш вес в килограммах."
    INVALID_WEIGHT_VALUE = "Пожалуйста, укажите корректное значение веса (число)."
    WEIGHT_OUT_OF_RANGE = "Указанный вес находится вне допустимого диапазона (30-300 кг). Пожалуйста, проверьте значение."
    
    # Сообщения для команды воды
    INVALID_WATER_FORMAT = "Пожалуйста, укажите количество воды в формате 'вода X', где X - количество стаканов."
    INVALID_WATER_VALUE = "Пожалуйста, укажите корректное количество стаканов воды (число)."
    WATER_OUT_OF_RANGE = "Указанное количество воды находится вне допустимого диапазона (0-20 стаканов). Пожалуйста, проверьте значение."

    # Сообщения для списка покупок
    SHOPPING_LIST_GENERATION = "🛒 Начинаю формирование списка покупок на основе вашего плана питания. Это займет несколько секунд..."
    SHOPPING_LIST_ERROR = "Извините, не удалось создать список покупок. Попробуйте позже."
    INVALID_PRODUCT_FORMAT = "Пожалуйста, укажите название продукта в формате 'купил [название продукта]'."
    PRODUCT_MARKED = "✅ Отлично! Я отметил '{product}' как купленный."
    PRODUCT_NOT_FOUND = "Я не нашел '{product}' в твоем списке покупок. Проверь название продукта или напиши 'список покупок' для просмотра полного списка."
    
    # Сообщения для команды статистики
    STATS_ERROR = "К сожалению, произошла ошибка при формировании статистики. Попробуйте позже."
    
    # Сообщения для команды соблюдения плана
    INVALID_COMPLIANCE_FORMAT = "Пожалуйста, укажите тип приема пищи в формате '[выполнено/частично/заменил/пропустил] [завтрак/обед/ужин/перекус]'."
    INVALID_COMPLIANCE_TYPE = "Пожалуйста, укажите один из типов соблюдения плана: выполнено, частично, заменил, пропустил."
    INVALID_MEAL_TYPE = "Пожалуйста, укажите корректный тип приема пищи: завтрак, обед, ужин или перекус."
    NO_DIET_PLAN_FOR_COMPLIANCE = "У тебя пока нет активного плана питания для отметки о соблюдении. Напиши 'диета' для создания нового плана."
    COMPLIANCE_RECORD_ERROR = "Извините, произошла ошибка при записи данных о соблюдении плана. Попробуйте позже."

    def get_help_message(self) -> str:
        """
        Возвращает отформатированное сообщение с помощью
        
        Returns:
            str: Сообщение с помощью
        """
        return format_help_message()
    
    def format_weight_recorded_message(self, weight: float, progress: Optional[Dict[str, Any]] = None) -> str:
        """
        Форматирует сообщение о записи веса
        
        Args:
            weight: Записанный вес
            progress: Информация о прогрессе
            
        Returns:
            str: Отформатированное сообщение
        """
        message = f"✅ Отлично! Я записал твой вес: {weight} кг.\n\n"
        
        if progress:
            if progress.total_weight_change < 0:
                message += f"📉 С начала ты уже сбросил {abs(progress.total_weight_change):.1f} кг "
            else:
                message += f"📈 С начала ты уже набрал {progress.total_weight_change:.1f} кг "
                
            message += f"({abs(progress.weight_change_percentage):.1f}% от начального веса)\n\n"
            
            message += f"🎯 До целевого веса осталось: {abs(progress.remaining_to_goal):.1f} кг\n"
            message += f"📊 Ты выполнил {progress.goal_completion_percentage:.1f}% своей цели!\n\n"
            
        message += "Продолжай отслеживать прогресс регулярно! 💪"
        
        return message
        
    def format_water_recorded_message(self, amount: float, ml_amount: float, status: Optional[Dict[str, Any]] = None) -> str:
        """
        Форматирует сообщение о записи потребления воды
        
        Args:
            amount: Количество стаканов
            ml_amount: Количество в миллилитрах
            status: Статус трекинга
            
        Returns:
            str: Отформатированное сообщение
        """
        message = f"💧 Отлично! Я записал потребление воды: {amount} стаканов (~{ml_amount} мл).\n\n"
        
        if status:
            message += f"Сегодня ты выпил всего: {status.current_water_intake} мл\n"
            message += f"Это {status.water_percentage:.1f}% от дневной цели в {status.water_goal} мл\n\n"
            
        message += "Продолжай в том же духе! Регулярное потребление воды помогает контролировать голод и улучшает общее самочувствие."
        
        return message
    
    def format_compliance_message(self, meal_type: str, status: str, compliance_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Форматирует сообщение о соблюдении режима питания
        
        Args:
            meal_type: Тип приема пищи
            status: Статус соблюдения
            compliance_data: Общие данные о соблюдении
            
        Returns:
            str: Отформатированное сообщение
        """
        meal_type_display = meal_type.capitalize()
        
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
            
            # Добавляем мотивацию
            if compliance_data["overall_score"] >= 80:
                message += "\n\n👍 Отличная работа! Продолжай в том же духе."
            elif compliance_data["overall_score"] >= 50:
                message += "\n\n👍 Хороший результат! Старайся следовать плану."
            else:
                message += "\n\n💪 Не сдавайся! Каждый день - это новая возможность."
                
        return message
    
    def format_stats_message(self, weight_progress: Optional[Dict[str, Any]], today_status: Optional[Dict[str, Any]], compliance_data: Optional[Dict[str, Any]]) -> str:
        """
        Форматирует сообщение со статистикой
        
        Args:
            weight_progress: Прогресс по весу
            today_status: Статус трекинга на сегодня
            compliance_data: Данные о соблюдении плана
            
        Returns:
            str: Отформатированное сообщение
        """
        message = f"*📊 СТАТИСТИКА И ПРОГРЕСС*\n\n"
        
        # Прогресс по весу
        if weight_progress:
            message += f"*⚖️ Прогресс по весу:*\n"
            message += f"• Начальный вес: {weight_progress.start_weight} кг\n"
            message += f"• Текущий вес: {weight_progress.current_weight} кг\n"
            message += f"• Целевой вес: {weight_progress.target_weight} кг\n\n"
            
            if weight_progress.total_weight_change < 0:
                message += f"• Изменение: -{abs(weight_progress.total_weight_change):.1f} кг 👍\n"
            elif weight_progress.total_weight_change > 0:
                message += f"• Изменение: +{weight_progress.total_weight_change:.1f} кг\n"
            else:
                message += "• Изменение: 0 кг (вес стабилен)\n"
                
            message += f"• Осталось до цели: {abs(weight_progress.remaining_to_goal):.1f} кг\n"
            message += f"• Процент выполнения: {weight_progress.goal_completion_percentage:.1f}%\n\n"
            
        # Статус воды на сегодня
        if today_status:
            message += f"*💧 Потребление воды сегодня:*\n"
            message += f"• Выпито: {today_status.current_water_intake} мл\n"
            message += f"• Цель: {today_status.water_goal} мл\n"
            message += f"• Выполнено: {today_status.water_percentage:.1f}%\n\n"
            
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
                meal_type_ru = self._translate_meal_type(meal_type)
                emoji = emoji_map.get(status, "❓")
                message += f"• {meal_type_ru}: {emoji}\n"
                
            if "overall_score" in compliance_data:
                message += f"\nОбщее соблюдение: {compliance_data['overall_score']:.1f}%\n\n"
                
        # Добавляем мотивационное сообщение
        message += "💪 *Продолжай в том же духе!* Ты на пути к своей цели."
        
        return message
        
    def format_update_success_message(self, comment: str, updated_day_keys: List[str]) -> str:
        """
        Форматирует сообщение об успешном обновлении плана
        
        Args:
            comment: Комментарий по обновлению
            updated_day_keys: Список ключей обновленных дней
            
        Returns:
            str: Отформатированное сообщение
        """
        message = f"✅ *План питания обновлен*\n\n{comment}\n"
        
        for date_str in updated_day_keys:
            try:
                day_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                day_name = self._translate_day_name(day_date.strftime("%A"))
                message += f"\nОбновлено меню на *{day_name}, {day_date.strftime('%d.%m.%Y')}*"
            except:
                message += f"\nОбновлено меню на {date_str}"
                
        return message
    
    def _translate_day_name(self, day_name: str) -> str:
        """
        Переводит название дня недели
        
        Args:
            day_name: Название дня на английском
            
        Returns:
            str: Переведенное название
        """
        translations = {
            "Monday": "Понедельник",
            "Tuesday": "Вторник",
            "Wednesday": "Среда",
            "Thursday": "Четверг",
            "Friday": "Пятница",
            "Saturday": "Суббота",
            "Sunday": "Воскресенье"
        }
        return translations.get(day_name, day_name)
        
    def _translate_meal_type(self, meal_type: str) -> str:
        """
        Переводит тип приема пищи
        
        Args:
            meal_type: Тип приема пищи на английском
            
        Returns:
            str: Тип приема пищи на русском
        """
        translations = {
            "breakfast": "Завтрак",
            "lunch": "Обед",
            "dinner": "Ужин",
            "snack": "Перекус"
        }
        return translations.get(meal_type, meal_type.capitalize())