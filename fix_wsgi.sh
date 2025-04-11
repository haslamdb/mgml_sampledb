#\!/bin/bash

# Check if we're running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

echo "Stopping all gunicorn processes..."
pkill -f gunicorn

echo "Updating service file..."
cat > /etc/systemd/system/mgml_sampledb.service << INNEREOF
[Unit]
Description=Gunicorn daemon for mgml_sampledb
After=network.target

[Service]
User=david
Group=david
WorkingDirectory=/var/www/mgml_sampledb
Environment="DJANGO_SETTINGS_MODULE=mgml_sampledb.settings"
ExecStart=/home/david/miniconda3/envs/biobakery3/bin/gunicorn --access-logfile /var/www/mgml_sampledb/logs/gunicorn_access.log --error-logfile /var/www/mgml_sampledb/logs/gunicorn_error.log --workers 3 --bind unix:/var/www/mgml_sampledb/mgml_sampledb.sock mgml_sampledb.wsgi:application

[Install]
WantedBy=multi-user.target
INNEREOF

echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Starting Gunicorn service..."
systemctl start mgml_sampledb.service

echo "Checking Gunicorn service status..."
systemctl status mgml_sampledb.service

echo "Restarting Nginx..."
systemctl restart nginx

echo "Done."
