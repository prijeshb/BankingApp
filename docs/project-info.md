# Project Info

## Project Structure

```
├── app/                        # FastAPI backend
│   ├── main.py                 # Application entry point
│   ├── config.py               # Environment-based settings
│   ├── database.py             # Async SQLAlchemy engine (SQLite + WAL)
│   ├── common/                 # Shared utilities
│   │   ├── base_model.py       # UUID PK + timestamp mixins
│   │   ├── crypto.py           # Fernet encryption for card data
│   │   ├── exceptions.py       # Domain exceptions + error handlers
│   │   ├── health.py           # Health check endpoints
│   │   ├── logging.py          # Structured JSON logging (structlog)
│   │   ├── middleware.py       # Correlation ID middleware
│   │   └── types.py            # Shared types (UUIDPath)
│   ├── auth/                   # JWT authentication (register, login, refresh, logout)
│   ├── users/                  # User profile CRUD with soft delete
│   ├── accounts/               # Account create/list/get/delete, deposit, withdraw
│   ├── transactions/           # Append-only transaction ledger
│   ├── transfers/              # Atomic fund transfers with idempotency
│   ├── cards/                  # Card issuance, block/unblock, encrypted storage
│   ├── statements/             # Date-range account statements
│   └── audit/                  # Append-only audit log
├── frontend/                   # React SPA
│   └── src/
│       ├── api/                # Axios client + API modules
│       ├── components/         # Layout, Badge, Spinner, ErrorAlert, FeatureGate
│       ├── config/             # Feature flags
│       ├── context/            # AuthContext, ToastContext
│       ├── hooks/              # useFeature
│       ├── pages/              # Login, Register, Dashboard, AccountDetail, TransferForm, StatementPage
│       └── utils/              # Permission helpers
├── tests/                      # pytest test suite
│   ├── conftest.py             # Async fixtures, test DB setup
│   ├── integration/            # 7 test files (auth, accounts, transactions, transfers, cards, statements, health)
│   └── unit/                   # 3 test files (auth service, transfer validation, account schemas)
├── alembic/                    # Database migrations
├── Dockerfile                  # Multi-stage build (Node + Python)
├── docker-compose.yml          # Production config
└── docker-compose.override.yml # Dev hot-reload
```

## API Endpoints

All API routes are prefixed with `/api/v1`. Authentication uses JWT Bearer tokens.

| Domain | Method | Endpoint | Auth |
|---|---|---|---|
| Health | GET | `/health`, `/health/ready`, `/health/live` | No |
| Auth | POST | `/auth/register` | No |
| Auth | POST | `/auth/login` | No |
| Auth | POST | `/auth/refresh` | No |
| Auth | POST | `/auth/logout` | Yes |
| Users | GET | `/users/me` | Yes |
| Users | PATCH | `/users/me` | Yes |
| Users | DELETE | `/users/me` | Yes |
| Accounts | GET | `/accounts/` | Yes |
| Accounts | POST | `/accounts/` | Yes |
| Accounts | GET | `/accounts/{id}` | Yes |
| Accounts | DELETE | `/accounts/{id}` | Yes |
| Accounts | POST | `/accounts/{id}/deposit` | Yes |
| Accounts | POST | `/accounts/{id}/withdraw` | Yes |
| Accounts | GET | `/accounts/lookup/{account_number}` | Yes |
| Transactions | GET | `/accounts/{id}/transactions/` | Yes |
| Transactions | GET | `/accounts/{id}/transactions/{tx_id}` | Yes |
| Transfers | POST | `/transfers` | Yes |
| Cards | GET | `/accounts/{id}/cards` | Yes |
| Cards | POST | `/accounts/{id}/cards` | Yes |
| Cards | GET | `/accounts/{id}/cards/{card_id}` | Yes |
| Cards | PATCH | `/accounts/{id}/cards/{card_id}/status` | Yes |
| Cards | DELETE | `/accounts/{id}/cards/{card_id}` | Yes |
| Cards | POST | `/accounts/{id}/cards/{card_id}/reveal` | Yes |
| Statements | GET | `/accounts/{id}/statements/` | Yes |

Interactive API documentation is available at `/docs` (Swagger UI) and `/redoc` when the backend is running.

## Architecture

### Backend

- **Framework:** FastAPI with async SQLAlchemy 2.0
- **Database:** SQLite with WAL mode and foreign key enforcement
- **Auth:** JWT access tokens (15 min) + refresh tokens (7 days). Access tokens are stateless; refresh tokens are stored server-side and revocable.
- **Money:** All monetary values use `Decimal(18,4)` — never `float`
- **Transfers:** Atomic debit + credit in a single database transaction with idempotency key to prevent duplicate processing
- **Cards:** Card numbers and CVVs encrypted at rest with Fernet symmetric encryption. Only masked last-4 digits and SHA-256 hash stored in plain text.
- **Audit:** Append-only audit log records every state change with user ID, action, IP address, and timestamp
- **Soft deletes:** Users, accounts, and cards use `deleted_at` timestamps instead of hard deletes

### Frontend

- **Stack:** Vite + React 18 + Tailwind CSS + React Router v6 + Axios
- **Token storage:** Access token held in React state (never persisted). Refresh token in `localStorage` for silent re-auth on page reload.
- **Feature flags:** Togglable via `VITE_FEATURE_*` environment variables (Cards, Statements, Transfers, Virtual Cards)
- **Permissions:** Centralised permission checks in `utils/permissions.js` control button visibility and disabled states
- **Accessibility:** WCAG 2.1 AA — semantic HTML, ARIA attributes, keyboard navigation, focus management

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/banking.db` | Database connection string |
| `JWT_SECRET_KEY` | *(must be set)* | Secret key for JWT signing |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `ALLOWED_ORIGINS` | `["http://localhost:5173"]` | CORS allowed origins |
| `DEBUG` | `false` | Enable debug logging |

### Frontend feature flags (in `frontend/.env.local`)

| Variable | Default | Description |
|---|---|---|
| `VITE_FEATURE_CARDS` | `true` | Enable card management |
| `VITE_FEATURE_STATEMENTS` | `true` | Enable account statements |
| `VITE_FEATURE_TRANSFERS` | `true` | Enable fund transfers |
| `VITE_FEATURE_VIRTUAL_CARDS` | `true` | Enable virtual card issuance |
