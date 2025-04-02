# Как получить файл firebase-credentials.json

Файл `firebase-credentials.json` содержит учетные данные для аутентификации вашего приложения в Firebase. Вот пошаговая инструкция по его получению:

## Шаг 1: Создайте проект Firebase

1. Перейдите на [консоль Firebase](https://console.firebase.google.com/)
2. Нажмите на кнопку "Создать проект" (или "Add project")
3. Введите название проекта (например, "GuateFit")
4. Следуйте инструкциям мастера создания проекта
   - Можно отключить Google Analytics, если он вам не нужен
   - Или включить его и настроить согласно вашим требованиям
5. Дождитесь создания проекта и нажмите "Продолжить"

## Шаг 2: Настройте Firestore Database

1. В боковом меню консоли Firebase выберите "Firestore Database"
2. Нажмите "Создать базу данных"
3. Выберите режим работы (рекомендуется начать с "Тестового режима" для разработки)
4. Выберите ближайший к вашим пользователям регион размещения
5. Нажмите "Создать"

## Шаг 3: Создайте учетные данные сервисного аккаунта

1. В консоли Firebase перейдите в раздел "Настройки проекта" (значок шестеренки в верхнем левом углу)
2. Перейдите на вкладку "Сервисные аккаунты"
3. В разделе "Firebase Admin SDK" нажмите кнопку "Создать ключ" (или "Generate new private key")
4. Нажмите "Создать ключ" в появившемся диалоговом окне
5. Файл JSON автоматически скачается на ваш компьютер
6. Переименуйте скачанный файл в `firebase-credentials.json`

## Шаг 4: Настройте проект для использования учетных данных

1. Переместите файл `firebase-credentials.json` в корневую директорию вашего проекта
2. Убедитесь, что этот файл добавлен в `.gitignore`, чтобы не загружать его в публичный репозиторий
3. Обновите файл `.env` с правильным путем к файлу:

```
FIREBASE_CREDENTIALS=firebase-credentials.json
FIREBASE_DATABASE_URL=https://YOUR-PROJECT-ID.firebaseio.com
```

Замените YOUR-PROJECT-ID на ID вашего проекта Firebase, который можно найти в настройках проекта.

## Шаг 5: Настройте правила безопасности Firestore

В продакшен-окружении рекомендуется настроить правила безопасности Firestore для защиты ваших данных:

1. В консоли Firebase перейдите в раздел "Firestore Database"
2. Перейдите на вкладку "Правила"
3. Настройте правила безопасности в соответствии с вашими требованиями, например:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    match /products/{document=**} {
      allow read: if true;
      allow write: if request.auth != null && request.auth.token.admin == true;
    }
    match /diet_plans/{planId} {
      allow read: if request.auth != null && resource.data.user_id == request.auth.uid;
      allow write: if request.auth != null && request.resource.data.user_id == request.auth.uid;
    }
  }
}
```

## Примечания по безопасности

- **Никогда не публикуйте** файл `firebase-credentials.json` в публичных репозиториях
- В продакшен-окружении храните его в безопасном месте (например, в секретах Docker или Kubernetes)
- Для локальной разработки используйте путь к файлу, а для продакшен-окружения можно использовать переменные окружения

После получения и настройки файла `firebase-credentials.json`, вы сможете успешно запустить проект GuateFit и использовать Firestore для хранения данных пользователей, диет и продуктов.