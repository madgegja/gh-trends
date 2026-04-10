---
name: tdd
description: Test-Driven Development — RED-GREEN-REFACTOR with pytest. TRIGGER when writing new functions, adding features, or user mentions "test", "TDD", "coverage". Auto-apply the Iron Law before any production code.
---

# TDD (Test-Driven Development)

## The Iron Law

NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.

Write code before the test? Delete it. Start over. No exceptions.

## Workflow

### RED — Write Failing Test
```bash
# One behavior. Clear name. Real assertions.
uv run pytest tests/test_<module>.py -x -v
```
- One minimal test showing what should happen
- No mocks unless unavoidable (prefer real objects)
- Test MUST fail (not error) — failure message should describe missing feature

### GREEN — Minimal Code
- Simplest code to pass the test. Nothing more.
- Don't add features, refactor, or "improve" beyond the test.

### REFACTOR — Clean Up
- After green only. Keep tests green. Don't add behavior.
- Extract duplication. Improve names. Simplify.

## Python/pytest Patterns

```python
# Parametrize for multiple cases
@pytest.mark.parametrize("input,expected", [...])
def test_something(input, expected): ...

# Async tests (httpx)
@pytest.mark.asyncio
async def test_fetch(): ...

# Fixtures for shared setup
@pytest.fixture
def snapshot(): ...
```

## Rules
- Run full test suite after each GREEN: `uv run pytest -x -v`
- Coverage target: 80%+ for new code
- Never skip RED verification — watch it fail first
