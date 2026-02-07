# Phase 9.8 Gate Evidence

## Scope
- Menu → scene coverage hardening with act_url guardrails.

## What Changed
- Scene key inference now falls back to `action_xmlid` when `action_id` is unavailable.
- act_url missing scene mapping emits `ACT_URL_MISSING_SCENE`.
- Warnings guard enforces:
  - `ACT_URL_MISSING_SCENE` must be 0.
  - `ACT_URL_LEGACY` capped at `SC_WARN_ACT_URL_LEGACY_MAX` (default 3).
- Menu scene resolve smoke emits coverage summary and is appended to gate summary.

## Gate Additions
- `gate.full` includes:
  - `verify.menu.scene_resolve.container`
  - `verify.menu.scene_resolve.summary`
  - `verify.portal.scene_warnings_guard.container`
  - `verify.portal.scene_warnings_limit.container`
  - `verify.portal.act_url_missing_scene_report.container`
  - `verify.phase_9_8.gate_summary`
- Strict toggle:
  - `SC_GATE_STRICT=0` skips Phase 9.8 guards.
  - Default is strict.

## Verification
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.menu.scene_resolve.container`
  - `/mnt/artifacts/codex/portal-menu-scene-resolve/20260207T051349`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_warnings_guard.container`
  - `/mnt/artifacts/codex/portal-scene-warnings/20260207T052709`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_warnings_limit.container`
  - `/mnt/artifacts/codex/portal-scene-warnings/20260207T052724`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.act_url_missing_scene_report.container`
  - `/mnt/artifacts/codex/portal-scene-warnings/20260207T053445`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.phase_9_8.gate_summary`
  - `artifacts/codex/phase-9-8/gate_summary.json`

## Safety / Rollback
- Disable strict guards:
  - `SC_GATE_STRICT=0 make gate.full`
- Adjust act_url legacy baseline:
  - `SC_WARN_ACT_URL_LEGACY_MAX=<n>`
- Warnings:
  - `ACT_URL_MISSING_SCENE`: act_url menu missing scene mapping.
  - `ACT_URL_LEGACY`: legacy act_url count.
  - `SCENEKEY_INFERRED_NOT_FOUND`: inferred scene_key not in registry.

## Known Limitations
- RC smoke user is `demo_pm` (demo data required).
- `svc_e2e_smoke` remains future hardening work.
