#!/bin/bash
# Script to restart the MGML SampleDB services

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx configuration valid. Restarting Nginx..."
    sudo systemctl restart nginx
else
    echo "Nginx configuration has errors. Please check and fix."
    exit 1
fi

echo "Restarting Gunicorn..."
sudo systemctl restart mgml_sampledb

echo "Services have been restarted."
echo "You can access the database at http://interface-labs.com or https://mgml-sampledb.interface-labs.com"