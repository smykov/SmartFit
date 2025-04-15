from typing import Dict, Any, Optional, List, Callable, Union
import re
import logging
logger = logging.getLogger(__name__)

class LocalizationString:
    """Класс для работы с локализованными строками, поддерживающий плюральные формы"""

    def __init__(self, value: Union[str, Dict[str, Any]], plural_forms: Optional[Dict[str, str]] = None,
                 context_variants: Optional[Dict[str, str]] = None):
        """
        Инициализация локализованной строки

        Args:
            value: Базовое значение строки или словарь с вложенными значениями
            plural_forms: Словарь для плюральных форм {'one': '1 яблоко', 'few': '2 яблока', 'many': '5 яблок'}
            context_variants: Словарь для контекстных вариантов {'male': '...', 'female': '...'}
        """
        self.value = value
        self.plural_forms = plural_forms or {}
        self.context_variants = context_variants or {}

    def format(self, **params) -> str:
        """
        Форматирует строку с подстановкой параметров

        Args:
            **params: Параметры для форматирования

        Returns:
            str: Отформатированная строка
        """
        # Удаляем lang из параметров форматирования,
        # т.к. он нужен только для определения плюральных форм
        params_copy = params.copy()
        if 'lang' in params_copy:
            lang = params_copy.pop('lang')
        else:
            lang = 'en'

        # Дальше используем очищенные params_copy
        # и явно передаем lang, где это нужно

        # Проверяем наличие параметра count для плюральных форм
        if 'count' in params_copy and self.plural_forms:
            count = params_copy['count']
            form = self._get_plural_form(count, lang)
            if form in self.plural_forms:
                return self.plural_forms[form].format(**params_copy)

        # Проверяем наличие параметра context для контекстных вариантов
        if 'context' in params and self.context_variants:
            context = params['context']
            if context in self.context_variants:
                return self.context_variants[context].format(**params)

        # Если value - словарь, возвращаем его как есть (будет обработан в LanguageBase.get)
        if isinstance(self.value, dict):
            return self.value

        # Если это стиль, применяем его
        if 'style' in params:
            from app.localization.formats import StringUtils
            return StringUtils.apply_style(self.value.format(**params), params['style'])

        # Базовое форматирование
        return self.value.format(**params)

    def _get_plural_form(self, count: int, lang: str = 'en') -> str:
        """
        Определяет плюральную форму для числа

        Args:
            count: Число для определения формы
            lang: Код языка (en, ru, es)

        Returns:
            str: Название плюральной формы ('one', 'few', 'many', 'other')
        """
        from app.localization.formats import PluralRule
        return PluralRule.get_plural_form(count, lang)


class LocalizationModule:
    """Базовый класс для модуля локализации"""

    def __init__(self, strings: Dict[str, Any]):
        """
        Инициализация модуля локализации

        Args:
            strings: Словарь локализованных строк
        """
        self.strings = strings

    def get(self, key: str, **params) -> str:
        """
        Получает локализованную строку по ключу

        Args:
            key: Ключ строки (например, "water.recorded")
            **params: Параметры для форматирования

        Returns:
            str: Локализованная строка
        """
        parts = key.split('.')
        current = self.strings

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return key

        if isinstance(current, LocalizationString):
            return current.format(**params)
        elif isinstance(current, str):
            try:
                return current.format(**params)
            except:
                return current

        return key

    def _get_nested_value(self, obj: Dict[str, Any], path: str, **params) -> Any:
        """
        Получает значение из вложенного словаря по пути

        Args:
            obj: Словарь для поиска
            path: Путь к значению через точку
            **params: Параметры для форматирования

        Returns:
            Any: Найденное значение или путь, если значение не найдено
        """
        parts = path.split('.')
        current = obj

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return f"{path}"  # Значение не найдено

        # Если нашли LocalizationString, форматируем его
        if isinstance(current, LocalizationString):
            return current.format(**params)

        # Если нашли строку, форматируем ее
        if isinstance(current, str):
            try:
                return current.format(**params)
            except:
                return current

        return current


class LanguageBase:
    """Базовый класс для языка, содержащий все модули"""

    def __init__(self):
        """Инициализация с пустыми словарями модулей"""
        self.modules = {}

    def register_module(self, name: str, module: LocalizationModule):
        """
        Регистрирует модуль локализации

        Args:
            name: Имя модуля
            module: Модуль локализации
        """
        self.modules[name] = module

    def get(self, key: str, **params) -> str:
        """
        Получает локализованную строку по ключу

        Args:
            key: Ключ в формате 'module.key'
            **params: Параметры для форматирования

        Returns:
            str: Локализованная строка
        """
        parts = key.split('.', 1)
        if len(parts) < 2:
            return key

        module_name, string_key = parts

        if module_name in self.modules:
            result = self.modules[module_name].get(string_key, **params)

            # Если результат - словарь, это значит, что это вложенная структура
            if isinstance(result, dict):
                # Попробуем найти значение во вложенной структуре
                return f"[Nested dict found for {key}]"

            return result
        return key
