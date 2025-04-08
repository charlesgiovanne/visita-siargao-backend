"""
WSGI config for backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

# Check if running on Vercel
if 'VERCEL' in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.production')
    # Add the project directory to the sys.path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = get_wsgi_application()

# This is needed for Vercel deployment
app = application
