# Project Dashboard Entry Bootstrap Recovery CC

## Goal

Keep the project dashboard primary-entry smoke on the verification surface when
the current dev runtime proves login reachability before semantic-entry
reachability.

## Planned Change

1. Reuse the preflight-proven login/bootstrap URL as a bounded fallback
   candidate when backend semantic entry is unavailable.
2. Avoid re-navigating back to a login URL after form login succeeds.
3. Re-run the host smoke and distinguish verifier-bootstrap failure from real
   dashboard semantic failure.

## Checkpoint Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-VERIFY-PROJECT-DASHBOARD-ENTRY-BOOTSTRAP-RECOVERY-CC.yaml`: PASS
- `git diff --check -- ...`: PASS
- `make verify.portal.project_dashboard_primary_entry_browser_smoke.host ...`:
  conditional / not converged in bounded time
  - intermediate artifact `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T054133Z/summary.json`
    still showed semantic-entry failure, but no longer the original
    `ERR_CONNECTION_REFUSED` burst as the only stable signal
  - later runtime observation showed the verifier process holding a stable TCP
    connection to `localhost:5174`, yet the fresh run under
    `20260420T055002Z/` did not emit `summary.json` before timeout/termination

## Current Decision

The verifier bootstrap fallback moved the failure frontier forward, but the
acceptance gate still did not converge to a clean PASS/FAIL verdict in bounded
time. The next step must isolate the remaining in-browser wait condition before
claiming the host smoke is repaired.
