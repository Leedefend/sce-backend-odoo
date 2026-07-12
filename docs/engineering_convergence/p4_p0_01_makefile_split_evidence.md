# P4-P0-01 Makefile Split Evidence

Date: 2026-07-12
Branch: `topic/p4-p0-01-makefile-split`
Parent plan: `p0_split_plan_execution.md`

## Scope

This pass keeps public Make target names stable and moves coherent target groups into included Make fragments.

Extracted fragments:

| Fragment | Responsibility |
| --- | --- |
| `make/guards.mk` | Production guards, Codex fast-mode guards, compose/env checks, and daily-dev environment guards. |
| `make/contract.mk` | Contract export, catalog, evidence, and contract gate targets. |
| `make/help.mk` | `make help` output. |
| `make/dev.mk` | Local dev, frontend dev server, daily-dev acceptance publish, prod-sim wrapper, and Odoo service helper targets. |
| `make/runtime_ops.mk` | Runtime operations, migration, attachment, deployment, production validation, and data repair targets. |
| `make/frontend.mk` | Frontend build, static publish, browser smoke, and visual/user acceptance targets. |
| `make/codex.mk` | Codex SOP, PR helper, branch cleanup, and main sync targets. |
| `make/dev_test.mk` | Development test, contract, boundary, productization, low-code, and scene verification targets. |
| `make/ci.mk` | CI entrypoints, diagnostics, Continue helpers, and v1.1 engineering convergence quality targets. |

## Line Count Evidence

| File | Before | After |
| --- | ---: | ---: |
| `Makefile` | 6062 | 272 |

The root Makefile is now below the split-plan threshold and has exited the P0 split-plan queue. It should remain a thin variable and include entrypoint; future target bodies should be added to `make/*.mk` fragments or scripts.

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
make -n codex.fast
make -n verify.contract.preflight
make -n ci
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

Latest remote result:

```text
GitHub Actions v1.1 quality gate: passed
Run: 29189232441
Duration: 2m31s
Head: a4f54ac43
```
