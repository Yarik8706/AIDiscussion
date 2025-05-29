#!/bin/bash
set -e  # сразу прерываемся при ошибке

echo "=== Установка зависимостей ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Применение миграций ==="
python manage.py migrate --noinput

echo "=== Сборка статических файлов ==="
python manage.py collectstatic --noinput

echo "=== Готово ==="