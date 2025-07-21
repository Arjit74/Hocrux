#!/bin/bash

# ASL Translator - Run Script
# This script activates the virtual environment and starts the application

# Check if we're in the correct directory
if [ ! -f "src/main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Activate the virtual environment
if [ -d "venv" ]; then
    echo "🔍 Found virtual environment"
    if [ "$OSTYPE" == "msys" ] || [ "$OSTYPE" == "cygwin" ]; then
        # Windows
        source venv/Scripts/activate
    else
        # Unix/Linux/MacOS
        source venv/bin/activate
    fi
else
    echo "❌ Error: Virtual environment not found. Please run 'scripts/install.sh' first."
    exit 1
fi

# Check if requirements are installed
if ! pip show -q opencv-python mediapipe pyyaml loguru; then
    echo "⚠️  Some required packages are missing. Installing..."
    pip install -r requirements.txt
fi

# Create required directories if they don't exist
mkdir -p logs
mkdir -p output

# Run the application
echo "🚀 Starting ASL Translator..."
python src/main.py "$@"

# Deactivate the virtual environment when done
deactivate 2>/dev/null || true

echo "👋 ASL Translator has exited"
