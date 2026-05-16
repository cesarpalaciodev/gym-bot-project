# Gym Management Telegram Bot

A production-grade Telegram bot for managing gym members, payments, and expiration dates with MongoDB. Built with Python, async/await, and the python-telegram-bot framework.

[![Test](https://github.com/cesarpalaciodev/gym-bot-project/actions/workflows/test.yml/badge.svg)](https://github.com/cesarpalaciodev/gym-bot-project/actions/workflows/test.yml)
[![Security](https://github.com/cesarpalaciodev/gym-bot-project/actions/workflows/security.yml/badge.svg)](https://github.com/cesarpalaciodev/gym-bot-project/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/cesarpalaciodev/gym-bot-project/branch/main/graph/badge.svg)](https://codecov.io/gh/cesarpalaciodev/gym-bot-project)

---

## Features

- **Member management** — Add, search, delete (single & bulk)
- **Payment tracking** — Grace period (1-4 days) and late payment logic
- **Membership plans** — Monthly ($500), Quarterly ($1,350), Semi-annual ($2,500), Annual ($4,500)
- **Payment history** — Per-member full history
- **Overdue detection** — Automatic reports of late members
- **Statistics dashboard** — Active members, monthly income, upcoming expirations
- **Export** — Excel (members/payments), CSV, TXT summary
- **Multi-admin system** — 3 roles (super_admin, admin, viewer)
- **Daily notifications** — Automatic 5 AM summary to the group
- **Audit logging** — Every CRUD operation logged for accountability
- **Rate limiting** — 10 requests per 5 seconds per user
- **State expiration** — In-progress flows auto-expire after 10 minutes

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Show all commands |
| `/backup` | Create manual Excel backup (group only) |
| `/cancel` | Cancel any in-progress flow |
| `/getgroupid` | Get the current group ID |

### Menu navigation

All features accessible via reply keyboard buttons. Main menu:

```
👥 Miembers    💰 Payments
📊 Reports     📈 Statistics
💾 Export      ⚙️ Admin
⬅️ Back
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- MongoDB instance (local or Atlas)

### Setup

```bash
# Clone
git clone https://github.com/cesarpalaciodev/gym-bot-project.git
cd gym-bot-project

# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install
pip install -r requirements.txt

# Environment
cp .env.example .env
# Edit .env with your credentials
```

### Environment variables

```env
TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_user_id
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/gym
GROUP_ID=-1001234567890
```

### Run

```bash
python bot.py
```

---

## Payment Logic

```
Payment day: user-chosen date (e.g., 15th)
Due date: same day next month

1-4 days overdue:
  → GRACE PERIOD → Original due date preserved

5+ days overdue:
  → LATE → New due date = payment day + 1 month
```

### Edge cases handled

- Months with fewer days (Jan 31 → Feb 28)
- Year boundaries (Dec 10 → Jan 10)
- Leap years (Jan 31 → Feb 29)
- 31st day months (Mar 31 → Apr 30)

---

## Membership Plans

| Plan | Price | Duration |
|------|-------|----------|
| Monthly | $500 | 1 month |
| Quarterly | $1,350 | 3 months |
| Semi-annual | $2,500 | 6 months |
| Annual | $4,500 | 12 months |

---

## Admin Roles

| Role | Permissions |
|------|-------------|
| **super_admin** | Full access + manage other admins |
| **admin** | Members, payments, reports, stats, export |
| **viewer** | Read-only (reports, stats) |

---

## Project Structure

```
gym_bot_project/
├── bot.py                  # Entry point, application setup
├── config.py               # Environment & app configuration
│
├── database/
│   └── __init__.py         # MongoDB connection pooling & indexes
│
├── models/
│   ├── member.py           # Member dataclass
│   ├── payment.py          # Payment dataclass
│   └── admin.py            # Admin dataclass
│
├── handlers/
│   ├── start.py            # /start, /help, /getgroupid
│   ├── members.py          # Member CRUD
│   ├── payments.py         # Payment registration & history
│   ├── reports.py          # Overdue list, Excel reports
│   ├── stats.py            # Statistics dashboard
│   ├── notifications.py    # Daily 5 AM notifications
│   ├── admins.py           # Multi-admin management
│   ├── export.py           # Excel, CSV, TXT exports
│   └── button_handler.py   # Menu routing + rate limiting
│
├── utils/
│   ├── dates.py            # Date math (grace, late, due dates)
│   ├── auth.py             # Role-based authorization
│   ├── audit.py            # Action audit logging
│   └── cache.py            # LRU cache for plans & config
│
├── keyboards.py            # All reply keyboard definitions
├── tests/                  # Test suite (288 tests, 87% coverage)
│
├── requirements.txt
├── pyproject.toml           # Build config + tool settings
├── Makefile                # Dev workflow commands
├── Dockerfile              # Multi-stage production build
├── docker-compose.yml      # Bot + MongoDB services
├── .pre-commit-config.yaml # Pre-commit hooks
└── render.yaml             # Render deploy config
```

---

## Development

### Prerequisites

```bash
pip install -r requirements.txt
pip install pytest pytest-cov mypy ruff pre-commit bandit safety
```

### Makefile commands

| Command | Description |
|---------|-------------|
| `make lint` | Run ruff linter |
| `make format` | Auto-format with ruff |
| `make typecheck` | Run mypy strict |
| `make test` | Run pytest with coverage |
| `make security` | Bandit + safety scan |
| `make all` | lint + typecheck + test + security |
| `make docker-build` | Build Docker image |
| `make docker-up` | Start bot + MongoDB via compose |

### Pre-commit hooks

```bash
make precommit-install
```

Runs ruff (lint + format) and mypy on every commit.

---

## Docker

### Build & run

```bash
docker-compose up --build -d
```

Starts bot + MongoDB 7 with persistent volume.

### Multi-stage build

```dockerfile
FROM python:3.11-slim AS builder   # Install deps
FROM python:3.11-slim AS runner    # Runtime only
```

Final image is ~180MB (slim).

---

## CI/CD

Three GitHub Actions workflows:

| Workflow | Trigger | Actions |
|----------|---------|---------|
| **test.yml** | push + PR | ruff → mypy → pytest (3.11 & 3.12) |
| **security.yml** | weekly + main push | bandit → safety |
| **docker.yml** | tags v* | Build & push to Docker Hub |

---

## Testing

**288 tests** with **87% code coverage** across the entire project:

| Module | Coverage | Tests |
|--------|----------|-------|
| `handlers/members.py` | 96% | 31 |
| `handlers/payments.py` | 97% | 27 |
| `handlers/stats.py` | 100% | 22 |
| `handlers/button_handler.py` | 100% | 37 |
| `handlers/reports.py` | 100% | 16 |
| `handlers/export.py` | 100% | 17 |
| `handlers/admins.py` | 100% | 26 |
| `handlers/notifications.py` | 100% | 11 |
| `handlers/start.py` | 100% | 15 |
| `utils/dates.py` | 89% | 22 |
| `config.py` | 100% | 14 |
| `keyboards.py` | 100% | 10 |
| `models/` | 95%+ | 14 |
| `utils/cache.py` | 100% | 7 |

### Test categories

- **Unit tests** — Models, config, cache, keyboards, auth, dates
- **Handler tests** — All 9 handler files with mocked Telegram API
- **Integration** — Payment flow logic, end-to-end scenarios
- **Database** — Connection, error handling, collection access

### Running tests

```bash
make test              # All tests + coverage report
make test-integration  # Integration tests (needs MongoDB)
pytest tests/test_members.py -v  # Single file
```

---

## Deployment

### Render

1. Push to GitHub
2. Create Web Service on Render
3. Connect repository, set env vars
4. `render.yaml` auto-configures build & start

### Docker

```bash
docker build -t gym-bot:latest .
docker run -d --env-file .env gym-bot:latest
```

### Security notes

- `.env` is gitignored — never commit credentials
- Rate limiting prevents abuse (10 req / 5s)
- Admin-only commands require role validation
- Audit log tracks all operations
- MongoDB connection uses TLS by default
- Unique index on `admins.telegram_id` prevents duplicates

---

## License

MIT — Cesar Palacio
