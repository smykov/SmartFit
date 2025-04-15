# Система локализации в проекте SmartFit

## Введение

Система локализации в SmartFit предназначена для обеспечения мультиязычности всех пользовательских сообщений, что позволяет расширять географию проекта и улучшать пользовательский опыт. Документация содержит информацию о структуре локализации, используемых подходах и рекомендациях по работе с ней.

## Структура системы локализации

Система локализации имеет модульную структуру, что позволяет поддерживать разные языки и легко добавлять новые. Основные компоненты системы:

```
app/localization/
├── __init__.py
├── base.py             # Базовые классы для локализации
├── formats.py          # Функции для форматирования и плюральных форм
├── registry.py         # Реестр всех доступных языков
├── languages/          # Директория с языковыми модулями
│   ├── __init__.py
│   ├── en/             # Английский язык (основной)
│   │   ├── __init__.py
│   │   ├── common.py   # Общие сообщения
│   │   ├── commands.py # Сообщения для команд
│   │   ├── diet.py     # Сообщения для диет
│   │   ├── onboarding.py # Сообщения для онбординга
│   │   ├── tracking.py # Сообщения для трекинга
│   │   └── errors.py   # Сообщения для ошибок
│   ├── ru/             # Русский язык
│   │   └── ... (аналогичная структура)
│   └── es/             # Испанский язык
│       └── ... (аналогичная структура)
```

## Основные классы системы локализации

### `LocalizationString`

Класс для представления локализованной строки, поддерживающий плюральные формы и контекстно-зависимые переводы.

```python
class LocalizationString:
    def __init__(self, value: str, plural_forms: Optional[Dict[str, str]] = None, 
                 context_variants: Optional[Dict[str, str]] = None):
        # ...
    
    def format(self, **params) -> str:
        # ... Форматирование с учетом плюральных форм и контекста
```

### `LocalizationModule`

Модуль, содержащий набор локализованных строк для определенной функциональной области.

```python
class LocalizationModule:
    def __init__(self, strings: Dict[str, LocalizationString]):
        self.strings = strings
    
    def get(self, key: str, **params) -> str:
        # ... Получение и форматирование строки по ключу
```

### `LanguageBase`

Базовый класс для языка, агрегирующий различные модули.

```python
class LanguageBase:
    def __init__(self):
        self.modules = {}
    
    def register_module(self, name: str, module: LocalizationModule):
        # ... Регистрация модуля
    
    def get(self, key: str, **params) -> str:
        # ... Получение строки из соответствующего модуля
```

### `LocalizationRegistry`

Глобальный реестр всех доступных языков с функциональностью для их загрузки и получения локализованных сообщений.

```python
class LocalizationRegistry:
    def __init__(self, default_language: str = 'en'):
        # ...
    
    def register_language(self, code: str, language: LanguageBase):
        # ...
    
    def get(self, key: str, lang: Optional[str] = None, **params) -> str:
        # ... Получение локализованной строки с учетом языка
```

## Константы локализационных ключей

Для обеспечения консистентного использования ключей локализации в проекте определен класс `LocalizationKeys` (сокращенно `LK`), который содержит все доступные ключи, организованные в иерархическую структуру.

```python
# app/constants/localization_keys.py
class LocalizationKeys:
    class Common:
        YES = "common.yes"
        NO = "common.no"
        # ...
    
    class Commands:
        class Weight:
            RECORDED = "commands.weight.recorded"
            INVALID_FORMAT = "commands.weight.invalid_format"
            # ...
```

## Использование локализации в коде

### 1. Получение локализованного сообщения в классах с доступом к локализационному сервису

```python
# В классах, имеющих доступ к локализационному сервису через инжекцию зависимостей
from app.constants.localization_keys import LocalizationKeys as LK

class WeightCommand(BaseCommand):
    async def execute(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Получение языка пользователя
        lang = await self.localization_service.get_user_language(user_id)
        
        # Получение локализованного сообщения
        message = self.get_localized_message(
            LK.Commands.Weight.RECORDED,
            lang,
            weight=weight
        )
```

### 2. Использование хелпера get_message

```python
# В местах, где нет прямого доступа к локализационному сервису
from app.localization.registry import get_message
from app.constants.localization_keys import LocalizationKeys as LK

def some_function():
    # Получение локализованного сообщения
    message = get_message(LK.Common.YES, "ru")
```

### 3. Определение и использование плюральных форм

```python
# В модулях локализации (например, app/localization/languages/en/common.py)
from app.localization.base import LocalizationString, LocalizationModule

strings = {
    # Пример с плюральными формами
    'days_remaining': LocalizationString(
        '{count} days remaining',
        plural_forms={
            'one': '{count} day remaining',
            'few': '{count} days remaining',
            'many': '{count} days remaining'
        }
    ),
}

# Использование в коде
message = self.get_localized_message("common.days_remaining", lang, count=5)
# Результат: "5 days remaining"
```

### 4. Использование контекстно-зависимых переводов

```python
# В модулях локализации
strings = {
    # Пример с контекстными вариантами
    'weight_progress': LocalizationString(
        'You have changed weight by {change} kg',
        context_variants={
            'lost': 'You have lost {change} kg. Great job!',
            'gained': 'You have gained {change} kg. Keep working!'
        }
    ),
}

# Использование в коде
context = 'lost' if weight_change < 0 else 'gained'
message = self.get_localized_message(
    "tracking.weight_progress", 
    lang,
    context=context,
    change=abs(weight_change)
)
```

## Плюральные формы в разных языках

Система локализации поддерживает различные правила для плюральных форм в зависимости от языка:

### Английский (en)

```
'one': для числа 1
'other': для всех остальных чисел
```

### Русский (ru)

```
'one': для чисел, оканчивающихся на 1 (кроме 11)
'few': для чисел, оканчивающихся на 2-4 (кроме 12-14)
'many': для чисел, оканчивающихся на 0, 5-9, и 11-19
```

### Испанский (es)

```
'one': для числа 1
'other': для всех остальных чисел
```

## Интеграция с сервисами

### Сервис локализации

```python
# app/services/localization/localization_service.py
class LocalizationService(ILocalizationService):
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
    
    def get_message(self, key: str, lang: Optional[str] = None, **params) -> str:
        # ...
    
    async def get_user_language(self, user_id: str) -> str:
        # ...
    
    async def set_user_language(self, user_id: str, lang: str) -> bool:
        # ...
```

### Команда изменения языка

В проекте реализована команда `language`, позволяющая пользователю изменить язык интерфейса:

```
language ru   # Изменить язык на русский
language en   # Изменить язык на английский
language es   # Изменить язык на испанский
```

## Добавление нового языка

Чтобы добавить новый язык в систему, выполните следующие шаги:

1. **Создайте структуру каталогов для нового языка**:

   ```
   mkdir -p app/localization/languages/<code>/
   ```

   где `<code>` - код языка (например, `fr` для французского).

2. **Создайте базовые файлы модулей**:

   ```
   touch app/localization/languages/<code>/__init__.py
   touch app/localization/languages/<code>/common.py
   touch app/localization/languages/<code>/commands.py
   touch app/localization/languages/<code>/diet.py
   touch app/localization/languages/<code>/onboarding.py
   touch app/localization/languages/<code>/tracking.py
   touch app/localization/languages/<code>/errors.py
   ```

3. **Инициализируйте модули с переводами**:

   ```python
   # app/localization/languages/<code>/common.py
   from app.localization.base import LocalizationString, LocalizationModule

   strings = {
       'yes': LocalizationString('Перевод "Да"'),
       'no': LocalizationString('Перевод "Нет"'),
       # ... другие строки
   }

   module = LocalizationModule(strings)
   ```

4. **Создайте файл инициализации языка**:

   ```python
   # app/localization/languages/<code>/__init__.py
   from app.localization.base import LanguageBase

   from app.localization.languages.<code> import common
   from app.localization.languages.<code> import commands
   from app.localization.languages.<code> import diet
   from app.localization.languages.<code> import onboarding
   from app.localization.languages.<code> import tracking
   from app.localization.languages.<code> import errors

   # Создаем экземпляр языка
   language = LanguageBase()

   # Регистрируем все модули
   language.register_module('common', common.module)
   language.register_module('commands', commands.module)
   language.register_module('diet', diet.module)
   language.register_module('onboarding', onboarding.module)
   language.register_module('tracking', tracking.module)
   language.register_module('errors', errors.module)
   ```

5. **Для обеспечения корректной работы плюральных форм добавьте логику в метод `_get_plural_form`**:

   ```python
   # app/localization/formats.py
   @staticmethod
   def get_plural_form(count: int, lang: str = 'en') -> str:
       # ... существующая логика для en, ru, es

       # Добавьте логику для нового языка
       elif lang == '<code>':
           # Правила для нового языка
           # ...
           return plural_form
   ```

## Обновление и синхронизация переводов

Для поддержания переводов в актуальном состоянии рекомендуется использовать скрипт синхронизации, который автоматически добавляет новые ключи в модули локализации разных языков на основе английской версии:

```bash
python scripts/sync_localizations.py
```

## Лучшие практики локализации

1. **Всегда используйте класс `LocalizationKeys`** для ссылок на ключи локализации:
   ```python
   self.get_localized_message(LK.Common.YES, lang)
   ```

2. **Группируйте ключи логически** в классе `LocalizationKeys`:
   ```python
   class Commands:
       class Weight:
           # Все ключи, связанные с командой веса
       class Water:
           # Все ключи, связанные с командой воды
   ```

3. **Используйте параметры для подстановки значений**, а не конкатенацию строк:
   ```python
   # Правильно
   self.get_localized_message(LK.Commands.Weight.RECORDED, lang, weight=weight)
   
   # Неправильно
   self.get_localized_message(LK.Commands.Weight.RECORDED, lang) + str(weight)
   ```

4. **Учитывайте грамматические особенности разных языков** при создании строк:
   ```python
   # В английском "5 days" - множественное число
   # В русском "5 дней" - множественное число с особой формой
   ```

5. **Не используйте захардкоженные строки** в коде:
   ```python
   # Правильно
   self.get_localized_message(LK.Errors.NOT_FOUND, lang)
   
   # Неправильно
   "Error: Resource not found"
   ```

6. **Всегда получайте язык пользователя** перед отправкой сообщения:
   ```python
   lang = await self.localization_service.get_user_language(user_id)
   message = self.get_localized_message(LK.Common.YES, lang)
   ```

7. **Тестируйте локализацию** для всех поддерживаемых языков:
   ```python
   def test_all_languages():
       for lang in ['en', 'ru', 'es']:
           assert get_message(LK.Common.YES, lang) != LK.Common.YES
   ```

## Решение проблем

### 1. Отсутствие перевода

Если при вызове `get_localized_message` возвращается сам ключ вместо перевода, проверьте:

- Существует ли ключ в соответствующем модуле локализации
- Правильно ли указан язык
- Корректно ли зарегистрирован модуль в `LanguageBase`

### 2. Неправильное форматирование параметров

Если параметры не подставляются в строку, убедитесь, что:

- Имена параметров в строке соответствуют именам в вызове метода
- Используется правильный синтаксис для форматирования: `{parameter_name}`

### 3. Проблемы с плюральными формами

Если плюральные формы работают некорректно:

- Проверьте, определены ли все необходимые формы для языка
- Убедитесь, что используется параметр `count` при вызове `get_localized_message`
- Проверьте логику определения плюральной формы в методе `_get_plural_form`

## Заключение

Система локализации в проекте SmartFit обеспечивает гибкий и расширяемый механизм перевода сообщений на разные языки. Она поддерживает плюральные формы и контекстно-зависимые переводы, что позволяет создавать естественные и грамматически корректные сообщения для пользователей из разных стран.

Следуя рекомендациям и лучшим практикам, изложенным в этой документации, вы сможете эффективно использовать и развивать систему локализации в проекте SmartFit.