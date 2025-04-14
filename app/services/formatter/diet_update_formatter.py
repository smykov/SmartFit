# app/services/formatter/diet_update_formatter.py
from typing import Dict, Any, Optional, List

from app.constants.localization_keys import LocalizationKeys as LK
from app.services.formatter.base_formatter import BaseFormatter
from app.services.localization.localization_interface import ILocalizationService
from app.utils.date_helper import DateHelper


class DietUpdateFormatter(BaseFormatter):
    """Класс для форматирования обновлений плана диеты"""

    def __init__(self, localization_service: ILocalizationService):
        """
        Инициализация форматтера обновлений

        Args:
            localization_service: Сервис локализации сообщений
        """
        super().__init__(localization_service)

    def format_update_success_message(self, comment: str, updated_day_keys: List[str], lang: Optional[str] = None) -> str:
        """
        Форматирует сообщение об успешном обновлении плана

        Args:
            comment: Комментарий по обновлению
            updated_day_keys: Список ключей обновленных дней
            lang: Код языка

        Returns:
            str: Отформатированное сообщение
        """
        try:
            # Создаем базовое сообщение об успешном обновлении
            message = self.get_localized_message(
                LK.Diet.Update.SUCCESS_HEADER,
                lang,
                comment=comment
            )

            # Добавляем информацию о каждом обновленном дне
            for date_str in updated_day_keys:
                try:
                    # Обработка даты или дня недели
                    is_date_format = "-" in date_str  # Проверка на формат даты YYYY-MM-DD

                    if is_date_format:
                        # Преобразуем строку даты в объект date
                        day_date = DateHelper.parse_date_string(date_str)
                        day_name = self.get_localized_message(
                            LK.Common.WEEKDAY_NAMES.format(day_date.strftime("%A").lower()),
                            lang
                        )
                        date_format = self.get_localized_message(LK.Common.DAY_FORMAT, lang)
                        date_formatted = DateHelper.format_date(day_date, date_format)
                        message += self.get_localized_message(
                            LK.Diet.Update.DAY_UPDATED_WITH_DATE,
                            lang,
                            day_name=day_name,
                            date_formatted=date_formatted
                        )
                    else:
                        # Это день недели
                        day_name = self.get_localized_message(
                            LK.Common.WEEKDAY_NAMES.format(date_str),
                            lang
                        ).capitalize()
                        message += self.get_localized_message(
                            LK.Diet.Update.DAY_UPDATED,
                            lang,
                            day_name=day_name
                        )

                except ValueError:
                    # В случае ошибки просто добавляем как есть
                    message += self.get_localized_message(
                        LK.Diet.Update.UNKNOWN_DAY_UPDATED,
                        lang,
                        date_str=date_str
                    )

            return self.format_for_whatsapp(message)

        except Exception as e:
            return self.handle_exception(
                e,
                "Error formatting update success message",
                LK.Diet.Update.FORMATTING_ERROR,
                lang
            )

    def prepare_diet_update_request(self, update_request: str, lang: Optional[str] = None) -> Dict[str, Any]:
        """
        Подготавливает запрос на обновление плана диеты

        Args:
            update_request: Текст запроса на обновление
            lang: Код языка

        Returns:
            Dict[str, Any]: Подготовленные данные запроса
        """
        try:
            # Выполняем базовую обработку запроса
            # Реальная логика будет зависеть от требований приложения
            # и будет реализована в конкретных сервисах

            # Возвращаем подготовленный запрос
            return {
                "original_request": update_request,
                "language": lang,
                "timestamp": DateHelper.get_current_datetime().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error preparing diet update request: {str(e)}")
            # Возвращаем базовый запрос
            return {
                "original_request": update_request,
                "error": str(e)
            }

    def format_no_updates_message(self, lang: Optional[str] = None) -> str:
        """
        Возвращает сообщение о том, что не удалось внести обновления

        Args:
            lang: Код языка

        Returns:
            str: Сообщение об отсутствии обновлений
        """
        return self.get_localized_message(LK.Diet.Update.NO_UPDATES, lang)
