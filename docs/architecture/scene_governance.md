# Scene Governance

## Purpose
This document explains the governance model for menu → scene → target and the guardrails
that keep navigation stable over time.

## Why Menu → Scene
- Menus are presentation; scenes are product behavior.
- Scene routing provides a stable contract across UI planes and channels.
- act_url remains transitional and is progressively retired.

## act_url Governance
- act_url is treated as legacy.
- Missing scene mappings emit warnings and can be blocked by guards.
- Legacy count is capped by a baseline threshold (`SC_WARN_ACT_URL_LEGACY_MAX`).

## Warnings and Guards
- `ACT_URL_MISSING_SCENE`: act_url menu missing a scene mapping.
- `ACT_URL_LEGACY`: legacy act_url count for the current contract.
- `SCENEKEY_INFERRED_NOT_FOUND`: inferred scene_key not in registry.

Guards are enforced in `gate.full` by default. Use `SC_GATE_STRICT=0` to skip
Phase 9.8 guards when running in non-container environments.

## Exemptions
Some menus should not be enforced (system or third-party menus). Exemptions live in:
- `docs/ops/verify/menu_scene_exemptions.yml`

Exempted menus are counted separately and do not fail coverage.

## Operational Notes
- Canonical UI smoke user is `svc_e2e_smoke`.
- Demo user `demo_pm` is reserved for manual walkthroughs and demos.
