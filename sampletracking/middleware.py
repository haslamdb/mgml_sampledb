"""
Security middleware for the MGML Sample Database
Provides additional security layers including:
- Request rate limiting
- Suspicious activity detection
- Security headers
- Audit logging
"""

import time
import logging
from collections import defaultdict
from django.http import HttpResponseTooManyRequests, HttpResponseForbidden
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.core.cache import cache

logger = logging.getLogger('security')

class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware for enhanced security monitoring and protection
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = defaultdict(list)
        self.blocked_ips = set()
        
        # Rate limiting settings
        self.max_requests_per_minute = getattr(settings, 'MAX_REQUESTS_PER_MINUTE', 60)
        self.max_requests_per_hour = getattr(settings, 'MAX_REQUESTS_PER_HOUR', 1000)
        self.block_duration = getattr(settings, 'IP_BLOCK_DURATION', 3600)  # 1 hour
        
    def process_request(self, request):
        """
        Process incoming requests for security threats
        """
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Check if IP is blocked
        if self.is_ip_blocked(client_ip):
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return HttpResponseForbidden("Access denied")
        
        # Rate limiting check
        if self.is_rate_limited(client_ip, current_time):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return HttpResponseTooManyRequests("Too many requests")
        
        # Check for suspicious patterns
        if self.detect_suspicious_activity(request):
            logger.critical(f"Suspicious activity detected from IP: {client_ip}")
            self.block_ip(client_ip)
            return HttpResponseForbidden("Suspicious activity detected")
        
        # Log security-relevant requests
        self.log_security_events(request)
        
        return None
    
    def get_client_ip(self, request):
        """
        Get the real client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_rate_limited(self, ip, current_time):
        """
        Check if the IP has exceeded rate limits
        """
        # Clean old entries
        self.request_counts[ip] = [
            timestamp for timestamp in self.request_counts[ip]
            if current_time - timestamp < 3600  # Keep last hour
        ]
        
        # Add current request
        self.request_counts[ip].append(current_time)
        
        # Check minute limit
        minute_requests = sum(
            1 for timestamp in self.request_counts[ip]
            if current_time - timestamp < 60
        )
        
        # Check hour limit
        hour_requests = len(self.request_counts[ip])
        
        return (minute_requests > self.max_requests_per_minute or 
                hour_requests > self.max_requests_per_hour)
    
    def detect_suspicious_activity(self, request):
        """
        Detect various types of suspicious activity
        """
        # Check for common attack patterns in URLs
        suspicious_url_patterns = [
            '../', '..\\', 'etc/passwd', 'cmd.exe', 'shell',
            '<script', 'javascript:', 'php', '.jsp', '.asp',
            'union select', 'drop table', '1=1', 'or 1=1'
        ]
        
        full_path = request.get_full_path().lower()
        if any(pattern in full_path for pattern in suspicious_url_patterns):
            return True
        
        # Check User-Agent for suspicious patterns
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        suspicious_agents = [
            'sqlmap', 'nmap', 'nikto', 'burp', 'dirbuster',
            'wget', 'curl', 'python-requests', 'scanner'
        ]
        
        if any(agent in user_agent for agent in suspicious_agents):
            return True
        
        # Check for excessive POST data
        if request.method == 'POST' and request.META.get('CONTENT_LENGTH'):
            content_length = int(request.META.get('CONTENT_LENGTH', 0))
            if content_length > 10 * 1024 * 1024:  # 10MB limit
                return True
        
        # Check for suspicious headers
        suspicious_headers = ['x-forwarded-host', 'x-real-ip']
        for header in suspicious_headers:
            if header in request.META:
                value = request.META[header].lower()
                if any(pattern in value for pattern in suspicious_url_patterns):
                    return True
        
        return False
    
    def is_ip_blocked(self, ip):
        """
        Check if an IP is currently blocked
        """
        return cache.get(f"blocked_ip_{ip}", False)
    
    def block_ip(self, ip):
        """
        Block an IP address for a specified duration
        """
        cache.set(f"blocked_ip_{ip}", True, self.block_duration)
        logger.critical(f"IP blocked for {self.block_duration} seconds: {ip}")
    
    def log_security_events(self, request):
        """
        Log security-relevant events
        """
        # Log admin access attempts
        if '/admin' in request.path:
            logger.info(f"Admin access: {self.get_client_ip(request)} - {request.user}")
        
        # Log failed authentication attempts
        if 'login' in request.path.lower() and request.method == 'POST':
            logger.info(f"Login attempt: {self.get_client_ip(request)}")
        
        # Log file access attempts
        if any(ext in request.path.lower() for ext in ['.sql', '.bak', '.log', '.conf']):
            logger.warning(f"File access attempt: {self.get_client_ip(request)} - {request.path}")

class ContentSecurityPolicyMiddleware(MiddlewareMixin):
    """
    Add Content Security Policy headers
    """
    
    def process_response(self, request, response):
        """
        Add CSP headers to response
        """
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        response['Content-Security-Policy'] = csp_policy
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response

class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Enhanced session security
    """
    
    def process_request(self, request):
        """
        Check session security
        """
        if request.user.is_authenticated:
            # Check for session hijacking
            stored_ip = request.session.get('_auth_user_ip')
            current_ip = self.get_client_ip(request)
            
            if stored_ip and stored_ip != current_ip:
                logger.critical(f"Possible session hijacking detected: stored IP {stored_ip}, current IP {current_ip}, user {request.user.username}")
                logout(request)
                return HttpResponseForbidden("Session security violation")
            
            # Store IP for future checks
            request.session['_auth_user_ip'] = current_ip
            
            # Check session age
            last_activity = request.session.get('_last_activity')
            current_time = time.time()
            
            if last_activity:
                inactive_time = current_time - last_activity
                max_inactive = getattr(settings, 'SESSION_MAX_INACTIVE', 3600)  # 1 hour
                
                if inactive_time > max_inactive:
                    logger.info(f"Session expired due to inactivity: user {request.user.username}")
                    logout(request)
                    return HttpResponseForbidden("Session expired")
            
            request.session['_last_activity'] = current_time
        
        return None
    
    def get_client_ip(self, request):
        """
        Get the real client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
