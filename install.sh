#!/bin/bash

# Install script for mimir-mvp
# This script installs the package and runs database migrations

set -e  # Exit on any error

echo "Installing mimir-mvp..."

# Install the package in editable mode
pip install -e .

# Run database migrations
alembic upgrade head

echo "Installation complete. You can now use the 'mimir' command."