# Residual Route Ownership Checkpoint

- checkpoint batch: `ITER-2026-04-05-1027`
- scope: `addons/smart_construction_core/controllers/*.py`

## Active Residual Routes (module still imported)

1. `/api/meta/project_capabilities`
   - file: `addons/smart_construction_core/controllers/meta_controller.py`
   - reason: scenario business-fact endpoint kept intentionally per provider-boundary decision.

2. `/api/scenes/export`
   - file: `addons/smart_construction_core/controllers/scene_template_controller.py`
   - reason: scene-template governance surface; not in migrated low-risk chain yet.

3. `/api/scenes/import`
   - file: `addons/smart_construction_core/controllers/scene_template_controller.py`
   - reason: scene-template governance surface; write path requires dedicated bounded batch.

4. `/web/signup`
   - file: `addons/smart_construction_core/controllers/auth_signup.py`
   - reason: website/auth entry outside current API-boundary remediation scope.

5. `/sc/auth/activate/<string:token>`
   - file: `addons/smart_construction_core/controllers/auth_signup.py`
   - reason: auth activation entry outside current API-boundary remediation scope.

## Dormant Route Definitions (file exists but not imported in controller `__init__`)

1. `/api/execute_button` → `execute_controller.py`
2. `/api/menu/tree`, `/api/user_menus` → `frontend_api.py`
3. `/api/contract/portal_execute_button`, `/api/portal/execute_button` → `portal_execute_button_controller.py`
4. `/api/ui/contract` → `ui_contract_controller.py`

These are no longer active route owners under current module loading and have
already been replaced by smart_core route shells.

## Next Suggested Slice

- optional cleanup screen: remove dormant controller imports/files in a separate non-functional hygiene batch.
- functional remediation next: decide dedicated batch for `scene_template` and `auth_signup` families if in scope.
