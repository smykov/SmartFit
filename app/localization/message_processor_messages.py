from datetime import datetime
from typing import List


class MessageProcessorMessages:
    """Класс с локализованными сообщениями для сервиса обработки сообщений"""

    # Общие сообщения
    NO_DIET_PLAN = "У тебя пока нет активного плана питания. Напиши 'диета' для создания нового плана."
    NO_PENDING_DIET_PLAN = "У тебя нет плана питания, ожидающего согласования. Напиши 'диета' для создания нового плана."
    UPDATE_FAILED = "К сожалению, не удалось обновить план питания. Попробуй позже."
    UPDATING_PLAN = "Я корректирую твой план питания согласно запросу. Это займет несколько секунд."

    # Сообщения для согласования плана питания
    PLAN_APPROVAL_SUCCESS = "✅ Отлично! Я начинаю готовить для вас полную версию плана питания с подробными рецептами и списком покупок. Это займет несколько минут."
    PLAN_APPROVAL_ERROR = "Извините, произошла ошибка при согласовании плана. Попробуйте позже."
    PLAN_DISAPPROVAL = "Понятно. Пожалуйста, уточните, что именно вы хотели бы изменить в плане. Например: 'Замени обед в понедельник' или 'Хочу больше белка'."

    # Сообщения для команд
    COMMAND_NOT_FOUND = "Извините, я не распознал команду. Напишите 'помощь' для просмотра списка доступных команд."
    PREREQUISITES_NOT_MET = "Не удалось выполнить команду. Сначала нужно {requirement}."

    # Сообщения для обработки ошибок
    ERROR_PROCESSING_MESSAGE = "Произошла ошибка при обработке вашего сообщения. Пожалуйста, попробуйте позже."
    UNKNOWN_COMMAND = "Неизвестная команда. Напишите 'помощь' для просмотра списка доступных команд."

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
                day_name = self.translate_day_name(day_date.strftime("%A"))
                message += f"\nОбновлено меню на *{day_name}, {day_date.strftime('%d.%m.%Y')}*"
            except:
                message += f"\nОбновлено меню на {date_str}"

        return message

    def translate_day_name(self, day_name: str) -> str:
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