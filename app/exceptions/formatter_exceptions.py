# app/exceptions/formatter_exceptions.py

class FormatterException(Exception):
    """Базовое исключение для ошибок форматирования"""
    
    def __init__(self, message: str, formatter_name: str = None, additional_info: dict = None):
        """
        Инициализация исключения форматтера
        
        Args:
            message: Сообщение об ошибке
            formatter_name: Имя форматтера, где произошла ошибка
            additional_info: Дополнительная информация об ошибке
        """
        self.formatter_name = formatter_name
        self.additional_info = additional_info or {}
        super().__init__(message)
        
    def __str__(self):
        error_message = super().__str__()
        if self.formatter_name:
            error_message = f"[{self.formatter_name}] {error_message}"
            
        if self.additional_info:
            error_message = f"{error_message} - Additional info: {self.additional_info}"
            
        return error_message


class DietFormatterException(FormatterException):
    """Исключение для ошибок форматирования диеты"""
    
    def __init__(self, message: str, additional_info: dict = None):
        super().__init__(message, "DietFormatter", additional_info)


class ShoppingListFormatterException(FormatterException):
    """Исключение для ошибок форматирования списка покупок"""
    
    def __init__(self, message: str, additional_info: dict = None):
        super().__init__(message, "ShoppingListFormatter", additional_info)


class LocalizationException(FormatterException):
    """Исключение для ошибок локализации"""
    
    def __init__(self, message: str, key: str = None, lang: str = None, additional_info: dict = None):
        """
        Инициализация исключения локализации
        
        Args:
            message: Сообщение об ошибке
            key: Ключ локализации, который не удалось найти
            lang: Код языка
            additional_info: Дополнительная информация об ошибке
        """
        info = additional_info or {}
        if key:
            info["localization_key"] = key
        if lang:
            info["language"] = lang
            
        super().__init__(message, "LocalizationService", info)
