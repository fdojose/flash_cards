#!/bin/bash

# Virtual Environment Activation Script for Flashcard Learning System
# This script activates the Python virtual environment and sets up the development environment

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"

echo "🐍 Flashcard Learning System - Environment Setup"
echo "📁 Project Root: $PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "🔨 Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🚀 Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Check if requirements are installed
echo "📦 Checking dependencies..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "🔧 Installing backend dependencies..."
    pip install --upgrade pip
    pip install -r backend/requirements.txt
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

# Set environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "🔐 Loading environment variables from .env"
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
else
    echo "⚠️  No .env file found. Copying from .env.example..."
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo "✅ Created .env file from template"
    fi
fi

echo ""
echo "🎉 Environment ready!"
echo ""
echo "💡 Available commands:"
echo "  • Start backend: cd backend && python main.py"
echo "  • Start with Docker: ./start_dev.sh"
echo "  • Run tests: cd backend && pytest"
echo "  • API docs: http://localhost:8000/docs"
echo ""
echo "🔍 Current Python: $(which python)"
echo "🔍 Python version: $(python --version)"
echo ""

# Start a new shell with the environment activated
exec "$SHELL"
