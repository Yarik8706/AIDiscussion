#!/bin/bash
set -e  # сразу прерываемся при ошибке

echo "=== Установка зависимостей ==="
pip3 install --upgrade pip
pip3 install -r requirements.txt

echo "=== Применение миграций ==="
python3 manage.py migrate --noinput

echo "=== Сборка статических файлов ==="
python3 manage.py collectstatic --noinput

echo "=== Готово ==="