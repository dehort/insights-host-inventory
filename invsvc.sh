#!/bin/sh
export prometheus_multiproc_dir="/tmp"
export INVENTORY_DB_NAME="insights"
export INVENTORY_LOGGING_CONFIG_FILE="logconfig.ini"
export FLASK_DEBUG=1 
export NOAUTH=1 
pipenv run gunicorn --log-config=$INVENTORY_LOGGING_CONFIG_FILE -c gunicorn.conf.py -b 0.0.0.0:8080 run
