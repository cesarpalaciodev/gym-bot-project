# GymBot - Gym Management System

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-352%20passing-green.svg)](./tests/)
[![Coverage](https://img.shields.io/badge/coverage-84%25-brightgreen.svg)](./coverage_html/)
[![Mypy](https://img.shields.io/badge/mypy-strict-brightgreen.svg)](./pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

Enterprise-grade Telegram Bot + Web Dashboard for professional gym management. Clean architecture with layered separation (handlers → services → repositories → providers).

**Dashboard**: [http://localhost:8080](http://localhost:8080)  
**API Docs**: [http://localhost:8080/docs](http://localhost:8080/docs)

---

## Architecture

### Layered Architecture (Clean)

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Telegram   │  │   Dashboard  │  │     API      │      │
│  │   Handlers   │  │   (FastAPI)  │  │   (REST)     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │
          └─────────────────┴─────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────┐
│                    BUSINESS LAYER                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Services                           │  │
│  │  (MemberService, PaymentService, ExportService, ...)  │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────┐
│                     DATA LAYER                             │
│  ┌──────────────────┐  ┌──────────────────────────────┐   │
│  │  Repositories    │  │         Providers            │   │
│  │  (MongoDB)       │  │  (Telegram, Database APIs)   │   │
│  └──────────────────┘  └──────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### Key Features

- **Layered Architecture**: Clear separation of concerns
- **Dependency Injection**: Services use repositories, repositories use providers
- **Professional Logging**: Structured JSON logs, colored console output
- **Centralized Error Handling**: AppError hierarchy with error codes
- **External API Abstraction**: Providers with retry logic and normalization
- **Type Safety**: Full mypy strict mode coverage
- **Testing**: 352 tests with 84% coverage

---

## Quick Start

### Using Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/cesarpalaciodev/gym-bot-project.git
cd gym-bot-project

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Start with Docker
chmod +x scripts/docker.sh
./scripts/docker.sh up

# View logs
./scripts/docker.sh logs
```

### Manual Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env

# Run
./scripts/start.sh
```

---

## Project Structure

```
gym_bot_project/
├── bot.py                      # Entry point
├── config.py                   # Configuration
├── requirements.txt            # Dependencies
├── Dockerfile                  # Container image
├── docker-compose.yml          # Orchestration
├── .env.example               # Environment template
├── .prettierrc                # Code formatting
├── pyproject.toml             # Tool configuration
│
├── core/                      # Core utilities
│   ├── logging.py            # Professional logging
│   ├── errors.py             # AppError hierarchy
│   └── error_handler.py      # Centralized error handling
│
├── handlers/                  # Telegram handlers
│   ├── members.py
│   ├── payments.py
│   └── ...
│
├── services/                  # Business logic
│   ├── member_service.py
│   ├── payment_service.py
│   ├── export_service.py
│   └── ...
│
├── repositories/              # Data access layer
│   ├── member_repository.py
│   ├── payment_repository.py
│   └── ...
│
├── providers/                 # External API abstraction
│   ├── telegram_provider.py
│   ├── database_provider.py
│   └── ...
│
├── models/                    # Data models
│   ├── member.py
│   ├── payment.py
│   └── admin.py
│
├── dashboard/                 # Web Dashboard
│   ├── server.py             # FastAPI app
│   └── templates/            # Jinja2 templates
│
├── scripts/                   # Utility scripts
│   ├── start.sh
│   ├── test.sh
│   ├── lint.sh
│   └── docker.sh
│
├── tests/                     # Test suite
├── docs/                      # Documentation
│   └── architecture/         # ADRs, C4 diagrams
│
└── migrations/                # DB migrations
```

---

## Development

### Available Scripts

```bash
# Start the application
./scripts/start.sh

# Run tests with coverage
./scripts/test.sh

# Run linting and type checking
./scripts/lint.sh

# Docker management
./scripts/docker.sh up      # Start containers
./scripts/docker.sh down    # Stop containers
./scripts/docker.sh build   # Rebuild images
./scripts/docker.sh logs    # View logs

# Database migrations
./scripts/migrate.sh status     # Check migration status
./scripts/migrate.sh upgrade    # Apply pending migrations
./scripts/migrate.sh downgrade  # Rollback migrations
```

### Code Quality

```bash
# Linting
make lint          # ruff check
make format        # ruff format

# Type checking
make typecheck     # mypy strict

# Testing
make test          # pytest with coverage
make security      # bandit + safety

# All checks
make all           # lint + typecheck + test + security
```

---

## Configuration (.env)

```env
# Required
TOKEN=your_bot_token_from_botfather
ADMIN_ID=your_telegram_user_id
MONGO_URI=mongodb://admin:password@localhost:27017/gym
DASHBOARD_SECRET=random_secret_key

# Optional
DASHBOARD_PORT=8080
ENVIRONMENT=development
REDIS_URL=redis://localhost:6379/0
SENTRY_DSN=
```

See `.env.example` for complete configuration options.

---

## Architecture Highlights

### Error Handling

All errors are standardized using `AppError` hierarchy:

```python
from core.errors import ValidationError, NotFoundError

raise ValidationError("Invalid email format")
raise NotFoundError("Member", member_id=123)
```

### Logging

Professional logging with structured output:

```python
from core import get_logger

logger = get_logger(__name__)
logger.info("Operation completed", extra={"user_id": 123})
```

### External APIs

Providers abstract external services with retry logic:

```python
from providers import TelegramProvider, DatabaseProvider

tg = TelegramProvider()
response = await tg.send_message(chat_id, "Hello")
if response.is_success:
    data = response.data
```

---

## Testing

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_members.py -v

# Run with coverage report
pytest --cov=. --cov-report=html

# Integration tests (requires MongoDB)
pytest -m integration
```

**Stats**:
- 352 passing tests
- 84% code coverage
- Unit + integration tests

---

## Deployment

### Docker Production

```bash
# Build production image
docker build -t gym-bot:latest .

# Run with docker-compose
docker-compose -f docker-compose.yml up -d
```

### Environment Variables for Production

```env
ENVIRONMENT=production
LOG_LEVEL=INFO
JSON_LOGS=true
SENTRY_DSN=https://...
```

---

## License

MIT © Cesar Palacio