#!/bin/bash
# Установка пакетов из requirements.txt
pip install -r requirements.txt

# Сборка статических файлов
python manage.py collectstatic --noinput

# Миграции базы данных
python manage.py makemigrations
python manage.py migrate 