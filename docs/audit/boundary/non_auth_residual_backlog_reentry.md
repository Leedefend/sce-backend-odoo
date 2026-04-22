# Non-Auth Residual Backlog Re-entry (ITER-2026-04-05-1049)

## Current Active Residual (Non-Auth)

Based on current controller load surface:

- `addons/smart_construction_core/controllers/__init__.py` only imports:
  - `auth_signup`
  - `meta_controller`

After excluding auth line, the active non-auth residual endpoint is:

1. `/api/meta/project_capabilities`
   - file: `addons/smart_construction_core/controllers/meta_controller.py`
   - classification: scenario business-fact capability descriptor
   - risk: `P2`
   - note: previously marked as intentional retain endpoint.

## Non-Auth Dormant Surfaces (Backlog Candidates)

These endpoints exist historically but are no longer active owner under current import surface:

- scene template pair (`/api/scenes/export`, `/api/scenes/import`) in industry module file
- legacy controller files replaced by smart_core route shells (menu/session/execute/ops/packs families)

## Re-entry Priority Suggestion

### Priority A (screen)
- verify whether `/api/meta/project_capabilities` should remain scenario-owned long-term or move behind neutral provider boundary in smart_core.

### Priority B (cleanup)
- bounded hygiene batch for dormant controller files/import references (no behavior change).

### Priority C (deferred high-risk)
- any cross-module ownership relocation that requires manifest updates remains deferred until dedicated authorization line.

## Next Executable Batch

- open a low-risk screen task focused on `/api/meta/project_capabilities` ownership permanence and provider-boundary contract.
