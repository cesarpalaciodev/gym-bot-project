#!/bin/bash
# Start the application locally

set -e

echo "🚀 Starting GymBot..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env with your configuration"
    exit 1
fi

# Create necessary directories
mkdir -p logs reports data

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "✅ Activating virtual environment..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
fi

# Run the bot
echo "🤖 Starting bot..."
python bot.py