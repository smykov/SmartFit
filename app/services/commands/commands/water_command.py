import re
from typing import Dict, Any, Optional
from app.services.commands.base_command import BaseCommand
from app.services.tracking.tracking_service import tracking_service

class WaterCommand(BaseCommand):
    """
    Команда для записи потребления воды
    """
    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение команды записи потребления воды
        
        Args:
            user_id: ID пользователя
            params: Параметры команды (содержит текст сообщения)
        
        Returns:
            Dict[str, Any]: Результат выполнения команды
        """
        if not params or 'params' not in params:
            return {
                "success": False, 
                "message": self.messages.INVALID_WATER_FORMAT
            }
        
        message_text = params['params'][0]
        
        # Используем регулярное выражение для извлечения количества стаканов
        water_match = re.match(r'^вода\s+(\d+[.,]?\d*)$', message_text.lower())
        
        if not water_match:
            return {
                "success": False, 
                "message": self.messages.INVALID_WATER_FORMAT
            }
        
        try:
            amount = float(water_match.group(1).replace(',', '.'))
            
            # Проверка диапазона потребления воды
            if amount < 0 or amount > 20:
                return {
                    "success": False, 
                    "message": self.messages.INVALID_WATER_VALUE
                }
            
            # Конвертируем стаканы в миллилитры (примерно 250 мл в стакане)
            ml_amount = amount * 250
            
            # Запись потребления воды через трекинг-сервис
            await tracking_service.record_water_intake(user_id, ml_amount)
            
            # Получаем статус трекинга
            status = await tracking_service.get_daily_status(user_id)
            
            # Форматируем сообщение о записи воды
            message = self.messages.format_water_recorded_message(amount, ml_amount, status)
            
            return {
                "success": True, 
                "message": message
            }
        
        except ValueError:
            return {
                "success": False, 
                "message": self.messages.INVALID_WATER_VALUE
            }
        except Exception as e:
            # Логирование ошибки
            print(f"Ошибка при записи потребления воды: {str(e)}")
            return {
                "success": False, 
                "message": "Произошла ошибка при записи потребления воды. Попробуйте позже."
            }

    def get_error_message(self) -> str:
        """
        Получение сообщения об ошибке
        
        Returns:
            str: Сообщение об ошибке
        """
        return self.messages.INVALID_WATER_FORMAT