# Future Considerations & Roadmap

Features and improvements that can be added in subsequent phases. All are compatible with the existing architecture and require no breaking changes.

---

## Phase 1 — Security Hardening

| Feature | Description | Effort |
|---|---|---|
| Rate limiting | Per-IP and per-user request throttling using `slowapi` or similar | Small |
| Login throttling | Exponential backoff after failed authentication attempts | Small |
| Password complexity | Require uppercase, numeric, and special characters | Small |
| Security headers | Add `X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`, `Content-Security-Policy` | Small |
| CORS lockdown | Remove wildcard default; require explicit origin configuration | Small |
| OTP / 2FA | TOTP (Google Authenticator) or email code for card reveal, large transfers, and account deletion | Medium |
| Password reset | Forgot-password flow with time-limited email reset link (requires SendGrid, SES, or similar) | Medium |
| Session management UI | List active sessions (device, IP, last seen); allow remote logout of individual sessions | Medium |

---

## Phase 2 — Accounts & Transactions

| Feature | Description | Effort |
|---|---|---|
| Transaction categories | Tag transactions (Food, Rent, Salary); show spend-by-category chart on dashboard | Small |
| Bulk export (CSV) | Download transactions for a date range as CSV from the statement page | Small |
| Interest calculation | Savings accounts accrue interest at a configurable rate; scheduled job credits interest monthly | Medium |
| Recurring payments | Standing orders: schedule a transfer to repeat daily/weekly/monthly | Medium |
| Dispute / chargeback | Flag a transaction as disputed; backend records dispute status; admin resolves | Medium |

---

## Phase 3 — Cards

| Feature | Description | Effort |
|---|---|---|
| Luhn-valid card numbers | Replace random digit generation with Luhn-compliant algorithm | Small |
| Freeze / unfreeze | Distinguish between permanent BLOCKED and temporary FROZEN status | Small |
| Card spending limits | Per-card daily/monthly spend cap enforced on each transaction | Medium |
| Card PIN management | Set/change PIN (stored as bcrypt hash, never retrievable) | Medium |

---

## Phase 4 — Transfers

| Feature | Description | Effort |
|---|---|---|
| Beneficiary list | Save frequently used recipient accounts with a friendly name | Small |
| Scheduled transfers | Execute at a future datetime; processed by background job | Medium |
| Transfer receipts | Downloadable PDF receipt for each completed transfer | Medium |

---

## Phase 5 — Frontend & UX

| Feature | Description | Effort |
|---|---|---|
| Dark mode | Tailwind `dark:` class variant; preference stored in localStorage | Small |
| Audit log viewer | User-facing "Account activity" page showing login history and state changes | Small |
| Real-time balance updates | WebSocket or SSE push from backend on balance change | Medium |
| Admin panel | Separate `/admin` section: list users, view audit log, manage accounts | Large |
| Mobile app | React Native reusing the same API layer and `api/` modules | Large |

---

## Phase 6 — Infrastructure

| Feature | Description | Effort |
|---|---|---|
| Alembic migration files | Generate proper `alembic revision --autogenerate` migrations to replace manual ALTER TABLE | Small |
| CI/CD pipeline | GitHub Actions: lint, test (90 cases), build frontend, Docker image push on merge to main | Medium |
| PostgreSQL migration | Replace SQLite for concurrent write support; Alembic migrations are already set up | Medium |
| Production deployment | Nginx reverse proxy + Gunicorn/Uvicorn workers + static frontend from `dist/` | Medium |
| Database encryption at rest | SQLCipher for SQLite or PostgreSQL with TDE | Medium |
