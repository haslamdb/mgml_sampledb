#!/bin/bash
# Script to check the status of the MGML SampleDB application

echo "===== MGML SampleDB Status Check ====="
echo ""

echo "1. Checking if Nginx is running..."
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running"
else
    echo "❌ Nginx is NOT running"
fi

echo ""
echo "2. Checking if Gunicorn service is running..."
if systemctl is-active --quiet mgml_sampledb.service; then
    echo "✅ Gunicorn service is running"
else
    echo "❌ Gunicorn service is NOT running"
fi

echo ""
echo "3. Checking if socket file exists..."
if [ -S "/var/www/mgml_sampledb/mgml_sampledb.sock" ]; then
    echo "✅ Socket file exists"
    ls -la /var/www/mgml_sampledb/mgml_sampledb.sock
else
    echo "❌ Socket file does NOT exist"
fi

echo ""
echo "4. Checking if the database is accessible..."
# This requires Python to run a small script that checks database connectivity
echo "from sampletracking.models import CrudeSample; print('Database connection successful. Found %s crude samples.' % CrudeSample.objects.count())" > /tmp/check_db.py
cd /var/www/mgml_sampledb
export DJANGO_SETTINGS_MODULE=mgml_sampledb.settings
if python -c "import django; django.setup(); exec(open('/tmp/check_db.py').read())"; then
    echo "✅ Database is accessible"
else
    echo "❌ Database connection FAILED"
fi

echo ""
echo "5. Checking Nginx configuration..."
sudo nginx -t

echo ""
echo "6. Recent Gunicorn logs..."
if [ -f "/var/www/mgml_sampledb/logs/gunicorn_error.log" ]; then
    echo "Last 10 lines of Gunicorn error log:"
    tail -n 10 /var/www/mgml_sampledb/logs/gunicorn_error.log
else
    echo "Gunicorn error log not found"
fi

echo ""
echo "7. Recent Nginx logs..."
if [ -f "/var/log/nginx/error.log" ]; then
    echo "Last 10 lines of Nginx error log:"
    tail -n 10 /var/log/nginx/error.log
else
    echo "Nginx error log not found"
fi

echo ""
echo "===== Status Check Complete ====="
echo ""
echo "To access the application:"
echo "- Website: https://mgml-sampledb.com or https://www.mgml-sampledb.com"
echo ""
echo "If there are issues:"
echo "1. Run the fix_gunicorn.sh script to update the Gunicorn service configuration"
echo "2. Check logs in /var/www/mgml_sampledb/logs/ for application errors"
echo "3. Check logs in /var/log/nginx/ for web server errors"