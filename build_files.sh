#!/bin/bash
set -e  # сразу прерываемся при ошибке

echo "=== Установка зависимостей ==="
pip3 install --upgrade pip
pip3 install -r requirements.txt

echo "=== Применение миграций ==="
python manage.py migrate --noinput

echo "=== Сборка статических файлов ==="
python manage.py collectstatic --noinput

echo "=== Готово ==="