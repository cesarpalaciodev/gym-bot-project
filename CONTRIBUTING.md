# Contributing Guide

Thank you for your interest in contributing to GymBot!

## How to Contribute

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/your-username/gym-bot.git
cd gym-bot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install
```

### 2. Environment Variables Configuration

Copy `.env.example` to `.env` and configure:

```bash
TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_user_id
MONGO_URI=mongodb://localhost:27017/gym
DASHBOARD_SECRET=random_secret_key
```

For local development with Docker:

```bash
docker-compose up -d mongo
```

### 3. Workflow

#### Create a Branch

```bash
git checkout -b feature/descriptive-name
# or
git checkout -b fix/bug-description
```

#### Make Changes

- Write clean, typed code
- Add tests for new features
- Ensure all tests pass

#### Verify Changes

```bash
# Linting and formatting
make lint
make format

# Type checking
make typecheck

# Tests
make test

# All together
make all
```

#### Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add payment reminder notifications
fix: correct date calculation for leap years
docs: update API documentation
refactor: extract validation logic to service
```

#### Pull Request

1. Update your branch with main: `git rebase main`
2. Push to your fork: `git push origin feature/name`
3. Create PR on GitHub with clear description
4. Ensure CI passes (tests, lint, security)

## Project Structure

```
gym_bot_project/
├── bot.py                 # Entry point
├── config.py              # Configuration
├── handlers/              # Telegram command handlers
│   ├── members.py
│   ├── payments.py
│   └── ...
├── services/              # Business logic
│   ├── member_service.py
│   ├── payment_service.py
│   └── report_service.py
├── models/                # Data models
├── utils/                 # Utilities
├── dashboard/             # FastAPI web dashboard
│   ├── server.py
│   ├── auth.py
│   └── templates/
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## Code Standards

### Python

- **Type hints**: Mandatory in all new code
- **Docstrings**: Google style for public functions
- **Line length**: 120 characters maximum
- **Imports**: stdlib → third-party → local

### Example

```python
from __future__ import annotations

from datetime import date
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from services import get_member_service


async def add_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a new gym member.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        None
    """
    if not update.message:
        return
        
    svc = await get_member_service()
    result = await svc.add_member(name, phone, date)
    await update.message.reply_text(result)
```

### Testing

- **Framework**: pytest
- **Minimum coverage**: 80% for new code
- **Mocks**: Use `unittest.mock` and `AsyncMock`
- **Fixtures**: Define in `conftest.py`

### Security

- Never commit credentials
- Use `os.getenv()` for secrets
- Validate user inputs
- Sanitize data before displaying in HTML

## Reporting Issues

### Bugs

Include:
- Steps to reproduce
- Expected vs actual behavior
- Error logs
- Environment (OS, Python version)

### Feature Requests

Include:
- Use case
- Implementation proposal
- Alternatives considered

## Roadmap

See [ROADMAP.md](./ROADMAP.md) for planned improvements.

## Questions?

- Discord: [Server link]
- Email: gymbot@example.com
- Issues: GitHub Issues

## Code of Conduct

- Be respectful
- Accept constructive criticism
- Focus on what's best for the community
