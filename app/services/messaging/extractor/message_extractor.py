from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple


class MessageExtractor(ABC):
    """Абстрактный класс для извлечения данных из сообщений разных мессенджеров"""

    @abstractmethod
    def extract_message_data(self, body: Dict[str, Any]) -> Tuple[
        Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Извлекает данные из входящего сообщения

        Args:
            body: Данные сообщения

        Returns:
            Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
            (идентификатор отправителя, текст сообщения, тип сообщения, ID сообщения)
        """
        pass