# Smart Core Stabilize M0

## Scope
- controllers/ (intent + contract entrypoints)
- core/ (router, registry, exceptions)
- security/ (JWT auth)
- tests/ (smart_core smoke coverage)
- docs/ (this plan + references)

Out of scope:
- models/ (business models and data)
- functional business logic beyond stability fixes

## Risks
- HTTP route change could impact clients if they relied on the duplicate v1 endpoint behavior.
- JWT expiration changes could affect long-lived sessions if clients do not refresh.
- Test additions may reveal hidden regressions in CI or staging.

## Acceptance Checklist
- /api/v1/intent has exactly one controller, consistently hit after restart.
- v1 intent smoke tests pass (anon login + system.init).
- /api/v2/intent returns HTTP 501 with JSON envelope (no 500).
- No ImportError/ModuleNotFoundError in smart_core tests.
- JWT secret is configurable, tokens include iat/exp, expired tokens are rejected.

## Behavior Change Notice
- `/api/v1/intent` is the single stable entrypoint.
- `/api/v1/intent_enhanced` is experimental and not guaranteed stable.
- `/api/v2/intent` returns HTTP 501 with a JSON envelope (explicitly disabled).
- JWT config:
  - Secret priority: `SC_JWT_SECRET` / `JWT_SECRET` → `ir.config_parameter` `sc.jwt.secret` → default (warn once).
  - Exp seconds: `SC_JWT_EXP_SECONDS` → `ir.config_parameter` `sc.jwt.exp_seconds` → default 8h.
  - Login response includes `expires_at` (epoch seconds).

## Rollback Point
- Baseline commit/tag: 8cdd3edd3f787eeec96ac2082a46c410b7673b40

## Change List (M0)
- Task 2: unify /api/v1/intent entrypoint and add controller identification log.
- Task 3: add v1 intent smoke tests.
- Task 4: disable /api/v2/intent with 501 response.
- Task 5: fix broken imports/tests (enhanced router exceptions, versioned handler, command registry).
- Task 6: configure JWT secret + exp/iat.
