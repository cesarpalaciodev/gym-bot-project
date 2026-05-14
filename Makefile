.PHONY: install lint typecheck test format clean docker-build docker-up security

# Install all dependencies
install:
	pip install -r requirements.txt
	pip install pytest pytest-cov mypy ruff pre-commit bandit safety

# Lint with ruff (fast)
lint:
	ruff check .

# Type check with mypy
typecheck:
	mypy bot.py config.py database/ handlers/ keyboards.py models/ utils/

# Format code with ruff
format:
	ruff format .

# Run all tests with coverage
test:
	pytest --cov=. --cov-report=term-missing -v

# Run only integration tests (needs MongoDB)
test-integration:
	pytest -m integration -v

# Security scan
security:
	bandit -r bot.py config.py database/ handlers/ keyboards.py models/ utils/
	safety check -r requirements.txt

# Pre-commit setup
precommit-install:
	pre-commit install

precommit-run:
	pre-commit run --all-files

# Docker
docker-build:
	docker build -t gym-bot:latest .

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Cleanup
clean:
	rm -rf __pycache__/ .pytest_cache/ .mypy_cache/ coverage_html/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Run everything
all: lint typecheck test security
