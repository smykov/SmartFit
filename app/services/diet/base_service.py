# app/services/diet/base_service.py

import logging
from abc import ABC
from typing import Optional, Dict, Any


class BaseDietService(ABC):
    """Базовый абстрактный класс для всех сервисов, связанных с диетами"""

    def __init__(self):
        """Инициализация сервиса"""
        self.logger = logging.getLogger(self.__class__.__name__)


    async def get_diet_plan_by_id(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает план диеты по его ID

        Args:
            plan_id: ID плана диеты

        Returns:
            Optional[Dict[str, Any]]: План диеты или None, если план не найден
        """
        pass