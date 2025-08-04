#!/bin/bash

# Build script for deployment

echo "Starting build process..."

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

echo "Build completed successfully!" 