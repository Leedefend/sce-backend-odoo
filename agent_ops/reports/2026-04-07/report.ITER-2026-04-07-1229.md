# ITER-2026-04-07-1229 Report

## Summary of change
- Ran host-approved non-sandbox live probes to classify corrected native endpoint and legacy endpoint behavior.
- Confirmed both endpoints are live and return unauthenticated business-safe responses (401), not transport failures.

## Changed files
- `agent_ops/tasks/ITER-2026-04-07-1229.yaml`
- `agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1229.md`
- `agent_ops/state/task_results/ITER-2026-04-07-1229.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1229.yaml`
- PASS: `python3 scripts/verify/scene_legacy_auth_smoke_semantic_verify.py`
- PASS (host-approved probe):
  - `POST http://localhost:8069/api/v1/intent` -> `401 AUTH_REQUIRED`
  - `GET http://localhost:8069/api/scenes/my` -> `401 AUTH_REQUIRED`

## Live classification evidence
- Native endpoint (`/api/v1/intent`):
  - `HTTP/1.0 401 UNAUTHORIZED`
  - envelope contains `error.code=AUTH_REQUIRED`
  - includes CORS headers and trace metadata
- Legacy endpoint (`/api/scenes/my`):
  - `HTTP/1.0 401 UNAUTHORIZED`
  - deprecation headers present:
    - `Deprecation: true`
    - `Sunset: Thu, 30 Apr 2026 00:00:00 GMT`
    - `X-Legacy-Endpoint: scenes.my`
    - `Link: </api/v1/intent>; rel="successor-version"`

## Risk analysis
- Low risk, evidence-only governance batch.
- No addon/frontend/security/manifest edits.
- Previous runtime-blocker classified as environment/sandbox visibility issue, not endpoint URL mismatch.

## Rollback suggestion
- `git restore agent_ops/tasks/ITER-2026-04-07-1229.yaml`
- `git restore agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1229.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-07-1229.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- Continue business-fact-layer usability lane with confidence that native and legacy auth entry semantics are reachable and correctly gated at runtime.
