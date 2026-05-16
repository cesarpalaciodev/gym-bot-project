# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-05-16

### Added
- Complete web dashboard with FastAPI
- Server-side session authentication with MongoDB
- CSRF protection on all POST routes
- Security headers (HSTS, X-Frame-Options, etc.)
- Rate limiting with Redis fallback
- Service layer with dependency injection
- Multi-admin support with roles (super_admin, admin, viewer)
- Export to Excel, CSV and TXT
- Debtor reports and statistics
- Automatic 5 AM notifications
- Audit logging for critical operations
- Retry logic with tenacity for MongoDB operations
- Pre-commit hooks (ruff, mypy, bandit)
- GitHub Actions CI/CD (test, security, docker)
- Docker multi-stage build
- docker-compose with MongoDB

### Changed
- Complete refactoring to service architecture
- Mypy strict mode enabled
- All handlers use services via factory
- Improved error handling with logging

### Security
- Dashboard API endpoints now require authentication
- SECRET_KEY moved to environment variable
- MongoDB with authentication in docker-compose
- Session cookie with secure flag in production
- Fix: Auth bypass when effective_user is None
- Fix: backup_command now uses RBAC

### Fixed
- Critical bug: dashboard/__init__.py was empty
- Date calculation for months with < 31 days
- Memory leak in rate limiter fallback

## [1.1.0] - 2026-03-15

### Added
- Support for multiple plans (Monthly, Quarterly, Semi-annual, Annual)
- 4-day grace period for payments
- /backup command to export data
- Environment variables for configuration

### Changed
- Improved due date calculation
- More intuitive button UI

### Fixed
- Timezone correction in notifications
- Fix: Member duplication when searching

## [1.0.0] - 2026-01-20

### Added
- Basic Telegram bot
- Member CRUD
- Payment registration
- Automatic due date calculation
- Daily notifications
- MongoDB as database
- Basic Docker

### Security
- Group admin validation
- Basic rate limiting

## Roadmap

### [2.1.0] - Next Version
- [ ] Integration tests with TestContainers
- [ ] MongoDB transactions for critical operations
- [ ] API versioning (/v1/)
- [ ] Improved webhooks with retry
- [ ] Prometheus metrics

### [3.0.0] - Future
- [ ] Companion mobile app
- [ ] Multi-gym support
- [ ] Payment gateway integration
- [ ] ML for churn prediction
- [ ] Horizontal scaling with Kubernetes

## Version Notes

### 2.0.0 - "Enterprise" Version
This version represents a complete rewrite focused on:
- Enterprise-grade security
- Clean and maintainable architecture
- Preparation for scaling
- Compliance with Python best practices

**Breaking Changes:**
- New `.env` format (see `.env.example`)
- New `sessions` collection in MongoDB
- Dashboard requires authentication

**Migration:**
```bash
# Backup before updating
python -m utils.migrate backup

# Update docker-compose
docker-compose down
docker-compose up -d

# Apply migrations
python -m utils.migrate
```
