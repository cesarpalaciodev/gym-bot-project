# Architecture Decision Records (ADRs)

## ADR-001: Using MongoDB as Primary Database

**Status**: Accepted

**Context**: We need a database that supports async CRUD operations to handle multiple simultaneous Telegram bot users.

**Decision**: Use MongoDB with Motor driver (async).

**Rationale**:
- Flexible schema for member and payment data
- Native async driver (Motor) compatible with python-telegram-bot
- TTL index support for sessions
- Replica set for ACID transactions when needed

**Consequences**:
- ✅ Horizontal scalability
- ✅ Agile development without schema migrations
- ⚠️ Less relational consistency than PostgreSQL

---

## ADR-002: Service Layer Architecture

**Status**: Accepted

**Context**: Telegram handlers had embedded business logic, making testing and reuse difficult.

**Decision**: Extract business logic to services (MemberService, PaymentService, ReportService).

**Rationale**:
- Separation of concerns
- Improved testability (service mocking)
- Reuse between bot and dashboard
- Dependency injection for testing

**Consequences**:
- ✅ Cleaner, more maintainable code
- ✅ Easier unit tests
- ⚠️ Additional abstraction layer

---

## ADR-003: FastAPI for Web Dashboard

**Status**: Accepted

**Context**: We needed a web interface to view metrics without using Telegram commands.

**Decision**: Use FastAPI instead of Flask or Django.

**Rationale**:
- Native async (compatible with Motor)
- Automatic OpenAPI/docs
- Superior performance
- Integrated type hints

**Consequences**:
- ✅ Automatic API documentation
- ✅ Type-safe development
- ⚠️ Learning curve for Jinja2 templates

---

## ADR-004: MongoDB Sessions vs JWT

**Status**: Accepted

**Context**: Decide authentication mechanism for the dashboard.

**Decision**: Server-side sessions in MongoDB with signed cookies (HMAC).

**Rationale**:
- Immediate session revocation
- No data exposure in token
- Automatic TTL in MongoDB
- More secure than JWT for this use case

**Consequences**:
- ✅ Instant revocation
- ✅ Controlled expiration
- ⚠️ Requires DB query per request
- ⚠️ Needs sticky sessions if scaling horizontally

---

## ADR-005: python-telegram-bot v21+

**Status**: Accepted

**Context**: Choose framework for the Telegram bot.

**Decision**: python-telegram-bot version 21+.

**Rationale**:
- Native async/await support
- Integrated job queue
- Active maintenance
- Extensive documentation

**Consequences**:
- ✅ Modern, clean API
- ✅ Webhook support
- ⚠️ Breaking changes between versions

---

## ADR-006: Rate Limiting with Redis Fallback

**Status**: Accepted

**Context**: Prevent bot and API abuse.

**Decision**: Redis for distributed rate limiting with memory fallback.

**Rationale**:
- Works without Redis (graceful degradation)
- Sliding window with sorted sets
- Limit: 10 requests per 5 seconds per user

**Consequences**:
- ✅ Spam protection
- ✅ Works standalone or distributed
- ⚠️ Potential memory leak in fallback (not critical)

---

## ADR-007: Mypy Strict Mode

**Status**: Accepted

**Context**: Improve code quality and catch errors early.

**Decision**: Enable mypy in strict mode.

**Rationale**:
- Complete type safety
- Detection of potential Nones
- Better IDE experience

**Consequences**:
- ✅ Fewer production bugs
- ✅ Implicit documentation with types
- ⚠️ Initial development overhead

---

## ADR-008: Docker Multi-Stage Build

**Status**: Accepted

**Context**: Optimize Docker image for production.

**Decision**: Multi-stage build with slim final image.

**Rationale**:
- Smaller final image
- No dev dependencies in production
- Efficient caching

**Consequences**:
- ✅ ~200MB image vs ~1GB
- ✅ Faster builds
- ⚠️ Additional complexity in Dockerfile

---

## ADR-009: CI/CD with GitHub Actions

**Status**: Accepted

**Context**: Automate testing and deployment.

**Decision**: GitHub Actions with separate workflows.

**Workflows**:
1. **test.yml**: Lint, type check, tests on every push/PR
2. **security.yml**: Bandit + Safety weekly and on main
3. **docker.yml**: Build and push image on tags

**Consequences**:
- ✅ Quality guaranteed before merge
- ✅ Early vulnerability detection
- ✅ Automated deployment

---

## ADR-010: Comprehensive Testing Strategy

**Status**: Accepted

**Context**: Ensure code quality and prevent regressions.

**Decision**: Multi-layer testing approach.

**Strategy**:
- **Unit tests**: Models, utils, services (pytest)
- **Handler tests**: All 9 handler files with mocked Telegram API
- **Integration tests**: Real MongoDB via Testcontainers
- **E2E tests**: Dashboard flows with Selenium/Playwright

**Consequences**:
- ✅ High confidence in changes
- ✅ Living documentation
- ⚠️ Test maintenance overhead
- ⚠️ Slower CI with integration tests

---

## ADR-011: Security-First Development

**Status**: Accepted

**Context**: Handle sensitive gym member and payment data.

**Decision**: Security integrated from the start, not as an afterthought.

**Measures**:
- RBAC with role hierarchy
- CSRF protection on all mutations
- Security headers (HSTS, CSP, etc.)
- Input validation and sanitization
- Audit logging for all operations
- Secrets never in code
- Regular dependency scanning

**Consequences**:
- ✅ Enterprise-grade security
- ✅ Compliance ready
- ⚠️ Additional development time
- ⚠️ More complex testing

---

## ADR-012: Documentation as Code

**Status**: Accepted

**Context**: Keep documentation updated and version controlled.

**Decision**: All documentation in Markdown, version controlled with code.

**Documentation**:
- README.md - Quick start and overview
- CONTRIBUTING.md - Developer guide
- CHANGELOG.md - Version history
- ADRs.md - Architecture decisions
- C4 diagrams - System architecture
- Inline code documentation (docstrings)

**Consequences**:
- ✅ Documentation always up to date
- ✅ Reviewed in PRs
- ✅ Searchable and linkable
- ⚠️ Requires discipline to maintain
