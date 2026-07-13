# Commit Convention

All commits during v1.1 convergence must use a short typed subject:

```text
<type>: <imperative summary>
```

Allowed types:

- `feat`: approved user-facing capability.
- `fix`: defect correction.
- `refactor`: internal structure change without intended behavior change.
- `test`: test, guard, fixture, or validation evidence.
- `docs`: documentation, runbook, ADR, or governance evidence.
- `chore`: repository, CI, dependency, formatting, or operational maintenance.

Rules:

- Keep the subject focused on one change set.
- Do not mix product behavior, migration, and unrelated cleanup in one commit.
- Prefer separate commits for governance, test infrastructure, and product fixes.
- Reference the GitHub issue in the PR, not necessarily every commit.
- Do not commit generated secrets, local environment files, or production-only data.

Examples:

```text
chore: establish v1.1 engineering convergence gate
test: inventory convergence validation assets
fix: enforce project isolation in intent access
docs: record backup restore drill evidence
```
