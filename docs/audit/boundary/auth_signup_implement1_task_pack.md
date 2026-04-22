# auth_signup Implement-1 Task Pack (ITER-2026-04-05-1039)

## Fixed Target Owner Path

- target controller file (fixed): `addons/smart_core/controllers/platform_auth_signup_web.py`
- target module export file: `addons/smart_core/controllers/__init__.py`
- source handoff files:
  - `addons/smart_construction_core/controllers/auth_signup.py`
  - `addons/smart_construction_core/controllers/__init__.py`

Reason: keep ownership in platform-side module namespace while preserving website/auth route semantics outside `/api/*` chain.

## Implement-1 Allowed Write Scope

1. `addons/smart_core/controllers/platform_auth_signup_web.py` (new)
2. `addons/smart_core/controllers/__init__.py`
3. `addons/smart_construction_core/controllers/auth_signup.py`
4. `addons/smart_construction_core/controllers/__init__.py`
5. task/report/state/log artifacts only

## Implement-1 Required Acceptance Commands

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/<IMPLEMENT1_TASK>.yaml`
2. `python3 -m py_compile addons/smart_core/controllers/platform_auth_signup_web.py addons/smart_construction_core/controllers/auth_signup.py addons/smart_core/controllers/__init__.py addons/smart_construction_core/controllers/__init__.py`
3. `FRONTEND_API_BASE_URL=http://127.0.0.1:18069 ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim make verify.frontend_api`
4. `E2E_BASE_URL=http://127.0.0.1:18069 python3 scripts/verify/scene_legacy_auth_smoke.py`

## Compatibility Gates (Must Pass)

- `/web/signup` remains reachable.
- `/sc/auth/activate/<string:token>` route signature unchanged.
- source module does not retain competing active ownership after handoff (or explicit delegation-only mode documented).

## Stop Conditions (Implement-1)

- any requirement to modify `security/**`, `record_rules/**`, `ir.model.access.csv`, `__manifest__.py`.
- unresolved duplicate-route ownership after change.
- smoke command failure without deterministic low-risk fix.

## Rollback Anchors

- `git restore addons/smart_core/controllers/platform_auth_signup_web.py`
- `git restore addons/smart_core/controllers/__init__.py`
- `git restore addons/smart_construction_core/controllers/auth_signup.py`
- `git restore addons/smart_construction_core/controllers/__init__.py`
