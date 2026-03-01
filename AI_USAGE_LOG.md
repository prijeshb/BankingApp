# AI Usage Log — Banking REST Service

## Tools Used
- **Claude Code** (claude-sonnet-4-6) — primary development tool for all phases

---

## Session 1 — Phase 1: Plan

### Prompt Used
> Kickoff prompt from `PROMPTS.md` with the full project spec pasted into `[PASTE SPEC HERE]`.

**Role context given:** Senior Staff Engineer at a financial institution
**Constraints enforced:** No code, plan only. Domain-driven structure. Decimal for money. Auth + idempotency + audit from the start.

### What AI produced
- Technology stack selection with rationale (FastAPI, SQLAlchemy 2.0 async, Pydantic v2, aiosqlite, Alembic, structlog)
- Full domain-driven folder structure (8 domains: auth, users, accounts, transactions, transfers, cards, statements, audit)
- 7 data models with field types — all monetary fields explicitly called out as `Decimal(18,4)` / never `float`
- Complete API endpoint table (method, path, auth requirement, request/response shape)
- Key design decisions table (UUID PKs, idempotency, soft deletes, append-only transactions, JWT + refresh tokens, audit log)
- Pre-approval banking checklist

### Manual review before approving
Checked the plan against the banking anti-pattern checklist from `PROMPTS.md`:
- ✅ No `float` anywhere — all `Decimal(18,4)`
- ✅ `idempotency_key` unique-constrained on Transfer table
- ✅ Soft deletes on Users, Accounts, Cards
- ✅ Every financial endpoint behind JWT + ownership check
- ✅ Append-only AuditLog table in schema
- ✅ Transactions append-only (no `updated_at`)
- ✅ Transfer wrapped in single DB transaction

**Decision:** Plan approved as-is. No corrections needed.

---

## Session 2 — Phase 2: Scaffold

### Prompt Used
> Scaffold prompt from `PROMPTS.md`.

**Must-include items verified:** JWT wired from the start, Pydantic v2 strict schemas, Decimal everywhere, global error handler, correlation ID middleware, env-var config.

### What AI produced (43 files)

#### Infrastructure
| File | Notes |
|---|---|
| `requirements.txt` | 12 pinned deps |
| `requirements-dev.txt` | pytest + httpx + faker |
| `.env.example` | All vars documented, no secrets |
| `app/config.py` | pydantic-settings with validator rejecting default JWT key |
| `app/database.py` | Async engine, WAL + foreign_keys pragmas on connect |

#### Common utilities
| File | Notes |
|---|---|
| `app/common/base_model.py` | UUID PK + timestamp mixins shared by all models |
| `app/common/logging.py` | structlog JSON output with context vars |
| `app/common/middleware.py` | Correlation ID injected on every request, echoed in response header |
| `app/common/exceptions.py` | Typed domain exceptions + structured `{"error": {"code", "message"}}` responses |
| `app/common/health.py` | `/health`, `/health/ready`, `/health/live` |

#### Domain modules (models → schemas → service → router)
- `auth` — register, login, refresh, logout; bcrypt passwords; server-side refresh token revocation
- `users` — profile CRUD with soft delete
- `accounts` — create/list/get/soft-delete; auto-generated account numbers
- `transactions` — append-only ledger; paginated list with date filters
- `transfers` — atomic debit+credit in single session; idempotency guard; ownership check
- `cards` — issue/list/get/block/soft-delete; only last 4 digits + SHA-256 hash stored
- `statements` — opening/closing balance, totals, transaction list for a date range
- `audit` — append-only log written on every state change

#### Deployment
| File | Notes |
|---|---|
| `Dockerfile` | Multi-stage build; non-root `appuser`; `HEALTHCHECK` directive |
| `docker-compose.yml` | Production config with named volume for DB |
| `docker-compose.override.yml` | Dev hot-reload via bind mount |
| `alembic.ini` + `alembic/env.py` | Async migration setup |
| `tests/conftest.py` | In-memory SQLite, async HTTPX client, auth + account fixtures |
| `pytest.ini` | `asyncio_mode = auto` |

### Manual interventions
- Added `python-dateutil` to `requirements.txt` after AI used `relativedelta` in cards service (missing from initial dep list)
- Expanded `.gitignore` to cover Python cache, `.env`, `data/`, and IDE files
- Kept `docs_url` always visible (AI had it hidden in non-DEBUG mode — changed for assessment submission)

### Key decisions made / confirmed
- **SQLite with WAL mode** — required by spec; pragmas set at engine connect time
- **Transfer atomicity** — both balance mutations and both transaction records created in the same SQLAlchemy session; committed together at request end via `get_db()`
- **Idempotency on transfers** — duplicate key returns `409 CONFLICT` rather than silently ignoring
- **Card number storage** — raw number never persisted; only masked last-4 and SHA-256 hash

---

## Challenges & How AI Helped

| Challenge | How AI helped |
|---|---|
| Async SQLAlchemy 2.0 WAL pragma setup | Correctly used `@event.listens_for(engine.sync_engine, "connect")` for async engines |
| Alembic async migration env.py | Generated the `run_async_migrations()` pattern with `async_engine_from_config` |
| Append-only audit log design | AI flagged the need for this in Phase 1 before any code was written |
| Multi-stage Dockerfile | Generated builder + runtime stages with non-root user unprompted |

---

## Session 3 — Phase 3: Tests

### Prompt Used
> Write Tests prompt from `PROMPTS.md`, applied to the full scaffold.
> Framework: pytest + pytest-asyncio + httpx

### What AI produced

#### Test infrastructure
- Rewrote `tests/conftest.py` — `clean_tables` autouse fixture wipes all rows before each test; `client` fixture gives each request its own committed session matching production behaviour exactly

#### Integration tests (7 files, ~90 test cases)
| File | Coverage |
|---|---|
| `test_health.py` | All 3 endpoints, no-auth requirement |
| `test_auth.py` | Register (happy, duplicate email, weak password, invalid email), login (happy, wrong password, non-existent), refresh (happy, invalid token), logout (revokes token) |
| `test_accounts.py` | Create (CHECKING, SAVINGS, invalid type/currency), list (empty, own-only), get (found, not found, other user 403), delete (soft, other user 403) |
| `test_transactions.py` | List (empty, after transfer, pagination), get (found, not found), ownership 403 |
| `test_transfers.py` | Happy path, balance debit/credit consistency, transaction records created, insufficient funds, zero/negative amount, same account, duplicate idempotency key, cross-user ownership 403, non-existent account 404 |
| `test_cards.py` | Issue (DEBIT, VIRTUAL), list, get, block/unblock, invalid status, soft delete, ownership 403 |
| `test_statements.py` | Empty period, with transactions, missing date params 422, ownership 403 |

#### Unit tests (3 files)
| File | Coverage |
|---|---|
| `test_auth_service.py` | bcrypt hash uniqueness, verify correct/wrong, JWT structure, expiry, wrong key rejection |
| `test_transfer_validation.py` | Same-account, zero/negative amount, precision, optional description |
| `test_account_schemas.py` | Currency case/length, invalid account type, default currency |

### Coverage gaps (honest)
| Gap | Priority |
|---|---|
| Token expiry (time-travel test) | HIGH — requires mocking `datetime.now` |
| Concurrent transfer race condition | HIGH — SQLite serialises writes; worth testing against PostgreSQL |
| Audit log rows created on state changes | MEDIUM — tested indirectly |
| Statement opening balance carry-forward | MEDIUM — prior-period balance not explicitly tested |
| Card 3-year expiry value | LOW — presence checked, value not asserted |

### Manual interventions
- Identified that `get_db` auto-commits made the original rollback-based fixture ineffective; redesigned to use `clean_tables` autouse
- Added DB-level balance seeding in transfer/transaction tests (no admin credit endpoint exists)

---

## Session 4 — Test Bug Fixes (90/90 green)

### Bugs fixed after first test run

| Bug | Root cause | Fix |
|---|---|---|
| `ImportError: email-validator is not installed` | `EmailStr` in Pydantic v2 requires the `email-validator` package | Added `email-validator==2.2.0` to `requirements.txt` |
| `passlib` + `bcrypt>=4.0` incompatibility | passlib 1.7.4 hashes a 73-byte test password; bcrypt 4.x rejects passwords >72 bytes | Removed `passlib`; replaced with direct `bcrypt==4.2.1` calls in `auth/service.py` |
| `TypeError: can't compare offset-naive and offset-aware datetimes` | `utc_now()` returned timezone-aware datetime; SQLite stores without timezone | Changed `utc_now()` to return naive UTC (`datetime.now(timezone.utc).replace(tzinfo=None)`); audited all service files for naive consistency |
| `test_refresh_returns_new_access_token` — tokens identical | Two JWTs created within the same second are identical (same `sub` + `exp`) | Changed assertion to verify 3-part JWT structure rather than token inequality |
| `sqlite3.OperationalError: no such table` | In-memory SQLite with `StaticPool` + aiosqlite doesn't share connections reliably across async tasks | Switched `conftest.py` to file-based SQLite (`test_banking.db`); added pre-session cleanup and post-session delete |
| 307 redirect on `POST /api/v1/transfers` | Router defined `POST "/"` giving URL `/api/v1/transfers/`; tests posted to `/api/v1/transfers`; httpx doesn't auto-follow POST 307s | Changed route path from `"/"` to `""` |
| `TypeError: Object of type ValueError is not JSON serializable` | Pydantic v2 embeds the raw `ValueError` object in `ctx['error']` inside `exc.errors()`; our handler passed this directly to `JSONResponse` | `validation_exception_handler` now extracts only `{field, message}` per error — always JSON-safe |
| `test_statement_with_transactions` — transaction_count=0 | `date.today()` returns local date; `utc_now()` stores UTC; machine was UTC-6 so UTC date was the next calendar day | Test changed to use `datetime.now(timezone.utc).date()` for the query date |

### Final result
**90/90 tests passing** (87 integration, 3 unit across 10 test files)

---

## Areas Where Manual Intervention Was Necessary

- Dependency audit (catching missing `python-dateutil`)
- Reviewing each model to confirm no `float` slipped through
- Confirming `get_db()` session lifecycle is sufficient for transfer atomicity in SQLite
- Deciding to keep OpenAPI docs always enabled for assessment visibility
- Diagnosing the UTC-vs-local date bug in the statement test (required checking machine timezone at runtime)
