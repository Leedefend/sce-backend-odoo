# ITER-2026-03-30-274 Report

## Summary

- Stabilized the frontend dev runtime so `make fe.dev.reset` no longer relies on a one-shot shell background process.
- Switched the reset path to a persistent `tmux` session and pinned frontend dev startup to Node 20.
- Verified that the dev server remains bound on `127.0.0.1:5174` after the reset command exits.

## Changed Files

- `Makefile`
- `scripts/dev/frontend_dev_reset.sh`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-274.yaml`
- `bash -n scripts/dev/frontend_dev_reset.sh`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`
- `bash scripts/dev/frontend_dev_reset.sh`
- `ss -ltnp | grep 5174 || true`
- `curl -I --max-time 5 http://127.0.0.1:5174/`

## Risk

- Low
- Scope is limited to frontend development runtime startup and does not change product behavior.
- Residual risk is limited to host environments without `tmux`; the script now fails explicitly in that case instead of reporting a false ready state.

## Rollback

```bash
git restore Makefile scripts/dev/frontend_dev_reset.sh
```

## Next Suggestion

- Keep `make fe.dev.reset` as the canonical recovery path for frontend dev.
- If browser-side HMR still shows stale modules after this fix, inspect websocket/HMR client behavior separately from process-lifetime issues.
