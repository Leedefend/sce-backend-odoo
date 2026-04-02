# ITER-2026-04-02-853

- status: FAIL
- mode: verify
- layer_target: Cross-Stack Usability
- module: custom frontend project dashboard primary entry browser smoke
- risk: low

## Verification Result

- `make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: FAIL
- fail reason: login page navigation timeout (`page.goto ... /login?db=sc_demo`)

## Decision

- FAIL
- stop condition triggered (`acceptance_failed`).

## Next Iteration Suggestion

- stabilize smoke login wait strategy and re-run; if host-network remains blocked, switch to container cross-stack smoke.

