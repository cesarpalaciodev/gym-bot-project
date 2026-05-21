# AGENTS.md - Gym Management Telegram Bot

## Description

Telegram bot for gym member & payment management with MongoDB. Python async/await, python-telegram-bot v21+.

## Commands

```bash
# Install all deps (prod + dev)
pip install -r requirements.txt
pip install pytest pytest-cov mypy ruff pre-commit bandit safety

# Run
python bot.py

# Make targets (preferred)
make lint          # ruff linter
make format        # ruff formatter
make typecheck     # mypy strict
make test          # pytest + coverage
make security      # bandit + safety
make all           # lint + typecheck + test + security
make docker-build  # build Docker image
make docker-up     # docker-compose up
```

## Environment (.env)

```
TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_user_id
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/gym
GROUP_ID=-1001234567890
```

## Code Conventions

### Type hints (MANDATORY - enforced by mypy strict)
```python
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
```

### Imports
stdlib → third-party → local  (enforced by ruff I rule)

### Names
- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private helpers: `_prefix`

### Async/await
Always `async def` for handlers. Use `await` for all Telegram API calls.

### Error handling
- Narrow exceptions: prefer `TelegramError` over bare `Exception`
- Log errors, return user-friendly messages
- Last-resort `except Exception` is acceptable in handlers for state cleanup

### State management
- Prefer `context.user_data` over global dicts
- When using global dicts, add `_ts` timestamp and `STATE_TIMEOUT = 600`
- Always call `_clean_stale_states()` before setting new state
- Always call `_del_state()` when flow completes or errors

## Architecture

```
gym_bot_project/
├── bot.py                 # Entry point, app builder, job queue
├── config.py              # Env vars, plans, roles, constants
├── database/
│   └── __init__.py        # MongoDB pooling, indexes, collections
├── models/
│   ├── member.py          # Member dataclass (to_dict / from_dict)
│   ├── payment.py         # Payment dataclass
│   └── admin.py           # Admin dataclass
├── handlers/
│   ├── start.py           # /start, /help, /getgroupid
│   ├── members.py         # Member CRUD (add/search/delete/bulk)
│   ├── payments.py        # Payment registration + history
│   ├── reports.py         # Overdue report, Excel generation
│   ├── stats.py           # Active members, income, expirations
│   ├── notifications.py   # 5 AM daily job
│   ├── admins.py          # Multi-admin CRUD + role management
│   ├── export.py          # Excel (members/payments), TXT, CSV
│   └── button_handler.py  # Menu routing + rate limiting
├── utils/
│   ├── dates.py           # Due date math, grace/late logic
│   ├── auth.py            # @require_role decorator, es_admin_grupo
│   ├── audit.py           # CRUD audit log
│   └── cache.py           # LRU cache for plans & config
├── keyboards.py           # ReplyKeyboardMarkup definitions
├── tests/                 # 87+ tests (pytest + coverage)
│
├── pyproject.toml         # Build system, ruff, mypy, pytest config
├── Makefile               # Dev workflow
├── Dockerfile             # Multi-stage build
├── docker-compose.yml     # Bot + MongoDB
├── .pre-commit-config.yaml
└── render.yaml            # Render deploy
```

## Payment Logic

```
DUE = payment_date + 1 month (same day)

1-4 days overdue:
  → GRACE → Original due date preserved

5+ days overdue:
  → LATE → New due date = today + 1 month
```

Edge cases handled: months with <31 days, year boundaries, leap years.

## Membership Plans

| Plan | Price | Months |
|------|-------|--------|
| Mensual | $500 | 1 |
| Trimestral | $1,350 | 3 |
| Semestral | $2,500 | 6 |
| Anual | $4,500 | 12 |

## Admin Roles

| Role | Level | Permissions |
|------|-------|-------------|
| super_admin | 3 | All + admin management |
| admin | 2 | Members, payments, reports, stats, export |
| viewer | 1 | Reports, stats (read-only) |

## Dependencies

- python-telegram-bot[job-queue]>=21.0
- python-dotenv
- python-dateutil
- openpyxl
- pymongo>=4.6.0

## Dev Dependencies (optional)

- pytest, pytest-cov (tests)
- mypy (type checking)
- ruff (linting + formatting)
- pre-commit (hooks)
- bandit, safety (security)

## Git Workflow

- Branches: `feature/description` or `fix/description`
- Commits: `feat: add feature` or `fix: resolve bug`
- Don't commit: `.env`, `logs/`, `reports/`, `__pycache__/`, `coverage_html/`, `.pytest_cache/`, `.mypy_cache/`

## Testing

```bash
make test              # all tests + coverage
pytest tests/test_file.py::TestClass::test_method  # single test
pytest -m integration  # integration tests only (needs MongoDB)
```

## CI (GitHub Actions)

- `test.yml`: ruff → mypy → pytest (every push/PR, Python 3.11 + 3.12)
- `security.yml`: bandit + safety (weekly + main push)
- `docker.yml`: build & push to Docker Hub (on tag v*)
