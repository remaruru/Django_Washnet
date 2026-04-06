#!/usr/bin/env bash
# build.sh — Render build script for WASHNET POS
set -o errexit  # Exit immediately if any command fails

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --no-input

echo "==> Running database migrations..."
python manage.py migrate

echo "==> Seeding default users..."
python make_dev_users.py

echo "==> Seeding default services & products..."
python make_dev_items.py

echo "==> Build complete!"
