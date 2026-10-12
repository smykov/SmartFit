> **Archived MVP (April–June 2025), not maintained.** An AI weight-loss assistant in WhatsApp for Guatemala: FastAPI, Firestore, Twilio, OpenAI with model fallback, Spanish/English localization, 118 tests. Kept public as a portfolio piece; dependencies and models are out of date.
>
> **MVP 2025, не поддерживается.** Репозиторий открыт как пример проекта; зависимости и модели устарели.

# SmartFit - AI-ассистент для похудения

SmartFit это MVP AI-ассистента для персонализированного контроля веса и здорового образа жизни, учитывающий местные продукты, бюджет и культурные особенности.

## Особенности

- **Персонализированные планы питания**: генерация диет с учетом местных продуктов Гватемалы
- **WhatsApp интеграция**: общение с пользователями через удобный WhatsApp бот
- **Трекинг прогресса**: отслеживание веса и потребления воды
- **Бюджетные ограничения**: учет финансовых возможностей пользователя

## Технологический стек

- **Backend**: Python 3.11, FastAPI
- **База данных**: Firebase (Firestore)
- **AI**: OpenAI API (GPT-3.5-turbo)
- **Интеграции**: WhatsApp Business API (через Twilio)
- **Контейнеризация**: Docker, Docker Compose

## Структура проекта

```
smartfit-mvp/
│
├── app/
│   ├── api/              # API эндпоинты
│   ├── db/               # Работа с БД и загрузка данных
│   ├── models/           # Модели данных
│   ├── services/         # Бизнес-логика 
│   └── templates/        # Шаблоны для AI
│
├── data/                 # Данные о продуктах
├── scripts/              # Вспомогательные скрипты
├── main.py               # Точка входа
├── config.py             # Конфигурация
├── Dockerfile            # Контейнеризация
└── docker-compose.yml    # Запуск сервисов
```

## Установка и запуск

### Требования

- Python 3.11+
- Docker и Docker Compose (опционально)
- Firebase аккаунт
- Twilio аккаунт (для WhatsApp)
- OpenAI API ключ

### Настройка переменных окружения

1. Скопируйте `.env.example` в `.env` и заполните переменные:

```bash
cp .env.example .env
```

2. Разместите ваш Firebase credentials файл в корне проекта:

```
firebase-credentials.json
```

### Запуск локально

1. Создайте и активируйте виртуальное окружение:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Заполните базу данных начальными данными:

```bash
python scripts/seed_database.py
```

4. Запустите сервер:

```bash
uvicorn main:app --reload
```

### Запуск с помощью Docker

```bash
docker-compose up -d
```

## Настройка WhatsApp

1. Зарегистрируйтесь в [Twilio](https://www.twilio.com/)
2. Настройте WhatsApp Sandbox
3. Укажите webhook URL `https://your-domain.com/api/whatsapp/webhook`
4. Для локальной разработки используйте ngrok:

```bash
docker-compose up ngrok -d
```

5. Посмотрите публичный URL командой:

```bash
docker-compose logs ngrok
```

## Тестирование MVP

1. Отправьте любое сообщение на WhatsApp номер вашего бота
2. Бот начнет онбординг с базовыми вопросами
3. После завершения онбординга бот сгенерирует персонализированную диету

Добавлю в README.md блок с описанием возможностей мок-режима. Предлагаю следующее дополнение к файлу:

## Режим тестирования (Мок-режим)

В SmartFit предусмотрен специальный режим тестирования, который позволяет разрабатывать и тестировать приложение без использования внешних API (OpenAI, Twilio и т.д.). Это экономит ресурсы и ускоряет разработку.

### Возможности мок-режима

- **Генерация диеты**: генерирует тестовый план питания без обращения к OpenAI API
- **Создание списков покупок**: создает тестовые списки покупок на основе моковых данных
- **Ответы на вопросы пользователей**: возвращает предопределенные ответы на вопросы о питании

### Как включить мок-режим

Вы можете включить мок-режим несколькими способами:

1. **Через .env файл**:
   ```
   USE_MOCK_SERVICES=True
   ```

2. **При запуске сервера из командной строки**:
   ```bash
   USE_MOCK_SERVICES=True uvicorn main:app --reload
   ```

3. **При запуске через Docker Compose**:
   ```bash
   USE_MOCK_SERVICES=True docker-compose up
   ```

### Когда использовать мок-режим

- Во время разработки UI/UX, когда не требуется реальная генерация диет
- При тестировании интеграций и пользовательских сценариев
- Когда у вас нет доступа к API-ключам (например, в CI/CD пайплайнах)
- Чтобы избежать расходов на использование платных API во время разработки

### Настройка моковых данных

Логика мок-сервисов находится в модуле `app/services/mock_diet_service.py`. Вы можете настроить генерируемые данные под ваши тестовые сценарии, изменив этот файл.

```python
# Пример настройки моковых данных
class MockDietService:
    def _generate_meal(self, meal_type: str, local_foods: List[str]) -> Dict[str, Any]:
        # Здесь вы можете настроить генерацию тестовых блюд
        # ...
```
## API документация

После запуска сервера, документация API доступна по адресу:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Выбор LLM через конфигурацию

В файле `.env` можно настроить используемый LLM-провайдер:

```
LLM_PROVIDER=openai  # Варианты: openai, deepseek, hybrid
```

### Гибридный режим

Для гибридного режима можно настроить маппинг задач на конкретные провайдеры:

```
LLM_TASK_MAPPING={"diet_plan": "openai", "nutrition_question": "deepseek", "shopping_list": "deepseek"}
```

### Добавление нового LLM-провайдера

Чтобы добавить поддержку нового LLM-провайдера, достаточно:

1. Создать новый класс, наследующий `BaseLLMService`
2. Реализовать абстрактные методы для работы с API этого провайдера
3. Добавить поддержку этого провайдера в `LLMFactory`


## Лицензия

Copyright (c) 2024 SmartFit
