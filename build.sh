#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories if they don't exist
mkdir -p staticfiles
mkdir -p media

# Collect static files and run migrations
python manage.py collectstatic --no-input
python manage.py migrate
