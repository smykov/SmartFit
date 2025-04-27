# app/services/tracking/tracking_service.py
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, Tuple, List, Coroutine

import pytz

from app.db.interfaces.user_repository_interface import IUserRepository
from app.db.interfaces.weight_entry_repository_interface import IWeightEntryRepository
from app.db.interfaces.water_entry_repository_interface import IWaterEntryRepository
from app.db.interfaces.compliance_repository_interface import IComplianceRepository
from app.models.tracking import (
    DailyTrackingStatus,
    WeightGoalProgress, MealComplianceStatus
)
from app.services.tracking.tracking_service_interface import ITrackingService
from app.services.localization.localization_interface import ILocalizationService
from app.constants.localization_keys import LocalizationKeys as LK
from config import settings

logger = logging.getLogger(__name__)


class TrackingService(ITrackingService):
    """Сервис для работы с данными трекинга"""

    def __init__(
            self,
            user_repository: IUserRepository,
            weight_entry_repository: IWeightEntryRepository,
            water_entry_repository: IWaterEntryRepository,
            compliance_repository: IComplianceRepository,
            localization_service: ILocalizationService
    ):
        """
        Инициализация сервиса трекинга с использованием DI

        Args:
            user_repository: Репозиторий для работы с пользователями
            weight_entry_repository: Репозиторий для работы с записями веса
            water_entry_repository: Репозиторий для работы с записями потребления воды
            compliance_repository: Репозиторий для работы с записями соблюдения диеты
            localization_service: Сервис локализации для сообщений
        """
        self.user_repository = user_repository
        self.weight_entry_repository = weight_entry_repository
        self.water_entry_repository = water_entry_repository
        self.compliance_repository = compliance_repository
        self.localization_service = localization_service
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_localized_message(self, key: str, lang: Optional[str] = None, **params) -> str:
        """
        Получает локализованное сообщение из сервиса локализации

        Args:
            key: Ключ сообщения
            lang: Код языка (по умолчанию используется системный язык)
            **params: Параметры для форматирования

        Returns:
            str: Локализованное сообщение
        """
        if hasattr(self, 'localization_service') and self.localization_service:
            return self.localization_service.get_message(key, lang, **params)
        return key

    async def record_weight(self, user_id: str, weight: float, notes: str = None) -> bool:
        """
        Записывает вес пользователя

        Args:
            user_id: ID пользователя
            weight: Вес в кг
            notes: Дополнительные заметки

        Returns:
            bool: Результат операции
        """
        try:
            # Используем репозиторий записей веса
            entry_id = await self.weight_entry_repository.add_entry(user_id, weight, notes=notes)
            return entry_id is not None
        except Exception as e:
            logger.error(f"Error recording weight: {str(e)}")
            return False

    async def record_water_intake(self, user_id: str, amount: float) -> bool:
        """
        Записывает потребление воды

        Args:
            user_id: ID пользователя
            amount: Количество воды в мл

        Returns:
            bool: Результат операции
        """
        try:
            # Используем репозиторий записей потребления воды
            entry_id = await self.water_entry_repository.add_entry(user_id, amount)
            return entry_id is not None
        except Exception as e:
            logger.error(f"Error recording water intake: {str(e)}")
            return False

    async def record_meal_compliance(
            self,
            user_id: str,
            date_value: date,
            meal_type: str,
            status: MealComplianceStatus,
            notes: str = None,
            alternative_meal: str = None
    ) -> bool:
        """
        Записывает соблюдение режима питания

        Args:
            user_id: ID пользователя
            date_value: Дата
            meal_type: Тип приема пищи (breakfast, lunch, dinner, snack)
            status: Статус (followed, partially, substituted, skipped)
            notes: Дополнительные заметки
            alternative_meal: Альтернативное блюдо (если status=substituted)

        Returns:
            bool: Результат операции
        """
        try:
            # Записываем соблюдение режима питания
            compliance_id = await self.compliance_repository.add_meal_compliance(
                user_id, date_value, meal_type, status, notes, alternative_meal
            )

            # Обновляем общую статистику соблюдения плана питания за день
            await self.compliance_repository.update_daily_compliance(user_id, date_value)

            return compliance_id is not None
        except Exception as e:
            self.logger.error(f"Error recording meal compliance: {str(e)}")
            return False

    async def calculate_weight_progress(self, user_id: str) -> Optional[WeightGoalProgress]:
        """
        Рассчитывает прогресс в достижении цели по весу

        Args:
            user_id: ID пользователя

        Returns:
            Optional[WeightGoalProgress]: Прогресс или None в случае ошибки
        """
        try:
            # Получаем пользователя
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None

            # Проверяем наличие целевого веса
            if "target_weight" not in user or not user["target_weight"]:
                logger.error(f"Target weight not set for user {user_id}")
                return None

            # Проверяем наличие текущего веса
            if "current_weight" not in user or not user["current_weight"]:
                logger.error(f"Current weight not set for user {user_id}")
                return None

            # Получаем историю веса для определения начального веса
            weight_entries = await self.weight_entry_repository.get_entries_by_user(user_id)

            # Определяем начальный вес
            start_weight, start_date = self._get_start_weight(weight_entries)

            if not start_weight:
                # Если нет истории, используем текущий вес как начальный
                start_weight = user["current_weight"]

            # Рассчитываем прогресс
            progress = WeightGoalProgress.calculate(
                user_id=user_id,
                start_weight=start_weight,
                current_weight=user["current_weight"],
                target_weight=user["target_weight"]
            )

            return progress

        except Exception as e:
            logger.error(f"Error calculating weight progress: {str(e)}")
            return None

    async def get_daily_status(self, user_id: str, target_date: date = None) -> Optional[DailyTrackingStatus]:
        """
        Получает статус трекинга на конкретный день с учетом соблюдения плана

        Args:
            user_id: ID пользователя
            target_date: Дата для статуса (по умолчанию сегодня)

        Returns:
            Optional[DailyTrackingStatus]: Статус трекинга или None в случае ошибки
        """
        try:
            # Получаем пользователя
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None

            # Если дата не указана, используем сегодняшнюю
            if not target_date:
                target_date = datetime.now(pytz.timezone(settings.TIMEZONE)).date()
            # Преобразуем в строку
            # Проверяем, записан ли вес на указанную дату
            latest_weight = await self.weight_entry_repository.get_latest_entry(user_id)
            weight_recorded = False
            if latest_weight:
                latest_date = datetime.strptime(latest_weight.get("date", ""), "%Y-%m-%d").date()
                weight_recorded = latest_date == target_date

            # Получаем потребление воды на указанную дату
            current_water_intake = await self.water_entry_repository.get_daily_total(user_id, target_date)

            # Целевое потребление воды (2 литра по умолчанию)
            water_goal = 2000  # в мл

            # Получаем данные о соблюдении плана питания
            compliance_data = await self.compliance_repository.get_daily_compliance(user_id, target_date)
            meal_compliance = {}
            overall_compliance_score = 0

            if compliance_data:
                meal_compliance = compliance_data.get("meals", {})
                overall_compliance_score = compliance_data.get("overall_score", 0)

            # Создаем объект статуса
            status = DailyTrackingStatus(
                user_id=user_id,
                date=target_date,
                weight_recorded=weight_recorded,
                current_water_intake=current_water_intake,
                water_goal=water_goal,
                meal_compliance=meal_compliance,
                overall_compliance_score=overall_compliance_score
            )

            # Рассчитываем процент выполнения цели по воде
            status.calculate_water_percentage()

            return status

        except Exception as e:
            logger.error(f"Error getting daily status: {str(e)}")
            return None

    async def get_diet_compliance(self, user_id: str, date_value: date = None) -> Optional[Dict[str, Any]]:
        """
        Получает статистику соблюдения плана питания

        Args:
            user_id: ID пользователя
            date_value: Дата (если None, используется текущая дата)

        Returns:
            Optional[Dict[str, Any]]: Статистика соблюдения или None
        """
        try:
            # Если дата не указана, используем текущую
            if date_value is None:
                date_value = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Получаем запись о соблюдении через репозиторий
            return await self.compliance_repository.get_daily_compliance(user_id, date_value)

        except Exception as e:
            logger.error(f"Error getting diet compliance: {str(e)}")
            return None

    async def get_weight_history(
            self,
            user_id: str,
            start_date: date = None,
            end_date: date = None
    ) -> Optional[Dict[str, float]]:
        """
        Получает историю веса пользователя за период

        Args:
            user_id: ID пользователя
            start_date: Начальная дата периода
            end_date: Конечная дата периода

        Returns:
            Optional[Dict[str, float]]: История веса (дата: вес) или None в случае ошибки
        """
        try:
            # Получаем записи веса через репозиторий
            entries = await self.weight_entry_repository.get_entries_by_user(user_id, start_date, end_date)

            # Преобразуем в словарь {дата: вес}
            weight_history = {}
            for entry in entries:
                date_str = entry.get("date", "")
                weight = entry.get("weight", 0.0)
                if date_str and weight:
                    weight_history[date_str] = weight

            return weight_history

        except Exception as e:
            logger.error(f"Error getting weight history: {str(e)}")
            return None

    async def get_water_history(
            self,
            user_id: str,
            start_date: date = None,
            end_date: date = None
    ) -> Optional[Dict[str, float]]:
        """
        Получает историю потребления воды за период

        Args:
            user_id: ID пользователя
            start_date: Начальная дата периода
            end_date: Конечная дата периода

        Returns:
            Optional[Dict[str, float]]: История потребления воды (дата: объем) или None в случае ошибки
        """
        try:
            # Получаем записи о потреблении воды через репозиторий
            entries = await self.water_entry_repository.get_entries_by_user(user_id, start_date, end_date)

            # Создаем словарь для суммирования потребления воды по дням
            water_history = {}

            for entry in entries:
                date_str = entry.get("date", "")
                amount = entry.get("amount", 0.0)

                if date_str:
                    if date_str in water_history:
                        water_history[date_str] += amount
                    else:
                        water_history[date_str] = amount

            return water_history

        except Exception as e:
            logger.error(f"Error getting water history: {str(e)}")
            return None

    async def generate_weekly_report(self, user_id: str) -> None | Coroutine[Any, Any, str] | str:
        """
        Генерирует еженедельный отчет о прогрессе

        Args:
            user_id: ID пользователя

        Returns:
            Optional[str]: Текст отчета или None в случае ошибки
        """
        # Получаем язык пользователя
        lang = None
        if hasattr(self, 'localization_service') and self.localization_service:
            lang = await self.localization_service.get_user_language(user_id)
        try:
            # Получаем пользователя
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None


            # Получаем текущую дату
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Получаем дату неделю назад
            week_ago = today - timedelta(days=7)

            # Получаем историю веса за неделю
            weight_history = await self.get_weight_history(user_id, week_ago, today)

            # Получаем историю потребления воды за неделю
            water_history = await self.get_water_history(user_id, week_ago, today)

            # Рассчитываем прогресс по весу
            weight_progress = await self.calculate_weight_progress(user_id)
            # Возвращаем локализованное сообщение ошибки
            return self._format_weekly_report(user, weight_history, water_history, weight_progress)

        except Exception as e:
            self.logger.error(f"Error generating weekly report: {str(e)}")
            return self.get_localized_message(LK.Tracking.Stats.REPORT_ERROR, lang)

    def _get_start_weight(self, weight_entries: List[Dict[str, Any]]) -> Tuple[Optional[float], Optional[date]]:
        """
        Определяет начальный вес пользователя из истории

        Args:
            weight_entries: Список записей веса

        Returns:
            Tuple[Optional[float], Optional[date]]: (начальный вес, дата начального веса)
        """
        try:
            if not weight_entries:
                return None, None

            # Сортируем записи по дате (от ранних к поздним)
            sorted_entries = sorted(
                weight_entries,
                key=lambda entry: entry.get("date", "")
            )

            # Берем самую раннюю запись
            earliest_entry = sorted_entries[0]

            start_weight = earliest_entry.get("weight")
            start_date_str = earliest_entry.get("date")

            if not start_weight or not start_date_str:
                return None, None

            # Преобразуем строку даты в объект date
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                start_date = None

            return start_weight, start_date

        except Exception as e:
            logger.error(f"Error getting start weight: {str(e)}")
            return None, None

    async def _format_weekly_report(
            self,
            user: Dict[str, Any],
            weight_history: Dict[str, float],
            water_history: Dict[str, float],
            weight_progress: Optional[WeightGoalProgress]
    ) -> str:
        """
        Форматирует еженедельный отчет

        Args:
            user: Данные пользователя
            weight_history: История веса за неделю
            water_history: История потребления воды за неделю
            weight_progress: Прогресс по весу

        Returns:
            str: Отформатированный отчет
        """
        # TODO вынести форматирование в отдельный сервис форматирования в будущем
        try:
            # Получаем язык пользователя, если доступен локализационный сервис
            lang = None
            if hasattr(self, 'localization_service') and self.localization_service:
                lang = await self.localization_service.get_user_language(user.get('id'))

            report = self.get_localized_message(
                LK.Tracking.Stats.WEEKLY_REPORT_HEADER,
                lang,
                user_name=user.get('name', self.get_localized_message(LK.Common.USER, lang))
            )

            # Анализ веса
            if weight_history:
                # Определяем начальный и конечный вес за период
                dates = sorted(weight_history.keys())
                first_weight = weight_history[dates[0]]
                last_weight = weight_history[dates[-1]] if len(dates) > 1 else first_weight

                weight_change = last_weight - first_weight

                report += self.get_localized_message(LK.Tracking.Stats.WEIGHT_SECTION, lang)
                report += self.get_localized_message(
                    LK.Tracking.Stats.WEIGHT_INITIAL,
                    lang,
                    weight=first_weight,
                    date=dates[0]
                )
                report += self.get_localized_message(
                    LK.Tracking.Stats.WEIGHT_CURRENT,
                    lang,
                    weight=last_weight,
                    date=dates[-1]
                )

                if weight_change < 0:
                    report += self.get_localized_message(
                        LK.Tracking.Stats.WEIGHT_CHANGE_NEGATIVE,
                        lang,
                        change=abs(weight_change)
                    )
                elif weight_change > 0:
                    report += self.get_localized_message(
                        LK.Tracking.Stats.WEIGHT_CHANGE_POSITIVE,
                        lang,
                        change=weight_change
                    )
                else:
                    report += self.get_localized_message(LK.Tracking.Stats.WEIGHT_CHANGE_NEUTRAL, lang)
            else:
                report += self.get_localized_message(LK.Tracking.Stats.WEIGHT_NO_DATA, lang)

            report += "\n"

            # Анализ потребления воды
            if water_history:
                total_water = sum(water_history.values())
                avg_water = total_water / len(water_history)
                days_tracked = len(water_history)

                report += self.get_localized_message(LK.Tracking.Stats.WATER_SECTION, lang)
                report += self.get_localized_message(
                    LK.Tracking.Stats.WATER_DAYS_TRACKED,
                    lang,
                    days=days_tracked
                )
                report += self.get_localized_message(
                    LK.Tracking.Stats.WATER_AVERAGE,
                    lang,
                    avg=avg_water / 1000
                )

                if avg_water >= 2000:
                    report += self.get_localized_message(LK.Tracking.Stats.WATER_EXCELLENT, lang)
                elif avg_water >= 1500:
                    report += self.get_localized_message(LK.Tracking.Stats.WATER_GOOD, lang)
                else:
                    report += self.get_localized_message(LK.Tracking.Stats.WATER_INSUFFICIENT, lang)
            else:
                report += self.get_localized_message(LK.Tracking.Stats.WATER_NO_DATA, lang)

            report += "\n"

            # Прогресс к цели
            if weight_progress:
                report += self.get_localized_message(LK.Tracking.Stats.GOAL_SECTION, lang)
                report += self.get_localized_message(
                    LK.Tracking.Stats.GOAL_TARGET,
                    lang,
                    target=weight_progress.target_weight
                )
                report += self.get_localized_message(
                    LK.Tracking.Stats.GOAL_REMAINING,
                    lang,
                    remaining=abs(weight_progress.remaining_to_goal)
                )
                report += self.get_localized_message(
                    LK.Tracking.Stats.GOAL_PERCENTAGE,
                    lang,
                    percentage=weight_progress.goal_completion_percentage
                )

            report += "\n"

            # Мотивационное сообщение
            report += self.get_localized_message(LK.Tracking.Stats.MOTIVATION, lang)

            return report

        except Exception as e:
            self.logger.error(f"Error formatting weekly report: {str(e)}")
            return self.get_localized_message(LK.Tracking.Stats.REPORT_ERROR, lang)

    async def get_recent_weight_entries(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Получает последние записи о весе пользователя

        Args:
            user_id: ID пользователя
            limit: Максимальное количество записей

        Returns:
            List[Dict[str, Any]]: Список записей о весе
        """
        try:
            # Получаем записи о весе через репозиторий
            entries = await self.weight_entry_repository.get_entries_by_user(user_id, limit)

            # Сортируем по дате (от новых к старым)
            sorted_entries = sorted(
                entries,
                key=lambda entry: entry.get("date", ""),
                reverse=True
            )

            # Ограничиваем количество записей
            return sorted_entries[:limit]

        except Exception as e:
            self.logger.error(f"Error getting recent weight entries: {str(e)}")
            return []

