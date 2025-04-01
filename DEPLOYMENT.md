# MGML Sample Database - Deployment Guide

## Deployment Strategy

### Central Server Approach (Recommended)
- Host the application on a dedicated lab server
- Set up as a proper web service with a domain name (e.g., samples.yourlabdomain.com)
- Users access via web browsers from their own computers
- Advantages: centralized data management, simpler backups, easier updates

### Hardware Requirements
- Modest server specs: 2-4 CPU cores, 4-8GB RAM, 50GB+ storage
- Could be a repurposed desktop or small server
- Server should be connected to your lab network with a static IP

### Production Setup
- Use Gunicorn as your WSGI server (already in requirements.txt)
- Nginx as a reverse proxy/static file server
- MySQL database (which you're already using)
- Supervisor to manage processes

## Barcode Scanner Integration

### Hardware
- USB barcode scanners work as keyboard emulators - they'll work automatically
- Consider scanners with stands for lab environments
- Wireless scanners give flexibility if users move between stations

### Scan Field Focus
- Add JavaScript to automatically focus the barcode field when page loads
- Implement auto-advance to next field after successful scan

### Validation
- Ensure barcode validation rules match your scanner output format
- Consider prefixing barcodes by sample type (e.g., CS- for crude samples)

## Multi-User Considerations

### User Accounts
- Create individual accounts for all lab members
- Set up roles (admin, technician, read-only)
- Add audit logging to track who created/modified entries

### Concurrent Usage
- Django handles concurrent users well
- Consider adding locking mechanisms for critical operations

### Data Backup
- Implement daily automated database backups
- Store backups in a separate physical location

## Basic Deployment Steps

```bash
# On your server
# 1. Install system dependencies
sudo apt-get update
sudo apt-get install nginx supervisor

# 2. Clone repo and set up environment
git clone https://github.com/yourusername/mgml_sampledb.git
cd mgml_sampledb
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Set up production settings
# Create production .env file with DEBUG=False

# 4. Create Gunicorn service file
sudo nano /etc/systemd/system/mgml_sampledb.service

# Content for service file:
[Unit]
Description=gunicorn daemon for MGML Sample Database
After=network.target

[Service]
User=username
Group=www-data
WorkingDirectory=/path/to/mgml_sampledb
ExecStart=/path/to/mgml_sampledb/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/path/to/mgml_sampledb/mgml_sampledb.sock mgml_sampledb.wsgi:application

[Install]
WantedBy=multi-user.target

# 5. Configure Nginx as reverse proxy
sudo nano /etc/nginx/sites-available/mgml_sampledb

# Content for Nginx config:
server {
    listen 80;
    server_name your_domain.com www.your_domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /path/to/mgml_sampledb;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/mgml_sampledb/mgml_sampledb.sock;
    }
}

# Create symbolic link
sudo ln -s /etc/nginx/sites-available/mgml_sampledb /etc/nginx/sites-enabled

# 6. Set up SSL certificate (Let's Encrypt)
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your_domain.com -d www.your_domain.com

# 7. Collect static files
python manage.py collectstatic

# 8. Start services
sudo systemctl start mgml_sampledb
sudo systemctl enable mgml_sampledb
sudo systemctl restart nginx
```

## Database Backup Script

Create a backup script (backup_db.sh):

```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/path/to/backups"
DB_USER="haslamdb"
DB_NAME="mgml_sampledb"

# Create backup
mysqldump -u $DB_USER -p $DB_NAME > $BACKUP_DIR/mgml_sampledb_$DATE.sql

# Delete backups older than 30 days
find $BACKUP_DIR -name "mgml_sampledb_*.sql" -mtime +30 -delete
```

Add to crontab to run daily:
```
0 2 * * * /path/to/backup_db.sh
```

## Remote Deployment from Home Server

If you want to deploy from a home server and allow remote access:

### Home Server Setup

1. **Set up your home server**:
   - Use your existing hardware or a dedicated machine
   - Install Ubuntu Server or similar OS
   - Follow the same basic setup (Nginx, Gunicorn, MySQL)

2. **Configure port forwarding on your router**:
   - Log into your router admin panel (typically 192.168.1.1)
   - Set up port forwarding for port 80 (HTTP) and 443 (HTTPS)
   - Forward these ports to your server's internal IP address

3. **Use a dynamic DNS service**:
   - Sign up for a free service like No-IP, DuckDNS, or Dynu
   - Install their client on your server to keep your dynamic IP updated
   - This gives you a consistent domain name despite changing IPs

4. **Secure your setup**:
   - **ESSENTIAL**: Set up SSL certificates using Let's Encrypt
   - Configure your firewall (ufw) to only allow necessary ports
   - Use strong passwords and consider setting up fail2ban

5. **Remote access options**:
   - **Option 1**: Direct web access via your dynamic DNS domain
   - **Option 2**: Set up a VPN server (like WireGuard) for more security

### Implementation Steps

```bash
# 1. Assign static internal IP to your server
# Edit /etc/netplan/01-netcfg.yaml on Ubuntu
sudo nano /etc/netplan/01-netcfg.yaml

# Example configuration:
network:
  version: 2
  ethernets:
    ens33:  # Your network interface name (check with `ip a`)
      dhcp4: no
      addresses: [192.168.1.100/24]  # Choose an unused IP on your network
      gateway4: 192.168.1.1          # Your router IP
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]

# Apply configuration
sudo netplan apply

# 2. Install Dynamic DNS client (example for No-IP)
sudo apt-get install noip2
sudo noip2 -C   # Run the configuration wizard

# 3. Configure UFW firewall
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22  # SSH
sudo ufw enable

# 4. For extra security, set up WireGuard VPN (optional)
sudo apt install wireguard
# Follow WireGuard setup instructions
```

### Important Considerations

1. **Security risks**: 
   - Home servers are more vulnerable than commercial hosting
   - Keep your system updated with `sudo apt update && sudo apt upgrade`
   - Monitor logs regularly with `sudo journalctl -xe`
   - Consider using a non-standard port for SSH access

2. **Bandwidth limitations**:
   - Home internet connections often have limited upload bandwidth
   - Check with your ISP about data caps and business use policies
   - Consider implementing caching to reduce bandwidth usage

3. **Reliability concerns**:
   - Home power outages will take your server offline
   - Consider a UPS (Uninterruptible Power Supply)
   - Set up monitoring with something like Uptime Robot or Healthchecks.io
   - Configure automatic restart of services after power loss

4. **Alternative - Cloud Hosting**:
   - Low-cost VPS providers like DigitalOcean ($5-10/month)
   - Significantly better uptime, bandwidth, and security
   - Eliminates ISP and home network concerns
   - Easier to scale if usage increases

## Additional Resources
- Django deployment checklist: https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/
- Nginx documentation: https://nginx.org/en/docs/
- Gunicorn documentation: https://docs.gunicorn.org/en/stable/
- Let's Encrypt: https://letsencrypt.org/docs/
- WireGuard VPN: https://www.wireguard.com/quickstart/
- DuckDNS (Dynamic DNS): https://www.duckdns.org/
- UFW Firewall guide: https://www.digitalocean.com/community/tutorials/how-to-set-up-a-firewall-with-ufw-on-ubuntu-20-04