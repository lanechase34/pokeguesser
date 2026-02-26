#!/bin/sh

echo "Running migrations..."
python manage.py migrate

echo "Creating cache table if not exists..."
python manage.py createcachetable

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8085
