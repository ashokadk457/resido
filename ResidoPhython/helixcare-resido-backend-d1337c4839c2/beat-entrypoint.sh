#!/bin/sh
until cd /resido_dev
do
    echo "Waiting for server volume...."
done
celery -A resido beat --loglevel=info

