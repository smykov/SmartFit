from typing import Dict, Any, Optional, List, Callable
import re


class LocalizationString:
    """Класс для работы с локализованными строками, поддерживающий плюральные формы"""

    def __init__(self, value: str | Dict[str, str], plural_forms: Optional[Dict[str, str]] = None,
                 context_variants: Optional[Dict[str, str]] = None):
        """
        Инициализация локализованной строки

        Args:
            value: Базовое значение строки
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
        # Проверяем наличие параметра count для плюральных форм
        if 'count' in params and self.plural_forms:
            count = params['count']
            form = self._get_plural_form(count)
            if form in self.plural_forms:
                return self.plural_forms[form].format(**params)

        # Проверяем наличие параметра context для контекстных вариантов
        if 'context' in params and self.context_variants:
            context = params['context']
            if context in self.context_variants:
                return self.context_variants[context].format(**params)

        if 'style' in params:
            from app.localization.formats import StringUtils
            return StringUtils.apply_style(self.value.format(**params), params['style'])

        # Базовое форматирование
        return self.value.format(**params)

    # В классе LocalizationString:
    def _get_plural_form(self, count: int, lang: str = 'en') -> str:
        """
        Определяет плюральную форму на основе класса PluralRule
        """
        from app.localization.formats import PluralRule
        return PluralRule.get_plural_form(count, lang)


class LocalizationModule:
    """Базовый класс для модуля локализации"""

    def __init__(self, strings: Dict[str, LocalizationString]):
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
            key: Ключ строки
            **params: Параметры для форматирования

        Returns:
            str: Локализованная строка
        """
        if key in self.strings:
            return self.strings[key].format(**params)
        return key


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
            return self.modules[module_name].get(string_key, **params)
        return key