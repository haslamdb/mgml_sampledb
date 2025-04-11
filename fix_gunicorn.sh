#!/bin/bash
# Script to fix Gunicorn configuration and restart services

echo "Stopping Gunicorn service..."
sudo systemctl stop mgml_sampledb.service

echo "Creating a backup of the service file..."
sudo cp /etc/systemd/system/mgml_sampledb.service /etc/systemd/system/mgml_sampledb.service.bak

echo "Creating new service file with correct configuration..."
sudo cat > /tmp/mgml_sampledb.service << EOF
[Unit]
Description=Gunicorn daemon for mgml_sampledb
After=network.target

[Service]
User=david
Group=david
WorkingDirectory=/var/www/mgml_sampledb
Environment="DJANGO_SETTINGS_MODULE=mgml_sampledb.mgml_sampledb.settings"
ExecStart=/home/david/miniconda3/envs/biobakery3/bin/gunicorn --access-logfile /var/www/mgml_sampledb/logs/gunicorn_access.log --error-logfile /var/www/mgml_sampledb/logs/gunicorn_error.log --workers 3 --bind unix:/var/www/mgml_sampledb/mgml_sampledb.sock mgml_sampledb.mgml_sampledb.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

echo "Installing new service file..."
sudo cp /tmp/mgml_sampledb.service /etc/systemd/system/mgml_sampledb.service

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Starting Gunicorn service..."
sudo systemctl start mgml_sampledb.service

echo "Checking Gunicorn service status..."
sudo systemctl status mgml_sampledb.service

echo "Restarting Nginx..."
sudo systemctl restart nginx

echo "Done. The application should now be accessible at interface-labs.com"