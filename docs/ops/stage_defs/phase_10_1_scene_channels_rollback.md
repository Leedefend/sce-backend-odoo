# Phase 10.1 - Scene Release Channels + Rollback

Date: 2026-02-06

## Scope
- Introduce scene channels (`stable`, `beta`, `dev`) and runtime switch.
- Add stable PINNED rollback path.
- Add channel/rollback smoke verifies and gate wiring.

## Channel Export
Export contract per channel:
```
SCENE_CHANNEL=stable DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make scene.contract.export

SCENE_CHANNEL=beta DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make scene.contract.export
```

Output (per channel):
- `docs/contract/exports/scenes/<channel>/LATEST.json`

## PINNED Rollback
Pin stable snapshot:
```
make scene.pin.stable
```

Rollback to PINNED:
```
SCENE_CHANNEL=stable SCENE_USE_PINNED=1 make scene.rollback.stable
```

## system.init Output
New fields:
- `scene_channel`
- `scene_contract_ref`

Diagnostics:
- `rollback_active`
- `rollback_ref`

## Verifies
Channel smoke:
```
SCENE_CHANNEL=stable DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make verify.portal.scene_channel_smoke.container
```

Rollback smoke:
```
SCENE_CHANNEL=stable SCENE_USE_PINNED=1 DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make verify.portal.scene_rollback_smoke.container
```

## Gate
- `verify.portal.ui.v0_8.semantic.container` includes:
  - `verify.portal.scene_channel_smoke.container`
  - `verify.portal.scene_rollback_smoke.container`

## Artifacts
- `artifacts/codex/portal-shell-v10_1/<timestamp>/`
