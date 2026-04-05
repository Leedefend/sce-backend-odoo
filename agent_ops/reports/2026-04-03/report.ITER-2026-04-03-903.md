# ITER-2026-04-03-903

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: host runtime probe chained stability
- risk: low
- publishability: not_publishable

## Summary of Change

- created:
  - `agent_ops/tasks/ITER-2026-04-03-903.yaml`
- updated:
  - `scripts/verify/host_browser_runtime_probe.mjs`
- stability hardening:
  - added launch profile sequence for deterministic fallback order:
    - `default` (3 attempts)
    - `full_chrome_fallback` (2 attempts, gated by error signature)
    - `default_retry_tail` (1 attempt)
  - added launch args to reduce crash reporting path impact:
    - `--disable-crash-reporter`
    - `--disable-crashpad-for-testing`
  - probe summary now records `launch_attempts`

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-903.yaml`: PASS
- `make verify.portal.host_browser_runtime_probe`: PASS
  - `artifacts/codex/host-browser-runtime-probe/20260404T024542Z`
- `GATEWAY_BASE_URLS=http://localhost:8069 make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: FAIL
  - nested `verify.portal.host_browser_runtime_probe` fails
  - fatal: `sandbox_host_linux.cc` `Operation not permitted`
  - artifact: `artifacts/codex/host-browser-runtime-probe/20260404T024605Z`

## Key Evidence

- PASS probe artifact:
  - `artifacts/codex/host-browser-runtime-probe/20260404T024542Z/summary.json`
- FAIL probe artifact:
  - `artifacts/codex/host-browser-runtime-probe/20260404T024605Z/summary.json`
- signal:
  - runtime probe remains non-deterministic across chained execution context
  - host-level permission failure persists despite fallback reorder

## Risk Analysis

- code risk remains low:
  - change confined to probe launch orchestration
- runtime risk remains high:
  - same host permission fatal still appears under nested execution, blocking explicit-gateway chain
- publishability remains `not_publishable`

## Rollback Suggestion

- `git restore scripts/verify/host_browser_runtime_probe.mjs`
- `git restore agent_ops/tasks/ITER-2026-04-03-903.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-903.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-903.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `not_publishable`

## Next Iteration Suggestion

- open dedicated make-chain isolation batch:
  - split nested probe invocation from host gate or reuse prior PASS probe result token
  - avoid re-launching browser probe in same chained make path
