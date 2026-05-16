# GymBot - Gym Management System

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-352%20passing-green.svg)](./tests/)
[![Coverage](https://img.shields.io/badge/coverage-84%25-brightgreen.svg)](./coverage_html/)
[![Mypy](https://img.shields.io/badge/mypy-strict-brightgreen.svg)](./pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

Enterprise-grade Telegram Bot + Web Dashboard for professional gym management. Membership control, payments, expirations, and reports with clean architecture.

**Dashboard**: [http://localhost:8080](http://localhost:8080)  
**API Docs**: [http://localhost:8080/docs](http://localhost:8080/docs)

---

## Key Features

### Telegram Bot
- Member management (individual & bulk CRUD)
- Payment registration with grace/late logic
- 4 configurable membership plans
- Multi-admin system with roles (super_admin, admin, viewer)
- Automatic daily notifications (5 AM)
- Distributed rate limiting with Redis
- Export to Excel, CSV, TXT

### Web Dashboard (FastAPI)
- Secure server-side session authentication
- CSRF protection on all operations
- Real-time statistics visualization
- Documented REST API (OpenAPI)
- Responsive Jinja2 design

### Enterprise Security
- ✅ RBAC (Role-Based Access Control)
- ✅ HMAC-SHA256 signed sessions
- ✅ Security headers (HSTS, CSP, X-Frame-Options)
- ✅ Distributed rate limiting
- ✅ Audit logging for critical operations
- ✅ Mypy strict mode
- ✅ Bandit + Safety scanning

---

## Architecture

### High-Level Diagram

```mermaid
graph TB
    User[Telegram User] -->|Commands| Bot[Telegram Bot<br/>python-telegram-bot]
    Admin[Web Admin] -->|HTTPS| Dashboard[FastAPI Dashboard]
    
    Bot -->|Async| Services[Service Layer<br/>Business Logic]
    Dashboard -->|Async| Services
    
    Services -->|Motor| MongoDB[(MongoDB<br/>Sessions, Members, Payments)]
    Services -.->|Optional| Redis[(Redis<br/>Rate Limiting)]
    
    Bot -->|WebSocket| TelegramAPI[Telegram API]
```

### Technology Stack

| Layer | Technology |
|------|-----------|
| **Bot** | python-telegram-bot v21+ (async) |
| **Dashboard** | FastAPI + Jinja2 + Uvicorn |
| **Database** | MongoDB 7.0 with Motor (async) |
| **Cache/Rate Limit** | Redis (optional, memory fallback) |
| **Testing** | pytest + pytest-asyncio + coverage |
| **Type Checking** | mypy strict mode |
| **Linting** | ruff |
| **CI/CD** | GitHub Actions |
| **Deploy** | Docker + Docker Compose |

---

## Quick Start

### With Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/cesarpalaciodev/gym-bot-project.git
cd gym-bot-project

# Configure environment variables
cp .env.example .env
# Edit .env with your credentials

# Start services
docker-compose up -d

# View logs
docker-compose logs -f bot
```

### Manual Installation

```bash
# Requirements: Python 3.11+, MongoDB

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env

# Start
python bot.py
```

---

## Configuration (.env)

```env
# Telegram
TOKEN=your_bot_token_from_botfather
ADMIN_ID=your_telegram_user_id
GROUP_ID=-1001234567890  # Optional: notification group

# MongoDB
MONGO_URI=mongodb://admin:password@localhost:27017/gym
MONGO_ROOT_PASSWORD=secure_password_here

# Dashboard
DASHBOARD_SECRET=random_secret_key_min_32_chars
DASHBOARD_PORT=8080
ENVIRONMENT=development  # Change to 'production' in prod

# Optional
REDIS_URL=redis://localhost:6379/0
SENTRY_DSN=https://...  # Error tracking
```

---

## Bot Commands

| Command | Description | Access |
|---------|-------------|--------|
| `/start` | Start bot and show menu | Everyone |
| `/help` | List commands | Everyone |
| `/backup` | Export data to Excel | Admin+ |
| `/cancel` | Cancel current operation | Everyone |
| `/getgroupid` | Get group ID | Admin+ |

### Interactive Flows

1. **Add Member**: Name Phone YYYY-MM-DD
2. **Register Payment**: Select member → Plan → Confirm
3. **Search**: Exact or partial name
4. **Reports**: Debtors, full Excel

---

## Web Dashboard

### Main Endpoints

| Route | Description | Auth |
|------|-------------|------|
| `/login` | Login with Telegram Chat ID | Public |
| `/` | Main dashboard with statistics | Admin |
| `/dashboard/members` | Active members list | Admin |
| `/dashboard/payments` | Payment history | Admin |
| `/api/stats` | API: statistics JSON | Admin |
| `/api/members` | API: members JSON | Admin |
| `/api/payments` | API: paginated payments | Admin |
| `/docs` | OpenAPI documentation | Public |

### Screenshots

[Dashboard]: Shows active members, grace period, overdue, and monthly income statistics.
[Members]: Table with name, phone, status, expiration date, and overdue days.

---

## Membership Plans

| Plan | Price | Duration | Savings |
|------|--------|----------|--------|
| Monthly | $500 | 1 month | - |
| Quarterly | $1,350 | 3 months | 10% |
| Semi-annual | $2,500 | 6 months | 17% |
| Annual | $4,500 | 12 months | 25% |

---

## Roles & Permissions

| Role | Permissions |
|-----|----------|
| **super_admin** | Everything + admin management |
| **admin** | Member/payment CRUD, reports, export |
| **viewer** | Read-only (reports, statistics) |

---

## Testing

```bash
# Run all tests
make test

# Specific tests
pytest tests/test_members.py -v
pytest tests/test_payments.py::TestProcesarPago -v

# With coverage
pytest --cov=. --cov-report=html

# Integration tests (requires Docker)
pytest -m integration
```

**Stats**:
- 352 passing tests
- 84% code coverage
- Unit + integration tests

---

## Development

### Make Commands

```bash
make lint          # ruff linter
make format        # ruff formatter
make typecheck     # mypy strict
make test          # pytest + coverage
make security      # bandit + safety
make all           # All above
make docker-build  # Build Docker
make docker-up     # Docker compose up
```

### Project Structure

```
gym_bot_project/
├── bot.py                  # Entry point
├── config.py               # Configuration
├── requirements.txt        # Dependencies
├── docker-compose.yml      # Orchestration
│
├── handlers/               # Telegram handlers
│   ├── members.py
│   ├── payments.py
│   └── ...
│
├── services/               # Business logic
│   ├── member_service.py
│   ├── payment_service.py
│   └── report_service.py
│
├── models/                 # Data models
│   ├── member.py
│   └── payment.py
│
├── dashboard/              # Web Dashboard
│   ├── server.py          # FastAPI app
│   ├── auth.py            # Authentication
│   └── templates/         # Jinja2
│
├── utils/                  # Utilities
│   ├── auth.py            # RBAC
│   ├── rate_limit.py      # Rate limiting
│   └── ...
│
├── tests/                  # Tests
├── docs/                   # Documentation
│   └── architecture/      # C4 diagrams, ADRs
│
└── .github/workflows/      # CI/CD
```

---

## Architectural Documentation

- [C4 Diagrams](./docs/architecture/diagrams/c4-diagrams.md) - Context, Containers, Components
- [Architecture Decision Records (ADRs)](./docs/architecture/ADRs.md) - Why we made each decision
- [Contributing Guide](./CONTRIBUTING.md) - How to contribute
- [Changelog](./CHANGELOG.md) - Change history

---

## CI/CD

| Workflow | Trigger | Actions |
|----------|---------|----------|
| **test.yml** | push, PR | lint → typecheck → test (3.11, 3.12) |
| **security.yml** | push, PR, weekly | bandit → safety |
| **docker.yml** | tags v* | Build, scan with Trivy, push to Docker Hub |

---

## Security

- **Authentication**: Server-side sessions with HMAC
- **Authorization**: RBAC with 3 levels
- **CSRF**: Protection on all mutations
- **Rate Limiting**: 10 req/5s per user
- **Headers**: HSTS, CSP, X-Frame-Options, etc.
- **Secrets**: Never in code, always in .env
- **Audit**: Logging of all critical operations

---

## Roadmap

### v2.1.0 (Next)
- [ ] Integration tests with TestContainers
- [ ] MongoDB transactions
- [ ] Prometheus metrics
- [ ] API versioning

### v3.0.0 (Future)
- [ ] Mobile app
- [ ] Multi-gym support
- [ ] Payment gateway integration
- [ ] ML for churn prediction

---

## License

MIT © Cesar Palacio

---

## Support

- Issues: [GitHub Issues](https://github.com/cesarpalaciodev/gym-bot-project/issues)
- Email: gymbot@example.com
- Discord: [Support Server](https://discord.gg/example)

---

**⭐ Star this repo if it's useful!**
