# AI Дискуссии

Проект для организации обсуждений между несколькими AI участниками с разными характерами, реализованный на Django с авторизацией через Firebase.

## Описание проекта

Система позволяет:
1. Пользователям зарегистрироваться и авторизоваться через Firebase
2. Задать вопрос через веб-интерфейс
3. Запустить обсуждение между несколькими AI участниками с разными характерами
4. Получить итоговое резюме обсуждения
5. Просматривать историю своих обсуждений, синхронизированную между устройствами

## Технологии

- Django 5.2
- Google Gemini API
- Firebase Authentication
- Firestore для хранения обсуждений
- Bootstrap для интерфейса

## Установка и запуск

### Настройка Firebase

1. Создайте проект в [Firebase Console](https://console.firebase.google.com/)
2. Включите Authentication и выберите поставщиков авторизации (Email/Password, Google)
3. Создайте базу данных Firestore
4. Добавьте веб-приложение и получите конфигурацию Firebase
5. Создайте сервисный аккаунт Firebase и скачайте JSON-ключ
6. Разместите ключ сервисного аккаунта в корне проекта как `firebase-service-account.json`

### Локальная разработка

1. Клонируйте репозиторий
```
git clone https://github.com/yourusername/ai-discussion.git
cd ai-discussion
```

2. Создайте и активируйте виртуальное окружение
```
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости
```
pip install -r requirements.txt
```

4. Создайте файл `.env` с вашими API ключами и настройками Firebase
```
GENAI_API_KEY_1=ваш_ключ_gemini_api
SECRET_KEY=секретный_ключ_django
DEBUG=True

# Firebase configuration
FIREBASE_API_KEY=ваш_api_key
FIREBASE_AUTH_DOMAIN=ваш_проект.firebaseapp.com
FIREBASE_DATABASE_URL=https://ваш_проект.firebaseio.com
FIREBASE_PROJECT_ID=ваш_проект
FIREBASE_STORAGE_BUCKET=ваш_проект.appspot.com
FIREBASE_MESSAGING_SENDER_ID=ваш_sender_id
FIREBASE_APP_ID=ваш_app_id
```

5. Выполните миграции базы данных
```
python manage.py makemigrations
python manage.py migrate
```

6. Запустите сервер разработки
```
python manage.py runserver
```

### Деплой на Vercel

Проект готов к деплою на Vercel. Вам понадобится:

1. Fork этого репозитория на GitHub
2. Подключите ваш репозиторий к Vercel
3. Настройте переменные окружения в Vercel:
   - `GENAI_API_KEY_1`: ваш ключ API для Google Gemini
   - `SECRET_KEY`: секретный ключ для Django
   - `VERCEL_DEPLOYMENT`: True
   - Добавьте все переменные Firebase, указанные выше
   - `FIREBASE_SERVICE_ACCOUNT`: содержимое файла сервисного аккаунта Firebase в формате JSON

## Структура проекта

- `ai_discussion/` - Основное приложение Django
- `characters/` - Файлы с описаниями характеров AI участников
- `discusser_settings.json` - Настройки AI участников
- `utils/` - Утилиты для Firebase, аутентификации и других функций

## Особенности работы

- Неавторизованные пользователи могут создавать обсуждения, но они не сохраняются между сессиями
- Авторизованные пользователи имеют доступ к истории своих обсуждений
- Обсуждения сохраняются как в БД Django, так и в Firestore для синхронизации между устройствами
- Поддерживается вход через Email/Password и через Google

## Лицензия

MIT