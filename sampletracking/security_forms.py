"""
Enhanced security forms for the MGML Sample Database
Provides additional validation and security measures
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import re
import logging

logger = logging.getLogger('security')

class SecureLoginForm(AuthenticationForm):
    """
    Enhanced login form with additional security validation
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'autocomplete': 'username',
            'maxlength': 150,
            'pattern': '[a-zA-Z0-9@.+_-]+',
            'title': 'Username can only contain letters, numbers, and @.+_- characters'
        })
        self.fields['password'].widget.attrs.update({
            'autocomplete': 'current-password',
            'maxlength': 128
        })
    
    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        
        # Basic validation
        if not username:
            raise ValidationError("Username is required.")
        
        # Length validation
        if len(username) > 150:
            raise ValidationError("Username is too long.")
        
        # Character validation
        if not re.match(r'^[a-zA-Z0-9@.+_-]+$', username):
            logger.warning(f"Invalid username format attempted: {username}")
            raise ValidationError("Username contains invalid characters.")
        
        # Check for suspicious patterns
        suspicious_patterns = ['admin', 'root', 'test', 'guest', 'anonymous']
        if any(pattern in username.lower() for pattern in suspicious_patterns):
            if not User.objects.filter(username=username).exists():
                logger.warning(f"Suspicious username attempted: {username}")
                raise ValidationError("Invalid username.")
        
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            # Log login attempt
            logger.info(f"Login attempt for username: {username}")
        
        return cleaned_data

class SecurePasswordChangeForm(PasswordChangeForm):
    """
    Enhanced password change form with additional validation
    """
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        
        if not password:
            raise ValidationError("Password is required.")
        
        # Length validation
        if len(password) < 12:
            raise ValidationError("Password must be at least 12 characters long.")
        
        # Complexity validation
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one number.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Password must contain at least one special character.")
        
        # Check for common patterns
        common_patterns = ['123', 'abc', 'password', 'qwerty', 'admin']
        if any(pattern in password.lower() for pattern in common_patterns):
            raise ValidationError("Password contains common patterns and is not secure.")
        
        return password

class SecureBarcodeForm(forms.Form):
    """
    Secure form for barcode input with validation
    """
    barcode = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter barcode',
            'pattern': '[A-Za-z0-9_-]+',
            'title': 'Barcode can only contain letters, numbers, underscores, and hyphens',
            'autocomplete': 'off'
        })
    )
    
    def clean_barcode(self):
        barcode = self.cleaned_data.get('barcode', '').strip()
        
        # Basic validation
        if not barcode:
            raise ValidationError("Barcode is required.")
        
        # Length validation
        if len(barcode) > 255:
            raise ValidationError("Barcode is too long.")
        
        if len(barcode) < 3:
            raise ValidationError("Barcode is too short.")
        
        # Character validation
        if not re.match(r'^[A-Za-z0-9_-]+$', barcode):
            logger.warning(f"Invalid barcode format: {barcode}")
            raise ValidationError("Barcode contains invalid characters.")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            '<script', 'javascript:', 'DROP', 'DELETE', 'INSERT', 
            'UPDATE', 'SELECT', '--', ';', '/*', '*/'
        ]
        
        if any(pattern.lower() in barcode.lower() for pattern in suspicious_patterns):
            logger.critical(f"Suspicious barcode pattern: {barcode}")
            raise ValidationError("Invalid barcode format.")
        
        return barcode

class SecureSearchForm(forms.Form):
    """
    Secure form for search queries with validation
    """
    query = forms.CharField(
        max_length=100,
        min_length=2,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search samples...',
            'autocomplete': 'off',
            'maxlength': 100
        })
    )
    
    def clean_query(self):
        query = self.cleaned_data.get('query', '').strip()
        
        # Basic validation
        if not query:
            raise ValidationError("Search query is required.")
        
        # Length validation
        if len(query) < 2:
            raise ValidationError("Search query is too short.")
        
        if len(query) > 100:
            raise ValidationError("Search query is too long.")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            '<script', 'javascript:', 'DROP TABLE', 'DELETE FROM', 
            'INSERT INTO', 'UPDATE ', 'SELECT * FROM', '--', ';',
            'UNION SELECT', '1=1', 'OR 1=1', 'XSS', 'SCRIPT'
        ]
        
        if any(pattern.lower() in query.lower() for pattern in suspicious_patterns):
            logger.warning(f"Suspicious search query: {query}")
            raise ValidationError("Invalid search query.")
        
        # Check for excessive special characters
        special_char_count = sum(1 for char in query if not char.isalnum() and char not in ' -_.')
        if special_char_count > len(query) * 0.3:  # More than 30% special chars
            raise ValidationError("Search query contains too many special characters.")
        
        return query

def validate_file_upload(file):
    """
    Validate file uploads for security
    """
    if not file:
        raise ValidationError("No file provided.")
    
    # Size validation (5MB limit)
    if file.size > 5 * 1024 * 1024:
        raise ValidationError("File size too large. Maximum size is 5MB.")
    
    # Extension validation
    allowed_extensions = ['.txt', '.csv', '.xlsx', '.pdf', '.jpg', '.jpeg', '.png']
    file_extension = file.name.lower().split('.')[-1] if '.' in file.name else ''
    
    if f'.{file_extension}' not in allowed_extensions:
        logger.warning(f"Unauthorized file upload attempt: {file.name}")
        raise ValidationError("File type not allowed.")
    
    # Content type validation
    allowed_content_types = [
        'text/plain', 'text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/pdf', 'image/jpeg', 'image/png'
    ]
    
    if file.content_type not in allowed_content_types:
        logger.warning(f"Invalid content type upload: {file.content_type}")
        raise ValidationError("Invalid file content type.")
    
    return file

class SecureFileUploadForm(forms.Form):
    """
    Secure file upload form
    """
    file = forms.FileField(validators=[validate_file_upload])
    description = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'rows': 3})
    )
    
    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        
        if description:
            # Check for suspicious content
            suspicious_patterns = ['<script', 'javascript:', 'onclick', 'onerror']
            if any(pattern.lower() in description.lower() for pattern in suspicious_patterns):
                logger.warning(f"Suspicious file description: {description}")
                raise ValidationError("Description contains invalid content.")
        
        return description
