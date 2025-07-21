#!/bin/bash

# ASL Translator - Installation Script
# This script sets up the Python virtual environment and installs dependencies

echo "🚀 Setting up ASL Translator..."

# Create a Python virtual environment
echo "🔧 Creating Python virtual environment..."
python -m venv venv

# Activate the virtual environment
if [ "$OSTYPE" == "msys" ] || [ "$OSTYPE" == "cygwin" ]; then
    # Windows
    source venv/Scripts/activate
else
    # Unix/Linux/MacOS
    source venv/bin/activate
fi

# Upgrade pip
echo "🔄 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating required directories..."
mkdir -p logs
mkdir -p output
mkdir -p models
mkdir -p assets

# Set execute permissions for Python scripts (Unix-like systems)
if [ "$OSTYPE" != "msys" ] && [ "$OSTYPE" != "cygwin" ]; then
    chmod +x src/*.py
    chmod +x scripts/*.sh
fi

echo "✅ Setup complete!"
echo "To activate the virtual environment, run:"

if [ "$OSTYPE" == "msys" ] || [ "$OSTYPE" == "cygwin" ]; then
    echo "source venv/Scripts/activate"
else
    echo "source venv/bin/activate"
fi

echo "\nThen, you can run the application with:"
echo "python src/main.py"
