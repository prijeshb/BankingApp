# PROMPTS — Banking REST Service

Use `@Workspace` so Claude sees your actual codebase.
Follow the **Plan → Approve → Code** rule — never skip the approval step.

---

## PHASE 1 — PLAN

### Kickoff
```
@Workspace

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

<output>
  1. Folder structure
  2. Data models with field types
  3. API endpoints (method, path, auth required, request/response shape)
  4. Key design decisions and why
</output>
```

### Design Decision
```
@Workspace

<role>Senior Staff Engineer at a financial institution</role>

<question>
  [e.g. Should I use JWT or sessions? Soft delete or hard delete?]
</question>

<output>
  - Trade-offs in a banking context
  - Your recommendation and reasoning
  - Key trade-off considerations for production banking systems
</output>
```

---

## PHASE 2 — CODE

> Security and validation are part of every feature — not a separate step.

### Scaffold
```
@Workspace

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

<output>
  Generate files in order: config → db session → base models → main app entry
  Note the file path at the top of every code block.
  End with key decisions and reasoning behind them.
</output>
```

### Feature
```
@Workspace

<role>Senior Staff Engineer at a financial institution</role>

<task>
  Implement: [describe the feature, e.g. "transfer funds between two accounts"]
</task>

<requirements>
  - Validate all inputs at the API boundary — reject bad data early
  - Auth check: confirm the requesting user owns the resource
  - If this touches money: make it idempotent and wrap it in a single transaction
  - Write to the audit log on every state change
  - Return structured error responses — no raw exceptions exposed
</requirements>

<output>
  Think through failure scenarios first.
  Then: schema → service → router, each with file path noted.
  Flag anything that needs careful consideration in a banking context.
</output>
```

### Debug
```
@Workspace

<role>Senior Staff Engineer at a financial institution</role>

<problem>
  [Describe the bug or paste the error]
</problem>

<output>
  Root cause first. Then the fix. Confirm nothing new is broken security-wise.
</output>
```

---

## PHASE 3 — TEST

### Write Tests
```
@Workspace

<role>Senior Staff Engineer at a financial institution</role>

<task>
  Write tests for: [feature name or paste code]
  Framework: pytest + pytest-asyncio + httpx
</task>

<output>
  Cover in this order: happy path → invalid input → auth failure → financial edge cases
  Note file paths. Be honest about what is not covered and why.
</output>
```

### Coverage Check
```
@Workspace

<role>Senior Staff Engineer at a financial institution</role>

<task>Review what is and isn't tested across the codebase.</task>

<output>
  List gaps by priority: CRITICAL / HIGH / MEDIUM
  Write the most important missing tests.
</output>
```

---

## PHASE 4 — REVIEW

### Code Review
```
@Workspace

<role>Senior Staff Engineer at a financial institution</role>

<task>Review the full codebase and be direct about what needs fixing.</task>

<output>
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


</output>
```

### Pre-Submit
```
@Workspace

<role>Senior Staff Engineer at a financial institution</role>

<task>Final check before release. Validate the service is production-ready.</task>

<output>
  Run through the full banking checklist above.
  Flag every gap with a fix.
  Give a straight verdict: NOT READY / NEEDS WORK / READY
</output>
```

---

## The Workflow

```
Kickoff → read the plan → catch issues → approve → Scaffold → Feature → Test → Review → Release
                  ↑
          Your most important job.
          Fix problems in the plan, not in the code.
```

**What to watch for before approving the plan:**

| Spot this | Fix it with |
|-----------|-------------|
| `float` for balance or amount fields | "Use `Numeric(precision=18, scale=4)` instead" |
| No idempotency_key on transaction table | "Add idempotency_key as a unique UUID field" |
| Hard deletes on financial records | "Switch to soft delete — add nullable `deleted_at` timestamp" |
| Auth not specified on endpoints | "Which endpoints need JWT? What role?" |
| No audit table in the schema | "Add an append-only AuditLog table" |