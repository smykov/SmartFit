# GuateFit - AI-ассистент для похудения

GuateFit это MVP AI-ассистента для персонализированного похудения, учитывающий местные продукты Гватемалы, бюджет и культурные особенности.

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
guatefit-mvp/
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

## API документация

После запуска сервера, документация API доступна по адресу:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Лицензия

Copyright (c) 2024 GuateFit
