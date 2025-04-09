#!/usr/bin/env bash
# exit on error
set -o errexit

# Update pip first
pip install --upgrade pip

# Then install requirements
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
