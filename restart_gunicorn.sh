#!/bin/bash
# Script to restart Gunicorn for MGML Sample Database

echo "Restarting Gunicorn for MGML Sample Database..."

# Kill existing Gunicorn processes
echo "Stopping existing Gunicorn processes..."
pkill -f 'gunicorn.*mgml_sampledb'
sleep 2

# Set the Django settings module
export DJANGO_SETTINGS_MODULE=mgml_sampledb.settings

# Change to the project directory
cd /var/www/mgml_sampledb

# Start Gunicorn in daemon mode
echo "Starting Gunicorn..."
/var/www/mgml_sampledb/venv/bin/gunicorn \
    --access-logfile /var/www/mgml_sampledb/logs/gunicorn_access.log \
    --error-logfile /var/www/mgml_sampledb/logs/gunicorn_error.log \
    --workers 3 \
    --bind unix:/var/www/mgml_sampledb/mgml_sampledb.sock \
    mgml_sampledb.wsgi:application \
    --daemon

# Check if Gunicorn started successfully
sleep 2
if pgrep -f 'gunicorn.*mgml_sampledb' > /dev/null
then
    echo "✅ Gunicorn restarted successfully!"
    echo "Gunicorn processes:"
    ps aux | grep '[g]unicorn.*mgml_sampledb' | head -5
else
    echo "❌ Failed to start Gunicorn. Check logs at /var/www/mgml_sampledb/logs/gunicorn_error.log"
fi