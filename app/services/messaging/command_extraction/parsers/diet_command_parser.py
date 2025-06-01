# app/services/messaging/command_extraction/parsers/diet_command_parser.py
import re
from typing import Optional, Dict, Any
from app.models.command import Command, CommandSource
from app.services.messaging.command_extraction.parsers.base_command_parser import BaseCommandParser
from app.services.messaging.command_extraction.parsers.date_parser import DateParser, DateParsingError
from app.services.localization.localization_interface import ILocalizationService
from app.constants.localization_keys import LocalizationKeys as LK
import logging


class DietCommandParser(BaseCommandParser):
    """
    Парсер для команд показа плана питания.
    Поддерживает различные форматы: план, план на понедельник, план на 28 мая, план на неделю и т.д.
    Следует принципам SOLID: SRP, OCP, DIP
    """

    def __init__(self, localization_service: ILocalizationService):
        """
        Инициализация парсера команд диеты

        Args:
            localization_service: Сервис локализации
        """
        self.localization_service = localization_service
        self.logger = logging.getLogger(self.__class__.__name__)

        # Базовые паттерны (расширяемые через локализацию)
        self._base_patterns = {
            'simple_diet': r'^(план|диета|меню|план питания)',
            'diet_with_period': r'^(план|диета|меню|план питания)\s+на\s+(.+)',
            'full_diet': r'^(полный\s+план|полное\s+меню|план\s+на\s+неделю|недельный\s+план)'
        }

    def parse(self, message: str, context: Dict[str, Any] = None) -> Optional[Command]:
        """
        Парсит сообщение на предмет команды показа плана питания

        Args:
            message: Текст сообщения
            context: Контекст пользователя (часовой пояс, язык и т.д.)

        Returns:
            Optional[Command]: Команда или None если не найдена
        """
        if not message or not isinstance(message, str):
            return None

        message = message.strip()
        if not message:
            return None

        # Получаем язык и часовой пояс из контекста
        language = context.get('language', 'ru') if context else 'ru'
        user_timezone = context.get('timezone') if context else None

        try:
            # Создаем парсер дат с контекстом пользователя
            date_parser = DateParser(user_timezone, language)

            # 1. Проверяем полный план на неделю
            if self._is_full_diet_request(message, language):
                return self._create_diet_command(full=True)

            # 2. Проверяем простой план без параметров
            if self._is_simple_diet_request(message, language):
                return self._create_diet_command()

            # 3. Проверяем план с указанием периода
            period_match = self._extract_period(message, language)
            if period_match:
                return self._parse_diet_with_period(period_match, date_parser, language)

        except DateParsingError as e:
            self.logger.warning(f"Date parsing error: {str(e)}")
            # Возвращаем команду с ошибкой для обработки в executor
            return Command(
                command_type="diet_error",
                params={"error_message": str(e)},
                priority=0,
                source=CommandSource.PATTERN_MATCH,
                confidence=0.9
            )
        except Exception as e:
            self.logger.error(f"Error parsing diet command: {str(e)}")

        return None

    def get_command_type(self) -> str:
        """Возвращает тип команды"""
        return "diet"

    def _is_simple_diet_request(self, message: str, language: str) -> bool:
        """Проверяет, является ли сообщение простым запросом плана"""
        terms = self._get_localized_diet_terms(language)
        pattern = r'^(' + '|'.join(re.escape(term) for term in terms) + r')$'
        return bool(re.match(pattern, message, re.IGNORECASE))

    def _is_full_diet_request(self, message: str, language: str) -> bool:
        """Проверяет, является ли сообщение запросом полного плана"""
        full_terms = self._get_localized_full_diet_terms(language)
        pattern = r'^(' + '|'.join(re.escape(term) for term in full_terms) + r')$'
        return bool(re.match(pattern, message, re.IGNORECASE))

    def _extract_period(self, message: str, language: str) -> Optional[str]:
        """Извлекает период из сообщения"""
        terms = self._get_localized_diet_terms(language)
        preposition = self._get_localized_preposition(language)

        pattern = r'^(' + '|'.join(re.escape(term) for term in terms) + r')\s+' + preposition + r'\s+(.+)$'
        match = re.match(pattern, message, re.IGNORECASE)

        if match:
            return match.group(2).strip()
        return None

    def _parse_diet_with_period(self, period: str, date_parser: DateParser, language: str) -> Optional[Command]:
        """
        Парсит команду с указанием периода

        Args:
            period: Период (завтра, понедельник, 28 мая и т.д.)
            date_parser: Парсер дат
            language: Язык пользователя

        Returns:
            Optional[Command]: Команда или None
        """
        period_lower = period.lower().strip()

        # 1. Проверяем относительные даты (завтра, вчера, сегодня)
        relative_date = date_parser.parse_relative_date(period_lower)
        if relative_date:
            # Особая обработка "сегодня"
            if period_lower in self._get_today_terms(language):
                return self._create_diet_command()
            return self._create_diet_command(day=relative_date.isoformat())

        # 2. Проверяем дни недели
        weekday_result = date_parser.parse_weekday(period_lower)
        if weekday_result:
            target_date, weekday_name = weekday_result
            return self._create_diet_command(day=weekday_name)

        # 3. Проверяем абсолютные даты
        absolute_date = date_parser.parse_absolute_date(period_lower)
        if absolute_date:
            return self._create_diet_command(day=absolute_date.isoformat())

        # 4. Проверяем специальные термины (неделя, месяц и т.д.)
        if self._is_week_term(period_lower, language):
            return self._create_diet_command(full=True)

        return None

    def _create_diet_command(self, day: Optional[str] = None, full: bool = False) -> Command:
        """
        Создает команду показа плана питания

        Args:
            day: День (дата в ISO формате или день недели)
            full: Показать полный план на неделю

        Returns:
            Command: Команда показа плана
        """
        params = {}

        if day:
            params['day'] = day

        if full:
            params['full'] = True

        return Command(
            command_type="show_diet_plan",
            params=params,
            priority=5,  # Высокий приоритет для команд показа
            source=CommandSource.PATTERN_MATCH,
            confidence=0.95
        )

    def _get_localized_diet_terms(self, language: str) -> list:
        """Получает локализованные термины для команд диеты"""
        # В реальной реализации используем localization_service
        # Пока захардкодим основные термины
        terms_map = {
            'ru': ['план', 'диета', 'меню', 'план питания', 'рацион'],
            'en': ['plan', 'diet', 'menu', 'meal plan', 'nutrition plan'],
            'es': ['plan', 'dieta', 'menú', 'plan de comidas', 'plan nutricional']
        }
        return terms_map.get(language, terms_map['ru'])

    def _get_localized_full_diet_terms(self, language: str) -> list:
        """Получает локализованные термины для полного плана"""
        terms_map = {
            'ru': ['полный план', 'полное меню', 'план на неделю', 'недельный план', 'весь план'],
            'en': ['full plan', 'complete menu', 'weekly plan', 'full menu', 'entire plan'],
            'es': ['plan completo', 'menú completo', 'plan semanal', 'plan completo']
        }
        return terms_map.get(language, terms_map['ru'])

    def _get_localized_preposition(self, language: str) -> str:
        """Получает локализованный предлог"""
        prepositions = {
            'ru': 'на',
            'en': 'for',
            'es': 'para'
        }
        return prepositions.get(language, 'на')

    def _get_today_terms(self, language: str) -> list:
        """ИСПРАВЛЕНО: Получает термины для обозначения 'сегодня'"""
        today_terms = {
            'ru': ['сегодня'],
            'en': ['today'],
            'es': ['hoy']
        }
        return today_terms.get(language, today_terms['ru'])

    def _is_week_term(self, term: str, language: str) -> bool:
        """Проверяет, является ли термин обозначением недели"""
        week_terms = {
            'ru': ['неделю', 'всю неделю', 'целую неделю'],
            'en': ['week', 'whole week', 'entire week'],
            'es': ['semana', 'toda la semana', 'semana completa']
        }
        terms = week_terms.get(language, week_terms['ru'])
        return term in terms
