# Banking REST Service — Claude Prompt Usage Guide

> **Golden Rule:** Plan → Approve → Code. Never skip the approval step.  
> Bugs found in the plan cost nothing. Bugs found in production cost everything.

---

## The Workflow

```
Kickoff → Review Plan → Approve → Scaffold → Feature → Test → Review → Release
              ↑
      Your most important step.
      Fix problems here, not in the code.
```

---

## Phase 1 — Plan

### 1.1 Kickoff

**When to use:** Starting the project from scratch.

**Fill in and paste:**
```
<context>
  [paste output of: tree app/]
  [or upload files via paperclip]
</context>

<role>Senior Staff Engineer at a financial institution</role>

<task>
  We are building a production-ready banking REST service.
  Requirements: [PASTE SPEC HERE]
  Stack: Python 3.12+, FastAPI, SQLAlchemy 2.0 async, Pydantic v2, Alembic, PostgreSQL
</task>

<constraints>
  - No code yet. Plan only.
  - Domain-driven folder structure (not monolithic)
  - Monetary fields must use Decimal — call it out if anything else is used
  - Include auth, idempotency, and audit trail in the design from the start
</constraints>

<o>
  1. Folder structure
  2. Data models with field types
  3. API endpoints (method, path, auth required, request/response shape)
  4. Key design decisions and why
</o>
```

**Before approving the plan, check for:**

| Red Flag | Fix |
|----------|-----|
| `float` for balance or amount | "Use `Numeric(precision=18, scale=4)` instead" |
| No `idempotency_key` on transactions | "Add idempotency_key as unique UUID field" |
| Hard deletes on financial records | "Switch to soft delete — add nullable `deleted_at`" |
| Endpoints missing auth | "Which endpoints need JWT? What role?" |
| No audit table in schema | "Add an append-only AuditLog table" |

---

### 1.2 Design Decision

**When to use:** Unsure about an architecture choice.

```
<context>
  [paste relevant files or describe current architecture]
</context>

<role>Senior Staff Engineer at a financial institution</role>

<question>
  [e.g. Should I use JWT or sessions? Soft delete or hard delete?]
</question>

<o>
  - Trade-offs in a banking context
  - Your recommendation and reasoning
  - Key trade-off considerations for production banking systems
</o>
```

---

## Phase 2 — Code

> Security and validation are part of every feature — not a separate step.

### 2.1 Scaffold

**When to use:** After the plan is approved. Generates the base project structure.

```
<context>
  [paste the approved plan from Phase 1]
</context>

<role>Senior Staff Engineer at a financial institution</role>

<task>
  Build the project scaffold based on the approved plan.
</task>

<must_include>
  - JWT auth wired up from the start
  - Pydantic v2 strict schemas
  - Decimal for all monetary values — never float
  - Global error handler with structured responses
  - Correlation ID on every request (for tracing)
  - Config via environment variables — no hardcoded values
</must_include>

<o>
  Generate files in order: config → db session → base models → main app entry
  Note the file path at the top of every code block.
  End with key decisions and reasoning behind them.
</o>
```

---

### 2.2 Feature

**When to use:** Implementing a new feature. Use once per feature, not in bulk.

```
<context>
  [paste relevant existing files: models.py, service.py, router.py]
</context>

<role>Senior Staff Engineer at a financial institution</role>

<task>
  Implement: [e.g. "transfer funds between two accounts"]
</task>

<requirements>
  - Validate all inputs at the API boundary — reject bad data early
  - Auth check: confirm the requesting user owns the resource
  - If this touches money: make it idempotent and wrap in a single transaction
  - Write to the audit log on every state change
  - Return structured error responses — no raw exceptions exposed
</requirements>

<o>
  Think through failure scenarios first.
  Then: schema → service → router, each with file path noted.
  Flag anything that needs careful consideration in a banking context.
</o>
```

---

### 2.3 Debug

**When to use:** Something is broken.

```
<context>
  [paste the file(s) where the bug lives]
</context>

<role>Senior Staff Engineer at a financial institution</role>

<problem>
  [describe the bug or paste the full error]
</problem>

<o>
  Root cause first. Then the fix. Confirm nothing new is broken security-wise.
</o>
```

---

## Phase 3 — Test

> Test after each feature. Do not batch tests at the end.

### 3.1 Write Tests

**When to use:** After each feature is implemented.

```
<context>
  [paste the feature code just written]
</context>

<role>Senior Staff Engineer at a financial institution</role>

<task>
  Write tests for: [feature name]
  Framework: pytest + pytest-asyncio + httpx
</task>

<o>
  Cover in this order: happy path → invalid input → auth failure → financial edge cases
  Note file paths. Be honest about what is not covered and why.
</o>
```

---

### 3.2 Coverage Check

**When to use:** Before review or release.

```
<context>
  [paste all service/router files, or use Claude Project]
</context>

<role>Senior Staff Engineer at a financial institution</role>

<task>Review what is and isn't tested across the codebase.</task>

<o>
  List gaps by priority: CRITICAL / HIGH / MEDIUM
  Write the most important missing tests.
</o>
```

---

## Phase 4 — Review

### 4.1 Code Review

**When to use:** Before merging a feature branch.

```
<context>
  [paste all files for review, or use Claude Project]
</context>

<role>Senior Staff Engineer at a financial institution</role>

<task>Review the full codebase and be direct about what needs fixing.</task>

<o>
  Issues found (label severity: CRITICAL / HIGH / MEDIUM / LOW)
  Specific fixes with before/after snippets

  Banking checklist:
  - Decimal everywhere money is handled?
  - Every endpoint behind auth?
  - Financial ops idempotent?
  - Audit trail on state changes?
  - No PII in logs?
  - Soft deletes on financial records?
  - Transactions roll back on failure?
  - Clean error responses throughout?
</o>
```

---

### 4.2 Pre-Submit

**When to use:** Final check before pushing to production.

```
<context>
  [paste full codebase or use Claude Project]
</context>

<role>Senior Staff Engineer at a financial institution</role>

<task>Final check before release. Validate the service is production-ready.</task>

<o>
  Run through the full banking checklist above.
  Flag every gap with a fix.
  Give a straight verdict: NOT READY / NEEDS WORK / READY
</o>
```

---

## Quick Reference

| Situation | Use |
|-----------|-----|
| Starting from scratch | `1.1 Kickoff` |
| Unsure about a design choice | `1.2 Design Decision` |
| Plan approved, starting to build | `2.1 Scaffold` |
| Building a new feature | `2.2 Feature` |
| Something is broken | `2.3 Debug` |
| Feature just finished | `3.1 Write Tests` |
| About to review or release | `3.2 Coverage Check` |
| Before merging a branch | `4.1 Code Review` |
| About to push to production | `4.2 Pre-Submit` |