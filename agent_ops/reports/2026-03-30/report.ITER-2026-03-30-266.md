# ITER-2026-03-30-266

## Summary
- Tightened the frontend dev reset flow so readiness depends on a live process and an actual localhost probe.
- Avoided stale-log false positives during Vite restart.

## Changed Files
- `agent_ops/tasks/ITER-2026-03-30-266.yaml`
- `scripts/dev/frontend_dev_reset.sh`

## Verification
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-266.yaml`
- PASS: `bash -n scripts/dev/frontend_dev_reset.sh`
- PASS: `make fe.dev.reset`
- PASS: `bash -lc 'curl -I --max-time 5 http://127.0.0.1:5174/'`

## Risk
- Low.
- Change is limited to the dev runtime reset script and does not alter frontend app code.

## Rollback
- `git restore agent_ops/tasks/ITER-2026-03-30-266.yaml`
- `git restore scripts/dev/frontend_dev_reset.sh`

## Next Suggestion
- Keep using the Makefile-driven frontend runtime path so subsequent startup issues can be distinguished from application bugs.
