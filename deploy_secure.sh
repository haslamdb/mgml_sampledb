#!/bin/bash

# Security Deployment Script for MGML Sample Database
# This script helps deploy the application with security best practices

set -e  # Exit on any error

echo "🛡️  MGML Sample Database - Security Deployment Script"
echo "===================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="mgml_sampledb"
APP_USER="django"
APP_DIR="/var/www/$APP_NAME"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="/var/log/$APP_NAME"
BACKUP_DIR="/var/backups/$APP_NAME"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root for security reasons."
        print_status "Please run as the application user: $APP_USER"
        exit 1
    fi
}

# Create application user if it doesn't exist
create_app_user() {
    if ! id "$APP_USER" &>/dev/null; then
        print_status "Creating application user: $APP_USER"
        sudo adduser --system --group --home $APP_DIR $APP_USER
        sudo usermod -s /bin/bash $APP_USER
    else
        print_status "Application user $APP_USER already exists"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating application directories..."
    
    sudo mkdir -p $APP_DIR
    sudo mkdir -p $LOG_DIR
    sudo mkdir -p $BACKUP_DIR
    sudo mkdir -p $APP_DIR/static
    sudo mkdir -p $APP_DIR/media
    sudo mkdir -p $APP_DIR/logs
    
    # Set ownership
    sudo chown -R $APP_USER:$APP_USER $APP_DIR
    sudo chown -R $APP_USER:$APP_USER $LOG_DIR
    sudo chown -R $APP_USER:$APP_USER $BACKUP_DIR
    
    # Set permissions
    sudo chmod 750 $APP_DIR
    sudo chmod 750 $LOG_DIR
    sudo chmod 750 $BACKUP_DIR
    sudo chmod 755 $APP_DIR/static
    sudo chmod 755 $APP_DIR/media
}

# Install system dependencies
install_system_dependencies() {
    print_status "Installing system dependencies..."
    
    sudo apt update
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        libmysqlclient-dev \
        pkg-config \
        nginx \
        mysql-server \
        redis-server \
        ufw \
        fail2ban \
        logrotate \
        certbot \
        python3-certbot-nginx \
        git \
        htop \
        curl \
        wget
}

# Setup firewall
setup_firewall() {
    print_status "Configuring firewall..."
    
    # Reset UFW to defaults
    sudo ufw --force reset
    
    # Default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH (adjust port if needed)
    sudo ufw allow 22/tcp
    
    # Allow HTTP and HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Allow MySQL (only from localhost)
    sudo ufw allow from 127.0.0.1 to any port 3306
    
    # Allow Redis (only from localhost)
    sudo ufw allow from 127.0.0.1 to any port 6379
    
    # Enable firewall
    sudo ufw --force enable
    
    print_status "Firewall configured and enabled"
}

# Setup fail2ban
setup_fail2ban() {
    print_status "Configuring fail2ban..."
    
    sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
backend = systemd

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6

[nginx-badbots]
enabled = true
port = http,https
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2

[nginx-noproxy]
enabled = true
port = http,https
filter = nginx-noproxy
logpath = /var/log/nginx/access.log
maxretry = 2
EOF

    sudo systemctl enable fail2ban
    sudo systemctl restart fail2ban
    
    print_status "Fail2ban configured and started"
}

# Setup Python virtual environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."
    
    cd $APP_DIR
    
    # Create virtual environment
    python3 -m venv $VENV_DIR
    
    # Activate virtual environment
    source $VENV_DIR/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install wheel for faster package compilation
    pip install wheel
    
    print_status "Python virtual environment created"
}

# Install Python dependencies
install_python_dependencies() {
    print_status "Installing Python dependencies..."
    
    cd $APP_DIR
    source $VENV_DIR/bin/activate
    
    # Install from requirements file
    if [ -f "requirements_secure.txt" ]; then
        pip install -r requirements_secure.txt
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        print_error "No requirements file found!"
        exit 1
    fi
    
    print_status "Python dependencies installed"
}

# Setup database security
setup_database_security() {
    print_status "Configuring database security..."
    
    # Secure MySQL installation
    print_warning "Please run 'sudo mysql_secure_installation' manually after this script"
    
    # Create database and user
    read -p "Enter database name [$APP_NAME]: " DB_NAME
    DB_NAME=${DB_NAME:-$APP_NAME}
    
    read -p "Enter database username [$APP_NAME_user]: " DB_USER
    DB_USER=${DB_USER:-${APP_NAME}_user}
    
    read -s -p "Enter database password: " DB_PASSWORD
    echo
    
    # Create database
    sudo mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    sudo mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
    sudo mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
    sudo mysql -e "FLUSH PRIVILEGES;"
    
    print_status "Database configured"
}

# Setup environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f "$APP_DIR/.env" ]; then
        # Generate secret key
        SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
        
        # Create .env file
        cat > $APP_DIR/.env <<EOF
# Django Configuration
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=3306

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Redis Configuration
REDIS_URL=redis://127.0.0.1:6379/1

# Email Configuration
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com

# Admin Configuration
ADMIN_URL=secure-admin-panel/
EOF
        
        # Set permissions
        chmod 600 $APP_DIR/.env
        chown $APP_USER:$APP_USER $APP_DIR/.env
        
        print_status "Environment file created"
        print_warning "Please edit $APP_DIR/.env with your actual configuration"
    else
        print_status "Environment file already exists"
    fi
}

# Setup Django application
setup_django() {
    print_status "Setting up Django application..."
    
    cd $APP_DIR
    source $VENV_DIR/bin/activate
    
    # Run migrations
    python manage.py migrate
    
    # Collect static files
    python manage.py collectstatic --noinput
    
    # Create superuser (interactive)
    print_status "Creating Django superuser..."
    python manage.py createsuperuser
    
    print_status "Django application configured"
}

# Setup systemd service
setup_systemd_service() {
    print_status "Setting up systemd service..."
    
    sudo tee /etc/systemd/system/$APP_NAME.service > /dev/null <<EOF
[Unit]
Description=MGML Sample Database Gunicorn Application
After=network.target

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn --workers 3 --bind unix:$APP_DIR/$APP_NAME.sock mgml_sampledb.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable $APP_NAME
    sudo systemctl start $APP_NAME
    
    print_status "Systemd service configured and started"
}

# Setup Nginx
setup_nginx() {
    print_status "Setting up Nginx..."
    
    sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root $APP_DIR;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        root $APP_DIR;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/$APP_NAME.sock;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Disable server tokens
    server_tokens off;
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone \$binary_remote_addr zone=api:10m rate=100r/m;
    
    location /login/ {
        limit_req zone=login burst=5 nodelay;
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/$APP_NAME.sock;
    }
}
EOF

    # Enable site
    sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    
    # Remove default site
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test configuration
    sudo nginx -t
    
    # Restart Nginx
    sudo systemctl restart nginx
    
    print_status "Nginx configured and restarted"
}

# Setup SSL with Let's Encrypt
setup_ssl() {
    print_status "Setting up SSL certificate..."
    
    read -p "Enter your domain name: " DOMAIN_NAME
    
    if [ ! -z "$DOMAIN_NAME" ]; then
        sudo certbot --nginx -d $DOMAIN_NAME
        
        # Setup auto-renewal
        sudo crontab -l | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -
        
        print_status "SSL certificate installed and auto-renewal configured"
    else
        print_warning "No domain provided, skipping SSL setup"
    fi
}

# Setup log rotation
setup_log_rotation() {
    print_status "Setting up log rotation..."
    
    sudo tee /etc/logrotate.d/$APP_NAME > /dev/null <<EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 $APP_USER $APP_USER
    postrotate
        systemctl reload $APP_NAME
    endscript
}
EOF

    print_status "Log rotation configured"
}

# Setup backup script
setup_backup() {
    print_status "Setting up backup script..."
    
    sudo tee /usr/local/bin/${APP_NAME}_backup.sh > /dev/null <<EOF
#!/bin/bash

# Backup script for $APP_NAME
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${APP_NAME}_backup_\$DATE.sql"

# Create database backup
mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME > \$BACKUP_FILE

# Compress backup
gzip \$BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "${APP_NAME}_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: \${BACKUP_FILE}.gz"
EOF

    sudo chmod +x /usr/local/bin/${APP_NAME}_backup.sh
    
    # Setup daily backup cron job
    (sudo crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/${APP_NAME}_backup.sh") | sudo crontab -
    
    print_status "Backup script configured with daily cron job"
}

# Security audit
run_security_audit() {
    print_status "Running security audit..."
    
    cd $APP_DIR
    source $VENV_DIR/bin/activate
    
    # Django security check
    python manage.py check --deploy
    
    # Run custom security audit
    if python manage.py help | grep -q "security_audit"; then
        python manage.py security_audit --days 7
    fi
    
    print_status "Security audit completed"
}

# Main deployment function
main() {
    print_status "Starting secure deployment of MGML Sample Database..."
    
    # Check if not root
    check_root
    
    # Create application user
    create_app_user
    
    # Create directories
    create_directories
    
    # Install system dependencies
    install_system_dependencies
    
    # Setup firewall
    setup_firewall
    
    # Setup fail2ban
    setup_fail2ban
    
    # Setup Python environment
    setup_python_env
    
    # Install Python dependencies
    install_python_dependencies
    
    # Setup database security
    setup_database_security
    
    # Setup environment
    setup_environment
    
    # Setup Django
    setup_django
    
    # Setup systemd service
    setup_systemd_service
    
    # Setup Nginx
    setup_nginx
    
    # Setup SSL
    setup_ssl
    
    # Setup log rotation
    setup_log_rotation
    
    # Setup backup
    setup_backup
    
    # Run security audit
    run_security_audit
    
    print_status "✅ Secure deployment completed successfully!"
    print_warning "Please review and update the configuration files as needed:"
    print_warning "- $APP_DIR/.env"
    print_warning "- /etc/nginx/sites-available/$APP_NAME"
    print_warning "- /etc/systemd/system/$APP_NAME.service"
    
    print_status "Next steps:"
    print_status "1. Update DNS records to point to this server"
    print_status "2. Test the application thoroughly"
    print_status "3. Setup monitoring and alerting"
    print_status "4. Review security logs regularly"
    print_status "5. Keep the system and dependencies updated"
}

# Run main function
main "$@"
