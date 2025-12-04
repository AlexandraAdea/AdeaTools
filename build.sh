#!/usr/bin/env bash
# AdeaTools Build Script für Render
# Swiss Quality Standard - Production Deployment

set -o errexit  # Exit bei Fehler

echo "🔧 Installing Python dependencies..."
pip install -r requirements.txt

echo "🗄️  Running database migrations..."
python manage.py migrate --noinput

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "✅ Build completed successfully!"

