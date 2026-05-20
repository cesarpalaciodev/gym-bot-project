# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue.

Email: **cesarpalaciodev@gmail.com**

Response time: within 48 hours. We take all security reports seriously.

## Security Measures

This project implements:

- **RBAC**: 3 role levels (super_admin, admin, viewer) with `@require_role` decorator
- **Rate limiting**: Per-user request throttling
- **Dashboard security**: HMAC-signed sessions, CSRF protection, CSP headers, HSTS, X-Frame-Options
- **Environment isolation**: `.env` excluded from git, all secrets via environment variables
- **CI security scanning**: Bandit + Safety on every push to main
- **No hardcoded credentials**: All tokens/keys loaded from environment
