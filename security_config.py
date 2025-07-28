# Security Configuration for MGML Sample Database
# This file contains security-related configurations and should be imported in settings.py

# Password Validation Settings
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Session Security Settings
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_COOKIE_SECURE = True  # Only send over HTTPS
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
SESSION_COOKIE_SAMESITE = 'Strict'  # CSRF protection
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True  # Update session on every request

# CSRF Protection
CSRF_COOKIE_SECURE = True  # Only send over HTTPS
CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_FAILURE_VIEW = 'sampletracking.views.csrf_failure'

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_SSL_REDIRECT = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")  # Consider removing unsafe-inline
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")   # Consider removing unsafe-inline
CSP_IMG_SRC = ("'self'", "data:")
CSP_FONT_SRC = ("'self'",)
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)

# Rate Limiting Settings
MAX_REQUESTS_PER_MINUTE = 60
MAX_REQUESTS_PER_HOUR = 1000
IP_BLOCK_DURATION = 3600  # 1 hour in seconds

# File Upload Security
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
FILE_UPLOAD_PERMISSIONS = 0o644

# Allowed file types for uploads
ALLOWED_UPLOAD_EXTENSIONS = ['.txt', '.csv', '.xlsx', '.pdf', '.jpg', '.jpeg', '.png']
ALLOWED_CONTENT_TYPES = [
    'text/plain',
    'text/csv', 
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/pdf',
    'image/jpeg',
    'image/png'
]

# Security Middleware Configuration
SECURITY_MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'sampletracking.middleware.SecurityMiddleware',  # Custom security middleware
    'sampletracking.middleware.ContentSecurityPolicyMiddleware',
    'sampletracking.middleware.SessionSecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Logging Configuration for Security
SECURITY_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '[SECURITY] {levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'audit': {
            'format': '[AUDIT] {asctime} {name} {levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/security.log',
            'formatter': 'security',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 10,
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/audit.log',
            'formatter': 'audit',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 10,
        },
        'security_email': {
            'level': 'CRITICAL',
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'security',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security_file', 'security_email'],
            'level': 'WARNING',
            'propagate': False,
        },
        'audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'sampletracking': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Database Security Settings
DATABASE_SECURITY = {
    'CONN_MAX_AGE': 600,  # Connection pooling
    'OPTIONS': {
        'sql_mode': 'STRICT_TRANS_TABLES',
        'charset': 'utf8mb4',
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'autocommit': True,
    },
}

# Email Security Settings
EMAIL_SECURITY = {
    'EMAIL_USE_TLS': True,
    'EMAIL_USE_SSL': False,  # Use TLS instead of SSL
    'EMAIL_TIMEOUT': 10,  # Timeout in seconds
}

# Admin Security Settings
ADMIN_SECURITY = {
    'ADMIN_URL': 'secure-admin-panel/',  # Change from default 'admin/'
    'ADMIN_REORDER': True,
    'ADMIN_INTERFACE_THEME': 'default',
}

# API Security Settings (if you add API endpoints)
API_SECURITY = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    },
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Security Headers to Add
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
}

# Backup and Recovery Settings
BACKUP_SECURITY = {
    'BACKUP_ENCRYPTION': True,
    'BACKUP_RETENTION_DAYS': 90,
    'BACKUP_VERIFICATION': True,
    'BACKUP_LOCATION': '/secure/backups/',
}

# Monitoring and Alerting
MONITORING = {
    'FAILED_LOGIN_THRESHOLD': 5,  # Number of failed logins before alert
    'SUSPICIOUS_ACTIVITY_THRESHOLD': 10,  # Number of suspicious requests before alert
    'ALERT_EMAIL': 'security@yourdomain.com',
    'MONITOR_INTERVAL': 300,  # 5 minutes
}

# Two-Factor Authentication Settings (if implementing)
TWO_FACTOR_AUTH = {
    'ENABLED': False,  # Set to True when ready to implement
    'ISSUER_NAME': 'MGML Sample Database',
    'BACKUP_TOKENS': 10,
    'TOKEN_VALIDITY': 30,  # seconds
}

# IP Whitelist/Blacklist
IP_RESTRICTIONS = {
    'WHITELIST_ENABLED': False,  # Set to True to enable IP whitelisting
    'WHITELIST': [
        # Add trusted IP addresses/ranges
        # '192.168.1.0/24',
        # '10.0.0.0/8',
    ],
    'BLACKLIST': [
        # Add blocked IP addresses/ranges
        # '192.168.1.100',
    ],
}

# Security Scan Settings
SECURITY_SCAN = {
    'ENABLE_VULNERABILITY_SCAN': True,
    'SCAN_FREQUENCY': 'weekly',
    'SCAN_REPORT_EMAIL': 'security@yourdomain.com',
}

# Data Retention and Privacy
DATA_PRIVACY = {
    'DATA_RETENTION_DAYS': 2555,  # 7 years
    'ANONYMIZATION_ENABLED': True,
    'GDPR_COMPLIANCE': True,
    'DATA_EXPORT_ENABLED': True,
    'DATA_DELETION_ENABLED': True,
}
