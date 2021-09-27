#!/bin/sh

if [ "$DATABASE" = "mysql" ]
then
    echo "Waiting for mysql..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "MySql started"

    # Collect static files
    echo "Collect static files"
    python manage.py collectstatic --noinput

    # Apply database migrations
    echo "Apply database migrations"
    python manage.py makemigrations
    python manage.py migrate

fi

exec "$@"