## Summary
- Harden menu → scene coverage and act_url guardrails (scene_key fallback, diagnostics, and gate enforcement).
- Add auditable warnings summaries and menu resolve coverage output for gate evidence.
- Wire guardrails into `gate.full` for Phase 9.8 enforcement.

## Changes
- Scene key injection now falls back to `action_xmlid` when `action_id` cannot be resolved.
- act_url missing scene mapping emits `ACT_URL_MISSING_SCENE` warning.
- Warnings guard outputs artifacts and enforces:
  - `ACT_URL_MISSING_SCENE` must be 0.
  - `ACT_URL_LEGACY` capped at `SC_WARN_ACT_URL_LEGACY_MAX` (default 3).
- Menu scene resolve smoke produces coverage summary and is appended to gate summary.
- Warning codes added: `ACT_URL_MISSING_SCENE`, `ACT_URL_LEGACY`, `SCENEKEY_INFERRED_NOT_FOUND`.
- Gate strict toggle: `SC_GATE_STRICT=0` skips Phase 9.8 guards.

## Verification
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.menu.scene_resolve.container`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_warnings_guard.container`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_warnings_limit.container`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.act_url_missing_scene_report.container`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.phase_9_8.gate_summary`

## Artifacts
- `/mnt/artifacts/codex/portal-menu-scene-resolve/20260207T051349`
- `/mnt/artifacts/codex/portal-scene-warnings/20260207T052709`
- `/mnt/artifacts/codex/portal-scene-warnings/20260207T052724`
- `/mnt/artifacts/codex/portal-scene-warnings/20260207T053445`
- `artifacts/codex/phase-9-8/gate_summary.json`
