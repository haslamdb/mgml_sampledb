#!/bin/bash
# Script to start Gunicorn with the correct configuration

# Activate the virtual environment if needed
# source /path/to/venv/bin/activate

# Set the Django settings module
export DJANGO_SETTINGS_MODULE=mgml_sampledb.settings

# Change to the project directory
cd /var/www/mgml_sampledb

# Start Gunicorn
/var/www/mgml_sampledb/venv/bin/gunicorn \
    --access-logfile /var/www/mgml_sampledb/logs/gunicorn_access.log \
    --error-logfile /var/www/mgml_sampledb/logs/gunicorn_error.log \
    --workers 3 \
    --bind unix:/var/www/mgml_sampledb/mgml_sampledb.sock \
    mgml_sampledb.wsgi:application