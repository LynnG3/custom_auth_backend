#!/bin/sh

set -e

# Ждем, пока база данных будет доступна
echo "Waiting for database..."
sleep 5

echo "Applying migrations..."
python manage.py makemigrations
python manage.py migrate || true
python manage.py collectstatic --noinput

echo "Creating superuser..."
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py createsuperuser \
        --noinput \
        --email "$DJANGO_SUPERUSER_EMAIL" \
        --first_name "Admin" \
        --last_name "User" || \
    echo "Superuser already exists"
fi

echo "Starting Gunicorn..."

GUNICORN_PORT=${GUNICORN_PORT:-8000}

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${GUNICORN_PORT} \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --reload