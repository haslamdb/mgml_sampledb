#!/usr/bin/env python
"""
Test script to check Django configuration
"""
import os
import sys
import django

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mgml_sampledb.mgml_sampledb.settings')

# Add the parent directory to sys.path
sys.path.append('/var/www/mgml_sampledb')

try:
    # Initialize Django
    django.setup()
    
    # Import models to test database connection
    from sampletracking.models import CrudeSample
    
    # Try to query the database
    count = CrudeSample.objects.count()
    
    print("Success! Connected to the database.")
    print(f"Found {count} crude samples in the database.")
    print("Django settings are working correctly.")
    
    # Print the URL patterns
    from django.urls import get_resolver
    resolver = get_resolver()
    print("\nRegistered URL patterns:")
    for pattern in resolver.url_patterns:
        print(f" - {pattern.pattern}")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nDebugging information:")
    print(f"Django version: {django.get_version()}")
    print(f"Python path: {sys.path}")
    print(f"Django settings module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    
    # Print the directory structure
    print("\nProject structure:")
    for root, dirs, files in os.walk('/var/www/mgml_sampledb', topdown=True, maxdepth=3):
        level = root.replace('/var/www/mgml_sampledb', '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            if not f.endswith('.pyc'):
                print(f"{sub_indent}{f}")