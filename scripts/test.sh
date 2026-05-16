#!/bin/bash
# Run all tests with coverage

set -e

echo "🧪 Running tests..."

# Check if virtual environment exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run tests with coverage
echo "📊 Running pytest with coverage..."
pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

echo "✅ Tests completed!"
echo "📈 Coverage report: coverage_html/index.html"