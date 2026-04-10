---
name: verify
description: Verification gate — no completion claims without fresh evidence
---

# Verification Before Completion

## The Iron Law

NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.

## The Gate Function

BEFORE claiming any status ("done", "fixed", "working", "passes"):

1. **IDENTIFY** — What command proves this claim?
2. **RUN** — Execute the FULL command (fresh, not cached)
3. **READ** — Full output, check exit code, count failures
4. **VERIFY** — Does output actually confirm the claim?
5. **ONLY THEN** — Make the claim with evidence

## Rationalization Prevention

| Excuse | Reality |
|---|---|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence != evidence |
| "Just this once" | No exceptions |
| "Same as before" | Run it FRESH |

## For This Project

```bash
# Tests pass?
uv run pytest -x -v

# Type check?
uv run mypy src/

# Import works?
uv run python -c "from gh_trends import ..."

# Server starts?
uv run gh-trends serve &; sleep 2; curl localhost:8000/mcp; kill %1
```
