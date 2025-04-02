# Руководство по развертыванию GuateFit

Данное руководство описывает процесс развертывания MVP GuateFit на сервере.

## Предварительные требования

- Сервер Ubuntu 20.04 или новее
- Установленный Docker и Docker Compose
- Домен или поддомен для сервиса
- Файл с учетными данными Firebase
- API ключи (OpenAI, Twilio)

## Шаг 1: Подготовка сервера

1. Обновите систему:

```bash
sudo apt update
sudo apt upgrade -y
```

2. Установите необходимые пакеты:

```bash
sudo apt install -y git docker.io docker-compose
```

3. Добавьте вашего пользователя в группу docker:

```bash
sudo usermod -aG docker $USER
```

4. Перезайдите в систему или выполните:

```bash
newgrp docker
```

## Шаг 2: Настройка домена и SSL

1. Настройте A-запись вашего домена на IP-адрес сервера
2. Установите Certbot для получения SSL-сертификата:

```bash
sudo apt install -y certbot python3-certbot-nginx
```

3. Получите SSL-сертификат:

```bash
sudo certbot --nginx -d your-domain.com
```

## Шаг 3: Клонирование и настройка проекта

1. Клонируйте репозиторий:

```bash
git clone https://github.com/yourusername/guatefit-mvp.git
cd guatefit-mvp
```

2. Создайте файл .env на основе .env.example:

```bash
cp .env.example .env
```

3. Отредактируйте файл .env, указав необходимые значения:

```
# Основные настройки
DEBUG=False

# Firebase
FIREBASE_CREDENTIALS=firebase-credentials.json
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com

# OpenAI
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-3.5-turbo

# WhatsApp API (Twilio)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
WHATSAPP_WEBHOOK_URL=https://your-domain.com/api/whatsapp/webhook
```

4. Скопируйте файл учетных данных Firebase:

```bash
# Скопируйте файл с локального компьютера на сервер
scp firebase-credentials.json username@your-server:/path/to/guatefit-mvp/
```

## Шаг 4: Настройка Docker

1. Отредактируйте docker-compose.yml, удалив или закомментировав сервис ngrok в продакшен-окружении

2. Создайте дополнительный файл docker-compose.prod.yml:

```yaml
version: '3.8'

services:
  api:
    restart: always
    environment:
      - DEBUG=False
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.guatefit.rule=Host(`your-domain.com`)"
      - "traefik.http.routers.guatefit.entrypoints=websecure"
      - "traefik.http.routers.guatefit.tls.certresolver=myresolver"

  traefik:
    image: traefik:v2.5
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.tlschallenge=true"
      - "--certificatesresolvers.myresolver.acme.email=your-email@example.com"
      - "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./letsencrypt:/letsencrypt
      - /var/run/docker.sock:/var/run/docker.sock:ro
    restart: always
    networks:
      - guatefit-network
```

## Шаг 5: Запуск приложения

1. Соберите и запустите контейнеры:

```bash
# В режиме разработки
docker-compose up -d

# В продакшене
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

2. Заполните базу данных начальными данными:

```bash
docker-compose exec api python scripts/seed_database.py
```

3. Проверьте работу приложения:

```bash
docker-compose logs -f api
```

## Шаг 6: Настройка Twilio

1. Войдите в панель управления Twilio
2. Перейдите в раздел WhatsApp
3. Настройте webhook URL на `https://your-domain.com/api/whatsapp/webhook`
4. Проверьте работу, отправив сообщение на номер WhatsApp бота

## Шаг 7: Мониторинг и обслуживание

1. Настройте базовый мониторинг:

```bash
# Установка Prometheus и Grafana (опционально)
docker-compose -f docker-compose.monitoring.yml up -d
```

2. Проверка журналов:

```bash
docker-compose logs -f api
```

3. Обновление приложения:

```bash
# Получение обновлений
git pull

# Перезапуск контейнеров
docker-compose down
docker-compose up -d
```

## Настройка регулярных задач

Для выполнения регулярных задач (например, отправка напоминаний), настройте crontab:

```bash
# Открыть редактор crontab
crontab -e

# Добавить задачи
# Ежедневное напоминание о весе в 9:00
0 9 * * * docker-compose exec -T api python scripts/send_weight_reminders.py

# Еженедельный отчет по воскресеньям в 18:00
0 18 * * 0 docker-compose exec -T api python scripts/send_weekly_reports.py
```

## Резервное копирование

Настройте регулярное резервное копирование вашей базы данных Firebase через консоль Firebase или используйте Firebase Admin SDK для создания резервных копий.

## Устранение неполадок

- **Проблемы с подключением**: Проверьте настройки брандмауэра и убедитесь, что порты 80, 443 открыты
- **Ошибки WhatsApp**: Проверьте журналы Twilio и убедитесь, что webhook URL правильно настроен
- **Проблемы с Docker**: Используйте `docker-compose logs` для диагностики проблем
