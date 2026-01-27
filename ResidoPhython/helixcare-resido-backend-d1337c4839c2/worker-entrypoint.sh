#!/bin/sh
until cd /resido_dev
do
    echo "Waiting for server volume..."
done
celery -A resido worker --loglevel=info -Q celery,tenant_launch
