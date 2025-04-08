# app.py - Direct entry point for Render

import os
import sys

# Add the project directory to the sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment variable for Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# Import Django and set up the application
import django
django.setup()

# Import the Django WSGI application
from django.core.wsgi import get_wsgi_application

# Create the application
app = get_wsgi_application()
