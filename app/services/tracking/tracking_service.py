import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, Tuple

import pytz

from app.db.firebase import firebase_client
from app.models.tracking import (
    DailyTrackingStatus,
    WeightGoalProgress
)
from config import settings

logger = logging.getLogger(__name__)


class TrackingService:
    """Сервис для работы с данными трекинга"""

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
            # Получаем пользователя
            user = firebase_client.get_document("users", user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False

            # Получаем текущую дату
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date().isoformat()

            # Обновляем текущий вес
            firebase_client.update_document("users", user_id, {"current_weight": weight})

            # Добавляем запись в историю веса
            weight_history = user.get("weight_history", {})
            weight_history[today] = weight

            firebase_client.update_document("users", user_id, {"weight_history": weight_history})

            # Создаем запись в коллекции weight_entries для аналитики
            entry_data = {
                "user_id": user_id,
                "weight": weight,
                "date": today,
                "notes": notes
            }

            firebase_client.add_document("weight_entries", entry_data)

            return True

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
            # Получаем пользователя
            user = firebase_client.get_document("users", user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False

            # Получаем текущую дату
            today = datetime.now(pytz.timezone(settings.TIMEZONE)).date().isoformat()

            # Добавляем запись в историю потребления воды
            water_history = user.get("water_intake_history", {})

            # Если на сегодня уже есть запись, добавляем к ней
            if today in water_history:
                water_history[today] += amount
            else:
                water_history[today] = amount

            firebase_client.update_document("users", user_id, {"water_intake_history": water_history})

            # Создаем запись в коллекции water_entries для аналитики
            entry_data = {
                "user_id": user_id,
                "amount": amount,
                "date": today,
                "time": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
            }

            firebase_client.add_document("water_entries", entry_data)

            return True

        except Exception as e:
            logger.error(f"Error recording water intake: {str(e)}")
            return False

    async def record_meal_compliance(
            self,
            user_id: str,
            date_val: date,
            meal_type: str,
            status: str,
            notes: str = None,
            alternative_meal: str = None
    ) -> bool:
        """
        Записывает соблюдение режима питания

        Args:
            user_id: ID пользователя
            date_val: Дата
            meal_type: Тип приема пищи (breakfast, lunch, dinner, snack)
            status: Статус (followed, partially, substituted, skipped)
            notes: Дополнительные заметки
            alternative_meal: Альтернативное блюдо (если status=substituted)

        Returns:
            bool: Результат операции
        """
        try:
            # Проверяем существование пользователя
            user = firebase_client.get_document("users", user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False

            # Формируем дату в формате строки
            date_str = date_val.isoformat() if isinstance(date_val, date) else date_val

            # Создаем запись о соблюдении режима
            compliance_data = {
                "user_id": user_id,
                "date": date_str,
                "meal_type": meal_type,
                "status": status,
                "notes": notes,
                "alternative_meal": alternative_meal,
                "created_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
            }

            # Сохраняем в базу данных
            compliance_id = firebase_client.add_document("meal_compliance", compliance_data)

            if not compliance_id:
                logger.error(f"Failed to save meal compliance for user {user_id}")
                return False

            # Обновляем общую статистику соблюдения
            await self._update_daily_compliance(user_id, date_str)

            return True

        except Exception as e:
            logger.error(f"Error recording meal compliance: {str(e)}")
            return False

    async def _update_daily_compliance(self, user_id: str, date_str: str) -> None:
        """
        Обновляет общую статистику соблюдения за день

        Args:
            user_id: ID пользователя
            date_str: Дата в формате строки
        """
        try:
            # Получаем все записи о соблюдении за день
            compliances = firebase_client.query_documents(
                "meal_compliance",
                "user_id", "==", user_id
            )

            # Фильтруем по дате
            daily_compliances = [c for c in compliances if c.get("date") == date_str]

            if not daily_compliances:
                return

            # Формируем словарь по типам приемов пищи
            meals_status = {}
            for compliance in daily_compliances:
                meal_type = compliance.get("meal_type")
                status = compliance.get("status")
                meals_status[meal_type] = status

            # Рассчитываем общий процент соблюдения
            score_map = {
                "followed": 1.0,
                "partially": 0.5,
                "substituted": 0.3,
                "skipped": 0.0,
                "not_recorded": 0.0
            }

            total_score = sum(score_map.get(status, 0) for status in meals_status.values())
            max_possible = len(meals_status) if meals_status else 1
            overall_score = (total_score / max_possible) * 100

            # Сохраняем общую статистику
            compliance_data = {
                "user_id": user_id,
                "date": date_str,
                "meals": meals_status,
                "overall_score": overall_score,
                "updated_at": datetime.now(pytz.timezone(settings.TIMEZONE)).isoformat()
            }

            # Проверяем, существует ли уже запись
            existing = firebase_client.query_documents(
                "daily_compliance",
                "user_id", "==", user_id
            )

            # Фильтруем по дате
            existing = [e for e in existing if e.get("date") == date_str]

            if existing:
                # Обновляем существующую запись
                firebase_client.update_document("daily_compliance", existing[0]["id"], compliance_data)
            else:
                # Создаем новую запись
                firebase_client.add_document("daily_compliance", compliance_data)

        except Exception as e:
            logger.error(f"Error updating daily compliance: {str(e)}")

    async def get_diet_compliance(self, user_id: str, date_val: date = None) -> Optional[Dict[str, Any]]:
        """
        Получает статистику соблюдения плана питания

        Args:
            user_id: ID пользователя
            date_val: Дата (если None, используется текущая дата)

        Returns:
            Optional[Dict[str, Any]]: Статистика соблюдения
        """
        try:
            # Если дата не указана, используем текущую
            if date_val is None:
                date_val = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            # Преобразуем в строку
            date_str = date_val.isoformat() if isinstance(date_val, date) else date_val

            # Получаем запись о соблюдении
            compliances = firebase_client.query_documents(
                "daily_compliance",
                "user_id", "==", user_id
            )

            # Фильтруем по дате
            compliances = [c for c in compliances if c.get("date") == date_str]

            if not compliances:
                # Если записи нет, создаем пустую запись
                empty_compliance = {
                    "user_id": user_id,
                    "date": date_str,
                    "meals": {},
                    "overall_score": 0,
                    "message": "Нет данных о соблюдении плана на этот день"
                }
                return empty_compliance

            return compliances[0]

        except Exception as e:
            logger.error(f"Error getting diet compliance: {str(e)}")
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
            user = firebase_client.get_document("users", user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None

            # Если дата не указана, используем сегодняшнюю
            if not target_date:
                target_date = datetime.now(pytz.timezone(settings.TIMEZONE)).date()

            date_str = target_date.isoformat()

            # Проверяем, записан ли вес на указанную дату
            weight_history = user.get("weight_history", {})
            weight_recorded = date_str in weight_history

            # Получаем потребление воды на указанную дату
            water_history = user.get("water_intake_history", {})
            current_water_intake = water_history.get(date_str, 0)

            # Целевое потребление воды (2 литра по умолчанию)
            water_goal = 2000  # в мл

            # Получаем данные о соблюдении плана питания
            compliance_data = await self.get_diet_compliance(user_id, target_date)
            meal_compliance = {}
            overall_compliance_score = 0

            if compliance_data and "meals" in compliance_data:
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
            # Получаем пользователя
            user = firebase_client.get_document("users", user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None

            # Получаем историю веса
            weight_history = user.get("weight_history", {})

            # Если не указаны даты, возвращаем всю историю
            if not start_date and not end_date:
                return weight_history

            # Фильтруем по датам
            filtered_history = {}

            for date_str, weight in weight_history.items():
                entry_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                # Проверяем, входит ли дата в указанный период
                if (not start_date or entry_date >= start_date) and (not end_date or entry_date <= end_date):
                    filtered_history[date_str] = weight

            return filtered_history

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
            # Получаем пользователя
            user = firebase_client.get_document("users", user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None

            # Получаем историю потребления воды
            water_history = user.get("water_intake_history", {})

            # Если не указаны даты, возвращаем всю историю
            if not start_date and not end_date:
                return water_history

            # Фильтруем по датам
            filtered_history = {}

            for date_str, amount in water_history.items():
                entry_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                # Проверяем, входит ли дата в указанный период
                if (not start_date or entry_date >= start_date) and (not end_date or entry_date <= end_date):
                    filtered_history[date_str] = amount

            return filtered_history

        except Exception as e:
            logger.error(f"Error getting water history: {str(e)}")
            return None

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
            user = firebase_client.get_document("users", user_id)
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

            # Определяем начальный вес
            start_weight, start_date = self._get_start_weight(user)

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

    async def generate_weekly_report(self, user_id: str) -> Optional[str]:
        """
        Генерирует еженедельный отчет о прогрессе

        Args:
            user_id: ID пользователя

        Returns:
            Optional[str]: Текст отчета или None в случае ошибки
        """
        try:
            # Получаем пользователя
            user = firebase_client.get_document("users", user_id)
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

            # Формируем отчет
            report = self._format_weekly_report(user, weight_history, water_history, weight_progress)

            return report

        except Exception as e:
            logger.error(f"Error generating weekly report: {str(e)}")
            return None

    def _get_start_weight(self, user: Dict[str, Any]) -> Tuple[Optional[float], Optional[date]]:
        """
        Определяет начальный вес пользователя

        Args:
            user: Данные пользователя

        Returns:
            Tuple[Optional[float], Optional[date]]: (начальный вес, дата начального веса)
        """
        try:
            # Получаем историю веса
            weight_history = user.get("weight_history", {})

            if not weight_history:
                return None, None

            # Находим самую раннюю запись
            earliest_date = min(weight_history.keys())
            start_weight = weight_history[earliest_date]

            # Преобразуем строку даты в объект date
            start_date = datetime.strptime(earliest_date, "%Y-%m-%d").date()

            return start_weight, start_date

        except Exception as e:
            logger.error(f"Error getting start weight: {str(e)}")
            return None, None

    def _format_weekly_report(
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
        try:
            report = f"📊 *Еженедельный отчет о прогрессе для {user.get('name', 'пользователя')}*\n\n"

            # Анализ веса
            if weight_history:
                # Определяем начальный и конечный вес за период
                dates = sorted(weight_history.keys())
                first_weight = weight_history[dates[0]]
                last_weight = weight_history[dates[-1]] if len(dates) > 1 else first_weight

                weight_change = last_weight - first_weight

                report += "⚖️ *Изменение веса:*\n"
                report += f"• Начальный вес: {first_weight} кг ({dates[0]})\n"
                report += f"• Текущий вес: {last_weight} кг ({dates[-1]})\n"

                if weight_change < 0:
                    report += f"• Изменение: -{abs(weight_change):.1f} кг 👍\n"
                elif weight_change > 0:
                    report += f"• Изменение: +{weight_change:.1f} кг\n"
                else:
                    report += "• Изменение: 0 кг (вес стабилен)\n"
            else:
                report += "⚖️ *Вес:* Нет данных за последнюю неделю\n"

            report += "\n"

            # Анализ потребления воды
            if water_history:
                total_water = sum(water_history.values())
                avg_water = total_water / len(water_history)
                days_tracked = len(water_history)

                report += "💧 *Потребление воды:*\n"
                report += f"• Дней отслеживания: {days_tracked}/7\n"
                report += f"• Среднее потребление: {avg_water / 1000:.1f} л/день\n"

                if avg_water >= 2000:
                    report += "• Статус: Отлично! Ты достигаешь целевого потребления воды 👍\n"
                elif avg_water >= 1500:
                    report += "• Статус: Хорошо, но можно увеличить потребление воды\n"
                else:
                    report += "• Статус: Недостаточное потребление воды, старайся пить больше\n"
            else:
                report += "💧 *Потребление воды:* Нет данных за последнюю неделю\n"

            report += "\n"

            # Прогресс к цели
            if weight_progress:
                report += "🎯 *Прогресс к цели:*\n"
                report += f"• Целевой вес: {weight_progress.target_weight} кг\n"
                report += f"• Осталось: {abs(weight_progress.remaining_to_goal):.1f} кг\n"
                report += f"• Прогресс: {weight_progress.goal_completion_percentage:.1f}% выполнено\n"

            report += "\n"

            # Мотивационное сообщение
            report += "💪 *Продолжай в том же духе!* Ты на пути к своей цели."

            return report

        except Exception as e:
            logger.error(f"Error formatting weekly report: {str(e)}")
            return "Еженедельный отчет недоступен. Пожалуйста, попробуйте позже."


# Создаем экземпляр сервиса трекинга
tracking_service = TrackingService()