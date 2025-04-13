from typing import Dict, Any, Optional
import importlib
import os
from pathlib import Path

from app.localization.base import LanguageBase


class LocalizationRegistry:
    """Реестр всех доступных локализаций"""

    def __init__(self, default_language: str = 'en'):
        """
        Инициализация реестра

        Args:
            default_language: Код языка по умолчанию
        """
        self.languages = {}
        self.default_language = default_language
        self._cache = {}  # Кэш переведенных строк

    def register_language(self, code: str, language: LanguageBase):
        """
        Регистрирует язык в реестре

        Args:
            code: Код языка (en, ru, es)
            language: Экземпляр класса языка
        """
        self.languages[code] = language

    def get(self, key: str, lang: Optional[str] = None, **params) -> str:
        """
        Получает локализованную строку

        Args:
            key: Ключ строки в формате 'module.key'
            lang: Код языка (если None, используется язык по умолчанию)
            **params: Параметры для форматирования

        Returns:
            str: Локализованная строка
        """
        # Если параметры не указаны, используем кэш
        cache_key = f"{lang or self.default_language}:{key}"
        if not params and cache_key in self._cache:
            return self._cache[cache_key]

        # Определяем язык
        language_code = lang or self.default_language

        # Если запрошенного языка нет, используем язык по умолчанию
        if language_code not in self.languages:
            language_code = self.default_language

        # Получаем строку
        result = self.languages[language_code].get(key, **params)

        # Если строка не найдена и язык не по умолчанию,
        # пробуем получить строку из языка по умолчанию
        if result == key and language_code != self.default_language:
            result = self.languages[self.default_language].get(key, **params)

        # Добавляем в кэш только если нет параметров
        if not params:
            self._cache[cache_key] = result

        return result

    def load_languages(self):
        """Загружает все доступные языки из модуля languages"""
        languages_dir = Path(__file__).parent / 'languages'

        # Проверяем, что директория существует
        if not languages_dir.exists() or not languages_dir.is_dir():
            raise ValueError(f"Languages directory not found: {languages_dir}")

        loaded_languages = 0

        for lang_dir in languages_dir.iterdir():
            if lang_dir.is_dir() and not lang_dir.name.startswith('__'):
                lang_code = lang_dir.name

                try:
                    lang_module = importlib.import_module(f"app.localization.languages.{lang_code}")

                    if hasattr(lang_module, 'language'):
                        self.register_language(lang_code, lang_module.language)
                        loaded_languages += 1
                    else:
                        print(f"Warning: Language module '{lang_code}' has no 'language' attribute")
                except (ImportError, AttributeError) as e:
                    print(f"Error loading language '{lang_code}': {e}")

        print(f"Loaded {loaded_languages} languages")


# Создаем глобальный экземпляр реестра
registry = LocalizationRegistry(default_language='en')

# Загружаем все доступные языки
registry.load_languages()


def get_message(key: str, lang: Optional[str] = None, **params) -> str:
    """
    Получает локализованное сообщение (функция-хелпер)

    Args:
        key: Ключ сообщения
        lang: Код языка
        **params: Параметры для форматирования

    Returns:
        str: Локализованное сообщение
    """
    return registry.get(key, lang, **params)