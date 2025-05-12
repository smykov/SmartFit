# Инструкция по добавлению новых уведомлений в систему SmartFit

Эта инструкция подробно описывает процесс добавления новых типов уведомлений в систему SmartFit с учетом принципов SOLID, DRY и чистой архитектуры. Инструкция предназначена для разработчиков, знакомых с основной архитектурой проекта.

## Содержание

1. [Архитектура системы уведомлений](#1-архитектура-системы-уведомлений)
2. [Пошаговое руководство по добавлению новых уведомлений](#2-пошаговое-руководство-по-добавлению-новых-уведомлений)
   1. [Добавление ключей локализации](#шаг-1-добавление-ключей-локализации)
   2. [Создание стратегии уведомления](#шаг-2-создание-стратегии-уведомления)
   3. [Регистрация стратегии в фабрике](#шаг-3-регистрация-стратегии-в-фабрике)
   4. [Добавление текстов уведомлений в локализацию](#шаг-4-добавление-текстов-уведомлений-в-локализацию)
   5. [Тестирование нового уведомления](#шаг-5-тестирование-нового-уведомления)
3. [Примеры](#3-примеры)
4. [Советы и лучшие практики](#4-советы-и-лучшие-практики)
5. [Устранение неполадок](#5-устранение-неполадок)

## 1. Архитектура системы уведомлений

Система уведомлений в SmartFit построена на следующих ключевых компонентах:

1. **ReminderService** - Основной сервис, управляющий отправкой уведомлений.
2. **ReminderStrategy** - Абстрактный класс, определяющий интерфейс для стратегий уведомлений.
3. **Конкретные стратегии** - Классы наследники от ReminderStrategy, реализующие логику для различных типов уведомлений.
4. **ReminderFactory** - Фабрика для создания стратегий уведомлений.
5. **IReminderRepository** - Репозиторий для хранения информации о отправленных уведомлениях.

Архитектура следует паттерну "Стратегия", который позволяет легко добавлять новые типы уведомлений без изменения основной логики отправки.

## 2. Пошаговое руководство по добавлению новых уведомлений

### Шаг 1: Добавление ключей локализации

Первым шагом добавьте ключи для нового типа уведомления в файл `app/constants/localization_keys.py`:

```python
# app/constants/localization_keys.py (дополнить класс Reminders)

class Reminders:
    """Ключи для напоминаний"""
    # ... Существующие ключи ...
    
    # Добавьте новый тип уведомления
    REMINDER_TYPE_YOUR_NEW_TYPE = "reminders.type.your_new_type"
    
    # Добавьте ключ для текста уведомления
    YOUR_NEW_TYPE_REMINDER = "reminders.your_new_type"
```

### Шаг 2: Создание стратегии уведомления

Создайте новый класс стратегии в файле `app/services/reminders/reminder_strategies.py`, который наследуется от `ReminderStrategy`:

```python
# app/services/reminders/reminder_strategies.py (добавить новый класс)

class YourNewReminderStrategy(ReminderStrategy):
    """Стратегия для нового типа уведомлений"""

    async def should_send(self, user: Dict[str, Any], tracking_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Определяет, нужно ли отправлять уведомление
        
        Args:
            user: Данные пользователя
            tracking_data: Данные трекинга
            context: Контекст (время суток и т.д.)
            
        Returns:
            bool: True, если нужно отправить уведомление
        """
        # Реализуйте логику проверки условий отправки уведомления
        # Например, отправлять уведомление только в определенное время дня
        # или при определенных условиях пользователя
        
        # Пример логики:
        is_time_condition = context.get("is_evening", False)
        is_user_condition = user.get("some_field") == "some_value"
        
        return is_time_condition and is_user_condition

    def get_reminder_type(self) -> str:
        """
        Возвращает тип уведомления
        
        Returns:
            str: Тип уведомления
        """
        return LK.Reminders.REMINDER_TYPE_YOUR_NEW_TYPE

    def get_message_key(self) -> str:
        """
        Возвращает ключ сообщения
        
        Returns:
            str: Ключ сообщения уведомления
        """
        return LK.Reminders.YOUR_NEW_TYPE_REMINDER

    def get_interval_seconds(self) -> int:
        """
        Возвращает минимальный интервал между уведомлениями в секундах
        
        Returns:
            int: Интервал в секундах
        """
        return 86400  # 24 часа (можно изменить по необходимости)
```

### Шаг 3: Регистрация стратегии в фабрике

Добавьте новую стратегию в фабрику уведомлений в файле `app/services/reminders/reminder_factory.py`:

```python
# app/services/reminders/reminder_factory.py (дополнить методы)

@staticmethod
def create_all_strategies() -> List[ReminderStrategy]:
    """
    Создает все доступные стратегии уведомлений
    
    Returns:
        List[ReminderStrategy]: Список стратегий
    """
    return [
        # Существующие стратегии
        WeightReminderStrategy(),
        WaterReminderStrategy(),
        BreakfastReminderStrategy(),
        LunchReminderStrategy(),
        DinnerReminderStrategy(),
        WeeklyReportReminderStrategy(),
        PlanApprovalReminderStrategy(),
        # Добавьте новую стратегию
        YourNewReminderStrategy()
    ]

@staticmethod
def create_strategy(reminder_type: str) -> ReminderStrategy:
    """
    Создает стратегию по типу уведомления
    
    Args:
        reminder_type: Тип уведомления
        
    Returns:
        ReminderStrategy: Стратегия уведомления
    """
    strategies = {
        # Существующие стратегии
        "weight": WeightReminderStrategy(),
        "water": WaterReminderStrategy(),
        "breakfast": BreakfastReminderStrategy(),
        "lunch": LunchReminderStrategy(),
        "dinner": DinnerReminderStrategy(),
        "weekly_report": WeeklyReportReminderStrategy(),
        "plan_approval": PlanApprovalReminderStrategy(),
        # Добавьте новую стратегию
        "your_new_type": YourNewReminderStrategy()
    }
    
    return strategies.get(reminder_type)
```

### Шаг 4: Добавление текстов уведомлений в локализацию

Добавьте текст уведомления в файлы локализации:

```python
# app/localization/languages/ru/reminders.py (дополнить словарь strings)

strings = {
    # Существующие строки
    'greeting': LocalizationString('👋 Привет'),
    
    'type': {
        # Существующие типы
        'onboarding': LocalizationString('onboarding'),
        'weight': LocalizationString('weight'),
        'water': LocalizationString('water'),
        'breakfast': LocalizationString('breakfast'),
        'lunch': LocalizationString('lunch'),
        'dinner': LocalizationString('dinner'),
        'weekly_report': LocalizationString('weekly_report'),
        'plan_approval': LocalizationString('plan_approval'),
        # Добавьте новый тип
        'your_new_type': LocalizationString('your_new_type'),
    },
    
    # Существующие уведомления
    'weight': LocalizationString('⚖️ Привет! Не забудь записать свой вес сегодня...'),
    # ...
    
    # Добавьте новое уведомление
    'your_new_type': LocalizationString(
        '📢 Текст вашего нового уведомления. Здесь можно использовать параметры: {param_name}.'
    ),
}
```

Повторите этот шаг для всех поддерживаемых языков (en, es и т.д.).

### Шаг 5: Тестирование нового уведомления

1. Запустите приложение.
2. Используйте эндпоинт API для принудительного запуска нового уведомления:
   ```
   POST /reminders/trigger/tracking
   ```
   Этот запрос активирует выполнение `send_tracking_reminders()`, который будет использовать все стратегии, включая вашу новую.

3. Проверьте логи на наличие информации об отправке уведомления.
4. Проверьте, получает ли пользователь уведомление при выполнении условий в методе `should_send()`.

## 3. Примеры

### Пример 1: Уведомление о низком потреблении белка

```python
# В app/constants/localization_keys.py
REMINDER_TYPE_LOW_PROTEIN = "reminders.type.low_protein"
LOW_PROTEIN_REMINDER = "reminders.low_protein"

# В app/services/reminders/reminder_strategies.py
class LowProteinReminderStrategy(ReminderStrategy):
    """Стратегия для уведомлений о низком потреблении белка"""
    
    async def should_send(self, user: Dict[str, Any], tracking_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Проверяем, есть ли данные о соблюдении плана
        if not tracking_data or "meal_compliance" not in tracking_data:
            return False
            
        # Получаем статистику соблюдения
        meal_compliance = tracking_data.get("meal_compliance", {})
        
        # Проверяем, что уже есть отметки о приемах пищи
        if not meal_compliance:
            return False
            
        # Проверяем наличие информации о потреблении белка
        proteins_deficit = False
        for meal_type, meal_data in meal_compliance.items():
            if "proteins_consumed" in meal_data and "proteins" in meal_data.get("planned_meal", {}):
                planned = meal_data["planned_meal"]["proteins"]
                consumed = meal_data["proteins_consumed"]
                
                # Если потребление белка менее 70% от запланированного
                if planned > 0 and consumed / planned < 0.7:
                    proteins_deficit = True
                    break
                    
        # Отправляем уведомление вечером, если обнаружен дефицит белка
        return context.get("is_evening", False) and proteins_deficit
        
    def get_reminder_type(self) -> str:
        return LK.Reminders.REMINDER_TYPE_LOW_PROTEIN
        
    def get_message_key(self) -> str:
        return LK.Reminders.LOW_PROTEIN_REMINDER
        
    def get_interval_seconds(self) -> int:
        return 86400  # 24 часа
```

### Пример 2: Уведомление о необходимости обновить план питания

```python
# В app/constants/localization_keys.py
REMINDER_TYPE_UPDATE_DIET = "reminders.type.update_diet"
UPDATE_DIET_REMINDER = "reminders.update_diet"

# В app/services/reminders/reminder_strategies.py
class UpdateDietReminderStrategy(ReminderStrategy):
    """Стратегия для уведомлений о необходимости обновить план питания"""
    
    async def should_send(self, user: Dict[str, Any], tracking_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Проверяем, что сегодня воскресенье и вечер
        is_sunday = context.get("is_sunday", False)
        is_evening = context.get("is_evening", False)
        
        # Проверяем, что план питания существует более 3 недель
        diet_plan_age = None
        if user.get("diet_plan", {}).get("created_at"):
            created_at = datetime.fromisoformat(user["diet_plan"]["created_at"])
            now = datetime.now(pytz.timezone(settings.TIMEZONE))
            diet_plan_age = (now - created_at).days
            
        # Напоминаем обновить план, если он старше 21 дня
        is_old_plan = diet_plan_age is not None and diet_plan_age > 21
        
        return is_sunday and is_evening and is_old_plan
        
    def get_reminder_type(self) -> str:
        return LK.Reminders.REMINDER_TYPE_UPDATE_DIET
        
    def get_message_key(self) -> str:
        return LK.Reminders.UPDATE_DIET_REMINDER
        
    def get_interval_seconds(self) -> int:
        return 604800  # 7 дней (еженедельное напоминание)
```

## 4. Советы и лучшие практики

1. **Временные интервалы**: Выбирайте подходящий интервал для уведомлений. Слишком частые уведомления могут раздражать пользователей.

2. **Контекстная релевантность**: Отправляйте уведомления только когда они действительно актуальны для пользователя.

3. **Персонализация**: Используйте данные пользователя для персонализации сообщений.

4. **Локализация**: Убедитесь, что все сообщения доступны на всех поддерживаемых языках.

5. **Тестирование**: Тщательно тестируйте новые уведомления перед выпуском в продакшн.

6. **Постоянно улучшайте**: Собирайте статистику о взаимодействии пользователя с уведомлениями и улучшайте их эффективность.

7. **Следите за качеством**: Уведомления должны быть информативными, краткими и полезными.

## 5. Устранение неполадок

### Уведомление не отправляется

1. **Проверьте метод `should_send()`**: Убедитесь, что условия корректны и возвращают `True` при необходимости отправки.

2. **Проверьте логи**: Ищите ошибки в логах приложения.

3. **Проверьте интервал**: Убедитесь, что `get_interval_seconds()` не слишком большой и прошло достаточно времени с момента последнего уведомления.

4. **Проверьте регистрацию в фабрике**: Убедитесь, что стратегия добавлена в методы `create_all_strategies()` и `create_strategy()`.

### Исключения при отправке уведомлений

1. **Проверьте класс стратегии**: Убедитесь, что все методы корректно реализованы.

2. **Проверьте ключи локализации**: Убедитесь, что ключи существуют в файлах локализации.

3. **Проверьте параметры сообщений**: Если сообщение принимает параметры, убедитесь, что они правильно переданы.

### Уведомление отправляется, но текст не отображается

1. **Проверьте локализацию**: Убедитесь, что строка добавлена во все файлы локализации.

2. **Проверьте формат сообщения**: Убедитесь, что сообщение форматируется корректно.

3. **Проверьте параметры**: Если сообщение использует параметры, убедитесь, что они корректно переданы.

---

Используя данную инструкцию, вы сможете легко добавлять новые типы уведомлений в систему SmartFit, следуя принципам SOLID и чистой архитектуры. Это позволит улучшить взаимодействие с пользователями и повысить эффективность приложения для контроля веса.