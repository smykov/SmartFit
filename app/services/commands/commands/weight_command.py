import re
from typing import Dict, Any, Optional

from app.services.commands.base_command import BaseCommand
from app.services.tracking.tracking_service import tracking_service


class WeightCommand(BaseCommand):
    """
    Команда для записи веса пользователя
    """
    async def can_execute(self, user_id: str) -> bool:
        """
        Проверка возможности выполнения команды
        
        Args:
            user_id: ID пользователя
        
        Returns:
            bool: Возможность выполнения команды
        """
        # Здесь можно добавить дополнительные проверки
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
        if not params or 'params' not in params:
            return {
                "success": False, 
                "message": self.messages.INVALID_WEIGHT_FORMAT
            }
        
        message_text = params['params'][0]
        
        # Используем регулярное выражение для извлечения веса
        weight_match = re.match(r'^вес\s+(\d+[.,]?\d*)$', message_text.lower())
        
        if not weight_match:
            return {
                "success": False, 
                "message": self.messages.INVALID_WEIGHT_FORMAT
            }
        
        try:
            weight = float(weight_match.group(1).replace(',', '.'))
            
            # Проверка диапазона веса
            if weight < 30 or weight > 300:
                return {
                    "success": False, 
                    "message": self.messages.WEIGHT_OUT_OF_RANGE
                }
            
            # Запись веса через трекинг-сервис
            await tracking_service.record_weight(user_id, weight)
            
            # Получаем прогресс
            progress = await tracking_service.calculate_weight_progress(user_id)
            
            # Форматируем сообщение о записи веса
            message = self.messages.format_weight_recorded_message(weight, progress)
            
            return {
                "success": True, 
                "message": message
            }
        
        except ValueError:
            return {
                "success": False, 
                "message": self.messages.INVALID_WEIGHT_VALUE
            }
        except Exception as e:
            # Логирование ошибки
            print(f"Ошибка при записи веса: {str(e)}")
            return {
                "success": False, 
                "message": "Произошла ошибка при записи веса. Попробуйте позже."
            }

    def get_error_message(self) -> str:
        """
        Получение сообщения об ошибке
        
        Returns:
            str: Сообщение об ошибке
        """
        return self.messages.INVALID_WEIGHT_FORMAT