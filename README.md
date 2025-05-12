# AI Дискуссии

Проект для организации обсуждений между несколькими AI участниками с разными характерами, реализованный на Django.

## Описание проекта

Система позволяет:
1. Пользователям задать вопрос через веб-интерфейс
2. Запустить обсуждение между несколькими AI участниками с разными характерами
3. Получить итоговое резюме обсуждения
4. Просматривать историю всех обсуждений

## Технологии

- Django 5.2
- Google Gemini API
- Bootstrap для интерфейса

## Установка и запуск

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

4. Создайте файл `.env` с вашими API ключами
```
GENAI_API_KEY_1=ваш_ключ_gemini_api
SECRET_KEY=секретный_ключ_django
DEBUG=True
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

## Структура проекта

- `ai_discussion/` - Основное приложение Django
- `characters/` - Файлы с описаниями характеров AI участников
- `discusser_settings.json` - Настройки AI участников
- `utils/` - Утилиты и скрипты (webui.py, bot.py и другие)

## Лицензия

MIT 