# Security Considerations

This document describes the security measures implemented in the Banking REST Service and lists known limitations.

---

## Authentication

| Mechanism | Details |
|---|---|
| Password hashing | bcrypt with automatic salt generation |
| Access tokens | JWT (HS256), 15-minute expiry, stored in React state (never persisted to disk) |
| Refresh tokens | 7-day expiry, SHA-256 hashed before database storage, revocable |
| Token refresh | Validates token is not revoked, not expired, and user account is still active |
| Logout | Revokes refresh token with ownership check (only the token owner can revoke it) |
| User enumeration prevention | Login returns the same error message for wrong password and non-existent email |

### JWT Secret Key

The `JWT_SECRET_KEY` environment variable must be set to a cryptographically random value. The application rejects the default placeholder value on startup. Generate one with:

```bash
openssl rand -hex 32
```

---

## Encryption

Card numbers and CVVs are encrypted at rest using Fernet symmetric encryption (AES-128-CBC with HMAC-SHA256 authentication).

| Data | Storage | Purpose |
|---|---|---|
| Full card number | Fernet encrypted | Revealed only after password verification |
| CVV | Fernet encrypted | Revealed only after password verification |
| Masked number | Plaintext (last 4 digits) | Displayed in UI |
| Card number hash | SHA-256 | Fast lookups without exposing plaintext |

The encryption key is derived from `JWT_SECRET_KEY` via SHA-256.

---

## Input Validation

- All path parameters for resource IDs are validated against a UUID regex before reaching any business logic (returns 422 for malformed IDs)
- Pydantic v2 schemas validate request bodies with strict type and length constraints
- Email addresses validated via `email-validator` (RFC 5322)
- Card status updates reject `EXPIRED` at both schema and service layers
- Financial amounts use `Decimal(18,4)` — never `float`

---

## Authorization & Ownership

Every protected endpoint verifies the requesting user owns the resource:

| Resource | Ownership check |
|---|---|
| Account | `account.owner_id == current_user.id` |
| Card | Verified via parent account ownership |
| Transfer | Only the source account owner can initiate; both sender and recipient can view |
| User profile | Users can only access/modify their own profile |

Ownership violations return 403 Forbidden with no information about the resource.

---

## Transfer Safety

- **Atomicity:** Both balance mutations and transaction records are created in a single database transaction — either all succeed or all roll back
- **Idempotency:** Client-provided idempotency key with unique constraint prevents duplicate processing; retries return 409 Conflict
- **Balance check:** Insufficient funds rejected before any mutation
- **Same-account check:** Transfers to the same account are rejected

---

## Audit Trail

An append-only audit log records state changes with:
- User ID, action type, resource type and ID
- Client IP address
- Correlation ID (links to the specific request)
- Old and new values (for updates)
- Immutable timestamp

Audited events include: registration, login, logout, account creation/deletion, card operations, and transfers.

---

## Database

- SQLite with WAL mode (crash-safe journaling) and foreign key enforcement
- All queries use SQLAlchemy ORM with parameterized statements (no SQL injection risk)
- Soft deletes on users, accounts, and cards (data preserved for compliance)
- Transactions and audit logs are append-only (never modified or deleted)

---

## Error Handling

- Unhandled exceptions return a generic "An unexpected error occurred" message with no stack trace
- Validation errors return field-level details without internal implementation information
- All exceptions are logged server-side with correlation IDs for debugging

---

## Request Tracing

Every request receives a `X-Correlation-ID` header (generated if not provided). This ID is:
- Included in all log entries for the request
- Stored in audit log records
- Returned in the response header

---

## Known Limitations

These are areas where the current implementation does not yet meet production-grade security standards:

| Area | Current state | Recommendation |
|---|---|---|
| Rate limiting | Not implemented | Add per-IP and per-user rate limiting (e.g., `slowapi`) |
| Login throttling | No brute force protection | Implement exponential backoff after failed attempts |
| Password complexity | Minimum 8 characters only | Add requirements for uppercase, numeric, and special characters |
| Security headers | Not set | Add `X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`, `Content-Security-Policy` |
| CORS | Defaults to `["*"]` if env var not set | Always set `ALLOWED_ORIGINS` explicitly in production |
| Database encryption | SQLite file not encrypted at rest | Consider SQLCipher or migrate to PostgreSQL with TDE |
| 2FA / MFA | Not implemented | Add TOTP or email-based verification for sensitive operations |
| Session concurrency | No detection of concurrent logins | Consider session invalidation or notification |
| API key rotation | Single JWT secret key | Implement key rotation with grace period |
| Refresh token TTL | 7 days | Consider shorter TTL with sliding window refresh |
