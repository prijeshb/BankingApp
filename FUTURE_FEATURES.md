# Future Features / Roadmap

Features that could be added in subsequent phases. All are compatible with the existing architecture and require no breaking changes.

---

## Security & Auth

| Feature | Notes |
|---|---|
| OTP / 2FA on sensitive actions | Verify identity before card reveal, large transfers, or account deletion — TOTP (Google Authenticator) or email code |
| Password reset via email | Forgot-password flow: send time-limited reset link; requires an email service (SendGrid, SES) |
| Session management UI | List active sessions (device, IP, last seen); allow remote logout of individual sessions |
| Per-user rate limiting | Throttle login attempts and transfer submissions to prevent brute force and abuse |

---

## Accounts & Transactions

| Feature | Notes |
|---|---|
| Interest calculation | Savings accounts accrue interest at a configurable rate; scheduled job credits interest monthly |
| Recurring payments | Standing orders: schedule a transfer to repeat daily/weekly/monthly |
| Transaction categories | Tag transactions (Food, Rent, Salary…); show spend-by-category chart on dashboard |
| Dispute / chargeback | Flag a transaction as disputed; backend records dispute status; admin resolves |
| Bulk export (CSV) | Download all transactions for a date range as CSV from the statement page |

---

## Cards

| Feature | Notes |
|---|---|
| Card spending limits | Per-card daily/monthly spend cap; backend enforces on each transaction |
| Card PIN management | Set / change PIN (stored as bcrypt hash, never retrievable); used for POS simulation |
| Luhn-valid card numbers | Replace random digit generation with Luhn-compliant algorithm |
| Freeze / unfreeze (temp block) | Distinction between permanent BLOCKED and temporary FROZEN status |

---

## Transfers

| Feature | Notes |
|---|---|
| Scheduled transfers | Transfer executes at a future datetime; stored with `scheduled_at`; processed by background job |
| Transfer receipts | Downloadable PDF receipt for each completed transfer |
| Beneficiary / payee list | Save frequently used recipient account IDs with a friendly name |

---

## Frontend / UX

| Feature | Notes |
|---|---|
| Dark mode | Tailwind `dark:` class variant; preference stored in localStorage |
| Real-time balance updates | WebSocket or SSE push from backend on balance change; no manual refresh needed |
| Admin panel | Separate `/admin` section: list all users, view audit log, activate/deactivate accounts |
| Mobile app | React Native reusing the same API layer and `api/` modules |
| Audit log viewer | User-facing "Account activity" page showing login history and state changes from the audit table |

---

## Infrastructure

| Feature | Notes |
|---|---|
| PostgreSQL migration | Replace SQLite with PostgreSQL for concurrent write support; Alembic migrations are already set up |
| Alembic migration files | Generate proper `alembic revision --autogenerate` migrations to replace the manual ALTER TABLE approach |
| Docker production deploy | Nginx reverse proxy + Gunicorn/Uvicorn workers + static frontend served from `dist/` |
| CI/CD pipeline | GitHub Actions: lint → test (90 cases) → build frontend → Docker image push on merge to main |
