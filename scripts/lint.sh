#!/bin/bash
# Run all linting and type checking

set -e

echo "🔍 Running linters and type checker..."

# Check if virtual environment exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "📝 Running ruff (linter)..."
ruff check . --fix

echo "🎨 Running ruff format..."
ruff format .

echo "🔎 Running mypy (type checker)..."
mypy bot.py config.py handlers/ models/ services/ utils/ dashboard/ database/__init__.py providers/ core/ --ignore-missing-imports

echo "✅ All checks passed!"