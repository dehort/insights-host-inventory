#!/bin/sh
pipenv run gunicorn --log-config=$INVENTORY_LOGGING_CONFIG_FILE -c gunicorn.conf.py -b 0.0.0.0:8080 run
