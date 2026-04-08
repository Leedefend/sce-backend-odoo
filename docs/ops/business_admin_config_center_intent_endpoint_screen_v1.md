# Business Admin Config Center Intent Endpoint Screen v1

## Screen Objective
- Explain why current runtime checks observe `404` on `/api/v1/intent` and related `/api/*` paths.
- Provide bounded remediation path for restoring intent-envelope verification parity.

## Evidence
- Code-side route exists:
  - `addons/smart_core/controllers/intent_dispatcher.py` defines `@http.route('/api/v1/intent', ...)`.
  - `addons/smart_core/controllers/platform_scenes_api.py` defines `/api/scenes/my`.
- Runtime no-session probe:
  - Direct call to `/api/v1/intent` and `/api/scenes/my` returns `404`.
- Runtime with authenticated DB session probe:
  - After `/web/session/authenticate` (`db=sc_test`), both `/api/scenes/my` and `/api/v1/intent` return `200`.

## Root Cause
- Current runtime stack is in multi-db selector mode (`/web/login` redirects to `/web/database/selector` when no bound db session).
- For requests without established db session context, router path resolution does not expose these custom `/api/*` routes, resulting in `404`.
- This is an access-path/context issue, not a missing controller code issue.

## Remediation Path (bounded)
1. For runtime verify scripts using `/api/v1/intent`, establish db-bound session first:
   - call `/web/session/authenticate` with target `db`.
2. Reuse same cookie jar/session for subsequent `/api/*` calls.
3. Keep explicit `DB_NAME` in verify env and avoid anonymous no-session probes when asserting availability.

## Impact on 1332 Risk
- 1332 `PASS_WITH_RISK` risk item is explained and now has a concrete remediation path.
- Once verify scripts are updated to session-bootstrap flow, intent-envelope runtime parity can be re-evaluated in a dedicated follow-up batch.

## Verdict
- Screen result: `PASS` (root cause identified, bounded remediation defined).
