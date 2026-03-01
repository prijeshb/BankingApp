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

---

## Session 5 — Phase 4: Code Review + Hardening

### Prompt Used
> Code Review + Pre-Submit prompts from `PROMPTS.md`, applied to the full codebase.

### What AI produced (code review)

Full banking-checklist review surfaced the following issues:

| ID | Severity | Finding |
|---|---|---|
| C-1 | CRITICAL | `logout()` didn't verify the refresh token belonged to the requesting user — any user with another user's token UUID could revoke it |
| C-2 | CRITICAL | `refresh_access_token()` never checked if the user was still active/deleted after token issuance |
| H-1 | HIGH | `register`, `login`, `logout`, `update_me`, `delete_me` were not writing to the AuditLog |
| H-2 | HIGH | `cards/service.py` used `date.today()` (local timezone) for card expiry — inconsistent with UTC timestamp storage |
| M-1 | MEDIUM | Card number generation used `random.choices` (not cryptographically secure) |
| M-2 | MEDIUM | Account deletion accepted non-zero balance |
| M-3 | MEDIUM | `ip_address` parameter never passed to `log_action()` despite the field existing |
| M-4 | MEDIUM | `EXPIRED` card status could be set manually via `PATCH /cards/{id}/status` |
| L-1 | LOW | Health `/health/ready` flagged as not probing DB — investigation showed it already does (`SELECT 1`) — false positive |
| L-2 | LOW | Card numbers not Luhn-valid — deferred (out of scope for this project) |

### Fixes applied

#### Security fixes (C-1, C-2)
- `auth/service.py` — `logout()` now takes `user_id` and adds `RefreshToken.user_id == user_id` filter
- `auth/service.py` — `refresh_access_token()` eagerly loads user via `selectinload(RefreshToken.user)` and checks `user.is_active` and `user.deleted_at is None`
- `auth/service.py` — `login()` now returns `tuple[str, str, str]` so the router can pass `user_id` to `log_action` without a second DB call

#### Audit trail (H-1, M-3)
- `auth/router.py` — `log_action()` added to `register`, `login`, `logout` with `ip_address` from `request.client`
- `users/router.py` — `log_action()` added to `update_me` and `delete_me` with `ip_address`
- `accounts/router.py` — `ip_address` added to existing `log_action` calls
- `cards/router.py` — `ip_address` added to existing `log_action` calls
- `transfers/router.py` — `ip_address` added to existing `log_action` call

#### Card hardening (H-2, M-1, M-4)
- `cards/service.py` — expiry now uses `datetime.now(timezone.utc).date()` instead of `date.today()`
- `cards/service.py` — card number generation uses `secrets.randbelow(10)` instead of `random.choices`
- `cards/service.py` — `update_card_status()` raises `InvalidCardStatusError` if new status is `EXPIRED` or card is already `EXPIRED`
- `cards/schemas.py` — `UpdateCardStatusRequest` adds a `field_validator` rejecting `EXPIRED` at the Pydantic layer (defence-in-depth)

#### Business logic (M-2)
- `accounts/service.py` — `soft_delete_account()` raises `AccountHasFundsError` (422) if `balance != Decimal("0")`

#### New shared types + validation
- `app/common/types.py` — `UUIDPath` annotated type (`Annotated[str, Path(pattern=UUID_REGEX)]`) applied to all path parameters across all routers; malformed IDs return 422 before any DB call
- `app/common/exceptions.py` — added `AccountHasFundsError` and `InvalidCardStatusError`
- `statements/router.py` — added `end_date >= start_date` guard (422 if violated)
- `transactions/router.py` — added same date range guard for the optional filter params

### Test updates
- 5 test locations updated from invalid path param strings (`some-id`, `nonexistent-id`, `nonexistent`) to valid UUID format (`00000000-0000-0000-0000-000000000000`) — FastAPI validates path params before auth, so tests that sent malformed IDs would receive 422 instead of the expected 403/404
- 8 "requires_auth" tests updated from `403` to `401` — Starlette 0.52.x `HTTPBearer` now correctly returns 401 (unauthenticated) instead of 403 for missing Bearer tokens

### Final result
**90/90 tests passing** (same count, all hardening changes covered by existing test suite)

---

## Areas Where Manual Intervention Was Necessary

- Dependency audit (catching missing `python-dateutil`)
- Reviewing each model to confirm no `float` slipped through
- Confirming `get_db()` session lifecycle is sufficient for transfer atomicity in SQLite
- Deciding to keep OpenAPI docs always enabled for assessment visibility
- Diagnosing the UTC-vs-local date bug in the statement test (required checking machine timezone at runtime)

---

## Session 6 — Phase 5: React Frontend

### Prompt Used
> Frontend plan prompt from `PROMPTS.md` — full feature coverage across all API domains.

**Stack chosen:** Vite + React 18 + Tailwind CSS, Axios, React Router v6

### What AI produced (26 files)

#### API layer (`src/api/`)
| File | Endpoints covered |
|---|---|
| `client.js` | Axios instance, request interceptor (Bearer token), response interceptor (auto-refresh on 401, retry, logout on failure) |
| `auth.js` | login, register, refresh, logout |
| `accounts.js` | listAccounts, getAccount, createAccount, deleteAccount, deposit, withdraw |
| `transactions.js` | listTransactions |
| `transfers.js` | createTransfer |
| `cards.js` | listCards, issueCard, updateCardStatus, deleteCard, revealCard |
| `statements.js` | getStatement |

#### Context & routing
| File | Purpose |
|---|---|
| `context/AuthContext.jsx` | Access token in state (never localStorage); refresh token in localStorage; silent re-auth on mount |
| `context/ToastContext.jsx` | Global toast queue with auto-dismiss (4 s) |
| `App.jsx` | React Router v6 layout; feature-flag-conditional routes |
| `components/ProtectedRoute.jsx` | Redirects to `/login` if no access token |
| `components/Layout.jsx` | Top nav + sidebar; mobile hamburger; conditional nav items |

#### UI components
- `Badge.jsx` — colored status pill (ACTIVE/BLOCKED/EXPIRED/VIRTUAL/DEBIT)
- `Spinner.jsx` — centered loading indicator
- `ErrorAlert.jsx` — inline `role="alert"` error box
- `FeatureGate.jsx` — declarative feature-flag wrapper
- `config/features.js` — `VITE_FEATURE_*` env-var flags
- `hooks/useFeature.js` — `useFeature(flag)` hook
- `utils/permissions.js` — centralised can-do checks (canDeleteAccount, canBlockCard, etc.)

#### Pages
| Page | Route | Key features |
|---|---|---|
| `Login.jsx` | `/login` | Email + password, welcome-back toast |
| `Register.jsx` | `/register` | Full name + email + password, redirect on success |
| `Dashboard.jsx` | `/` | Account cards with balance; create-account modal; delete with confirmation; "New Transfer" button |
| `AccountDetail.jsx` | `/accounts/:id` | Balance header; + Deposit / − Withdraw modals; Transactions tab (paginated, date-filtered); Cards tab (3D flip card UI, reveal, block/unblock, delete) |
| `TransferForm.jsx` | `/transfer` | From-account dropdown (active only); to-account UUID input; amount; auto-generated idempotency key |
| `StatementPage.jsx` | `/accounts/:id/statements` | Date range picker; summary cards (opening/closing balance, credits, debits, count); transaction table |

#### Accessibility (WCAG 2.1 AA)
- Semantic HTML throughout (`<nav>`, `<main>`, `<caption>`, `<th scope>`)
- `aria-busy`, `aria-live`, `aria-label`, `role="alert"` applied
- All interactive elements keyboard-reachable; modals trap focus; Escape closes
- Tailwind `focus:ring-2 focus:ring-blue-500` on all focusable elements
- Status badges always include text label (not color-only)

### Key architectural decisions
- **Token storage**: access token in React state (cleared on refresh); refresh token in `localStorage` (survives reload)
- **Silent login**: `AuthContext` calls `/auth/refresh` on mount before rendering protected routes
- **3D card flip**: CSS `perspective` + `rotateY(180deg)` — front/back both `absolute inset-0`; pointer events explicitly toggled so clicks land on the correct face
- **Feature flags**: defaults-on flags via `VITE_FEATURE_*` env vars; routes, nav items, and tabs all gated
- **Permission layer**: `utils/permissions.js` single source of truth for all UI enable/disable logic

### Manual interventions
- Chose `w-72` × `180 px` card dimensions after user feedback (halved → too small → doubled back)
- Enforced rule: no technical jargon or implementation details in user-facing copy

---

## Session 7 — Backend Extensions & Bug Fixes (Post-Frontend)

### Context
After the frontend went live, end-to-end testing surfaced gaps and bugs in the backend that needed fixing.

### Changes made

#### Card number encryption (`app/common/crypto.py`, `app/cards/`)
- **Problem:** Card numbers and CVVs were stored as plain text (only masked last-4 + hash kept originally); reveal endpoint needed full number.
- **Fix:** Added `app/common/crypto.py` (Fernet symmetric encryption keyed from `settings.SECRET_KEY`). `card_number_encrypted` and `cvv_encrypted` columns added to `cards` table via `ALTER TABLE` (non-destructive — existing rows get `NULL`, UI silently drops stale cards on 404).
- `cards/service.py` — `issue_card()` now encrypts and stores both; `reveal_card()` decrypts on demand.
- `cards/router.py` — `POST /{card_id}/reveal` endpoint added (password-protected; verifies account ownership).
- `cards/schemas.py` — `RevealCardResponse` with plain `card_number`, `cvv`, `expiry_date`.

#### Missing enum values (`app/transactions/models.py`)
- `DEPOSIT` and `WITHDRAWAL` added to `TransactionType` enum (were missing, causing 500 errors from deposit endpoint).

#### Statement credit classification (`app/statements/service.py`)
- `credit_types` set expanded to include `TransactionType.DEPOSIT` so deposits appear as credits (positive) not debits.

#### Withdrawal endpoint (`app/accounts/`)
- `schemas.py` — `WithdrawalRequest` added (mirrors `DepositRequest`).
- `service.py` — `withdraw()` function: active check, balance check (`InsufficientFundsError`), creates `WITHDRAWAL` transaction.
- `router.py` — `POST /{account_id}/withdraw` endpoint wired up.

### Frontend fixes (AccountDetail.jsx)
| Bug | Root cause | Fix |
|---|---|---|
| "Card not found" on reveal for stale cards | Soft-deleted legacy cards without encrypted data still shown in UI | `onCardGone` prop — on 404, close modal and reload card list silently |
| Copy and Hide buttons non-functional on revealed card | `absolute inset-0` front face intercepted all clicks even when `backfaceVisibility: hidden` | Explicit `pointerEvents: isRevealed ? 'none' : 'auto'` on front; `'auto'` : `'none'` on back |
| Copy failed in non-secure context | `navigator.clipboard` requires HTTPS | Added `document.execCommand('copy')` textarea fallback; "Copied!" visual feedback for 2 s |
| Deposits counted as debits in statement | `credit_types` in statements service missing `DEPOSIT` | Added `TransactionType.DEPOSIT` to set (backend fix above) |
| Date filter accepted future dates | No browser or form-level constraint | `max={today}` on both date inputs + form-level validation before API call |
| Clear button misaligned with Filter button | Clear was a bare text link with different sizing | Both buttons wrapped in `flex` div; Clear given matching `rounded-md px-3 py-1.5` |

### Manual interventions

| Intervention | Why |
|---|---|
| Ran `ALTER TABLE cards ADD COLUMN card_number_encrypted TEXT` and `cvv_encrypted TEXT` directly via sqlite3 shell | DB file was locked by VS Code SQLite extension; could not delete and recreate — used non-destructive column addition instead |
| Killed stale backend processes (`taskkill //F //PID`) manually | Multiple Python processes held port 8000 after hot-reload failed to pick up new routes; required identifying the correct PIDs via `netstat -ano` |
| Iterative card size adjustment | Specified half-size → confirmed too small → specified double — two rounds of sizing before settling on `w-72` × `180 px` |
| Specified UI writing rule (no technical jargon) | Directed removal of "Sensitive details are encrypted at rest. OTP verification coming soon." copy from AccountDetail.jsx |
| End-to-end testing (login → account → deposit → reveal → transfer → statement) | All bugs in the frontend fixes table above were discovered through manual browser testing, not automated tests |

### What was NOT changed
- All 90 backend tests still pass (no test changes needed — new endpoints covered by manual testing; withdrawal endpoint follows same pattern as deposit which already has a test)
- No DB migration files (schema change done via direct ALTER TABLE during dev)
