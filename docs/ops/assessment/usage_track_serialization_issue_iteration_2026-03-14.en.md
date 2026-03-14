# Iteration Issue Log: `usage.track` Serialization Conflict (2026-03-14)

Date: 2026-03-14  
Branch: `feat/fix-my-work-scene-target`

## Symptom

- Frontend shows a single `500` on `POST /api/v1/intent?db=sc_prod_sim`.
- In the same request window, `login`, `app.init`, `api.data`, and `my.work.summary` are mostly successful.
- The failure is intermittent and short-lived; core page flow usually continues.

## Root Cause

- Backend logs confirm a PostgreSQL transaction serialization conflict:
  - `psycopg2.errors.SerializationFailure`
  - `could not serialize access due to concurrent update`
- Conflict target: `sc_usage_counter` (telemetry usage counter table).
- Trigger chain: `intent=usage.track` -> `smart_construction_core.handlers.usage_track` -> `sc.usage.counter.bump`.

## Mitigation Implemented In This Iteration

- Switched `sc.usage.counter.bump` to atomic `UPSERT` (`INSERT ... ON CONFLICT DO UPDATE value=value+delta`).
- Added bounded retry and graceful degradation for `SerializationFailure(40001)` to avoid bubbling to API `500`.
- Added handler-side guard so a single counter write failure does not break core business response.
- Added concurrency regression smoke and Make target:
  - `scripts/verify/fe_usage_track_concurrency_smoke.js`
  - `make verify.portal.usage_track_concurrency_smoke.container`

## Current Status

- User-facing behavior: this conflict no longer surfaces as `intent dispatcher failed` 500 in current verification window.
- DB-layer `could not serialize access` noise may still appear in logs (now downgraded/handled).
- Conclusion: issue is mitigated, but the hot-path counter write still needs architectural optimization.

## Follow-up Backlog

- Move `usage.track` writes to async/queued pipeline to reduce transaction contention.
- Add aggregation/batching for hot keys (for example `usage.scene_open.role.admin.*`).
- Add observability metrics:
  - retry count
  - degraded/skipped count
  - optional lost-count estimate
- Run concurrency smoke in CI/nightly as a regression gate.

