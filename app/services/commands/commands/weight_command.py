# app/services/commands/commands/weight_command.py
import re
from typing import Dict, Any, Optional

from app.constants.localization_keys import LocalizationKeys as LK
from app.services.commands.base_command import BaseCommand


class WeightCommand(BaseCommand):
    """
    Команда для записи веса пользователя
    """
    # TODO переделать на форматтер все сообщения

    async def can_execute(self, user_id: str) -> bool:
        """
        Проверка возможности выполнения команды

        Args:
            user_id: ID пользователя

        Returns:
            bool: Возможность выполнения команды
        """
        return True

    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды записи веса

        Args:
            user_id: ID пользователя
            params: Параметры команды (содержит текст сообщения)

        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        self.logger.info(f"Processing weight tracking command: params: {params}")

        # Получаем язык пользователя
        lang = None
        if hasattr(self, 'localization_service') and self.localization_service:
            lang = await self.localization_service.get_user_language(user_id)

        if not params or 'params' not in params:
            return {
                "success": False,
                "message": self.get_localized_message(LK.Commands.Weight.INVALID_FORMAT, lang)
            }

        try:
            weight = float(params['params'][0].lower().strip().replace(',', '.'))

            # Проверка диапазона веса
            if weight < 30 or weight > 300:
                self.logger.error(f"Error recording weight tracking: WEIGHT_OUT_OF_RANGE '{weight}'")
                return {
                    "success": False,
                    "message": self.get_localized_message(LK.Commands.Weight.OUT_OF_RANGE, lang)
                }

            # Запись веса через типизированный сервис трекинга
            await self.tracking_service.record_weight(user_id, weight)

            # Получаем прогресс
            progress = await self.tracking_service.calculate_weight_progress(user_id)

            # Определяем контекст для форматирования сообщения (похудел/набрал)
            context = None
            if progress and progress.total_weight_change < 0:
                context = 'lost'
                change = abs(progress.total_weight_change)
            elif progress and progress.total_weight_change > 0:
                context = 'gained'
                change = progress.total_weight_change
            else:
                change = 0

            # Форматируем сообщение о записи веса
            message = self.get_localized_message(
                LK.Commands.Weight.RECORDED,
                lang,
                weight=weight
            )

            if progress:
                # Добавляем информацию о прогрессе
                progress_message = self.get_localized_message(
                    LK.Tracking.Weight.PROGRESS,
                    lang,
                    context=context,
                    weight_change=change,
                    percentage=progress.goal_completion_percentage
                )

                goal_message = self.get_localized_message(
                    LK.Tracking.Weight.GOAL_REMAINING,
                    lang,
                    remaining=abs(progress.remaining_to_goal),
                    target=progress.target_weight
                )

                message += f"\n\n{progress_message}\n{goal_message}"

                # Добавляем информацию о процентном выполнении цели
                message += "\n" + self.get_localized_message(
                    LK.Tracking.Weight.GOAL_PERCENTAGE,
                    lang,
                    percentage=progress.goal_completion_percentage
                )

            return {
                "success": True,
                "message": message
            }

        except ValueError:
            return {
                "success": False,
                "message": self.get_localized_message(LK.Commands.Weight.INVALID_VALUE, lang)
            }
        except Exception as e:
            # Логирование ошибки
            self.logger.error(f"Error recording weight: {str(e)}")
            return {
                "success": False,
                "message": self.get_localized_message(LK.Commands.Weight.ERROR, lang)
            }

    def get_error_message(self) -> str:
        """
        Получение сообщения об ошибке

        Returns:
            str: Сообщение об ошибке
        """
        return self.get_localized_message(LK.Commands.Weight.INVALID_FORMAT)