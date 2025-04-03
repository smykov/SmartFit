# app/services/diet/base_service.py

from abc import ABC
import logging


class BaseDietService(ABC):
    """Базовый абстрактный класс для всех сервисов, связанных с диетами"""

    def __init__(self):
        """Инициализация сервиса"""
        self.logger = logging.getLogger(self.__class__.__name__)