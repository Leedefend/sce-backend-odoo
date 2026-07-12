# P4-P0-01 Makefile Split Evidence

Date: 2026-07-12
Branch: `topic/p4-p0-01-makefile-split`
Parent plan: `p0_split_plan_execution.md`

## Scope

This pass keeps public Make target names stable and moves the first low-risk target groups into included Make fragments.

Extracted fragments:

| Fragment | Responsibility |
| --- | --- |
| `make/guards.mk` | Production guards, Codex fast-mode guards, compose/env checks, and daily-dev environment guards. |
| `make/contract.mk` | Contract export, catalog, evidence, and contract gate targets. |
| `make/help.mk` | `make help` output. |
| `make/dev.mk` | Local dev, frontend dev server, daily-dev acceptance publish, prod-sim wrapper, and Odoo service helper targets. |

## Line Count Evidence

| File | Before | After |
| --- | ---: | ---: |
| `Makefile` | 6062 | 5679 |

The root Makefile remains a P0 split-plan file after this pass. The next pass should continue moving large coherent target groups into `make/*.mk` without changing public target names.

## Non-Scope

- No target behavior change.
- No product feature change.
- No production deployment.
- No frontend UI or backend model change.
- No cleanup of unrelated P1/P2 split-plan files.

## Verification

```text
make -n help
make -n env.print.db
make -n check-compose-env
git diff --check
make ci
```

Latest local result:

```text
make ci: passed
complexity budget report: current
split plan queue: current
frontend lint/typecheck/build: passed
v1.1 E2E preflight: passed
```
