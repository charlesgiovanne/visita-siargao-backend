# vercel_app.py - Simplified entry point for Vercel

import os
import sys

# Add the project directory to the sys.path
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path)

# Set environment variable for Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# Import Django and set up the application
import django
django.setup()

# Import the Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# This is needed for Vercel
app = application
