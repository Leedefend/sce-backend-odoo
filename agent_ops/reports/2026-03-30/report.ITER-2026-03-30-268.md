# ITER-2026-03-30-268 Report

## Summary

- Hardened frontend startup recovery for stale-auth initialization failures.
- Kept scope within frontend startup chain only.

## Changed Files

- `frontend/apps/web/src/stores/session.ts`
- `frontend/apps/web/src/app/init.ts`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-268.yaml`
- `bash -n scripts/dev/frontend_dev_reset.sh`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- Low
- Behavior change is limited to `system.init` auth-failure recovery during startup.
- Non-auth init failures still remain visible through existing error state.

## Rollback

```bash
git restore frontend/apps/web/src/stores/session.ts frontend/apps/web/src/app/init.ts
```

## Next Suggestion

- Reproduce with the current dev runtime and confirm stale tokens now redirect to `/login` instead of leaving the app in init error state.
