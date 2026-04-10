---
name: review
description: Fix-First code review — auto-fix obvious issues, batch-ask the rest
---

# Code Review (Fix-First)

## Workflow

### Step 1: Get the diff
```bash
git diff main...HEAD    # or git diff --staged
```

### Step 2: Critical pass
Check every change against:
- **Injection** — SQL, shell, XSS in any user-facing output
- **Async safety** — unclosed clients, missing await, resource leaks
- **API keys/secrets** — hardcoded tokens, .env committed
- **Type safety** — Pydantic model_dump vs dict(), v2 patterns
- **Import errors** — missing deps, circular imports

### Step 3: Fix-First review

**3a. Classify each finding:**
- `AUTO-FIX` — obvious typo, missing import, style issue, unused variable
- `ASK` — design choice, behavior change, unclear intent

**3b. Auto-fix all AUTO-FIX items:**
```
[AUTO-FIXED] file:line — Problem → what you did
```

**3c. Batch-ask about ASK items:**
Present in ONE question with numbered items:
```
1. [file:line] Issue description — A) Fix / B) Skip
2. [file:line] Issue description — A) Fix / B) Skip
```

### Step 4: Verify
```bash
uv run pytest -x -v
uv run python -c "from gh_trends import ..."
```

## Rules
- Search before recommending — verify patterns are current for the framework
- Read code OUTSIDE the diff when checking enum/value completeness
- Never say "LGTM" without running verification
