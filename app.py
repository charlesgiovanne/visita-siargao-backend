# app.py - Direct entry point for Render

import os
import sys
import django

# Add the project directory to the sys.path
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)

# Set environment variable for Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# Configure Django
django.setup()

# Import the Django WSGI application
from django.core.wsgi import get_wsgi_application

# Create the application
app = get_wsgi_application()
