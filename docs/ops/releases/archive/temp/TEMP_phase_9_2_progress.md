# TEMP Phase 9.2 Progress

Date: 2026-02-07
Branch: `codex/phase-9-2-scene-data`

## Completed

1. Scene config sources split (layout / tiles / list_profile)
- `addons/smart_construction_scene/data/sc_scene_layout.xml`
- `addons/smart_construction_scene/data/sc_scene_tiles.xml`
- `addons/smart_construction_scene/data/sc_scene_list_profile.xml`
- `addons/smart_construction_scene/data/sc_scene_orchestration.xml` now base records only

2. system_init reduction
- `addons/smart_core/handlers/system_init.py` no longer applies layout defaults

3. scene_registry responsibility trimmed
- `addons/smart_construction_scene/scene_registry.py` no longer provides layout/tiles/list_profile defaults

4. Scene config audit hook
- `scripts/audit/scene_config_audit.js`
- `make audit.scene.config`

## Verification

- `make audit.scene.config`: PASS
  - artifacts: `/mnt/artifacts/audit/scene-config/20260207T040903`
- `E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_contract_smoke.container`: PASS
  - artifacts: `/mnt/artifacts/codex/portal-shell-v0_8-6/20260207T041133`
- `E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_targets_resolve_smoke.container`: PASS
  - artifacts: `/mnt/artifacts/codex/portal-shell-v0_9-7/20260207T041230`
- `E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_layout_contract_smoke.container`: PASS
  - artifacts: `/mnt/artifacts/codex/portal-shell-v0_9-1-1/20260207T041245`
- `E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_semantic_smoke.container`: PASS
  - artifacts: `/mnt/artifacts/codex/portal-shell-v0_9-6/20260207T041259`

## Notes

- Behavior intended to remain consistent with r0.1; changes are data relocation and system_init reduction only.

## Phase 9.2 Closure Checklist (Draft)

- [x] scene_registry no longer provides layout/tiles/list_profile defaults
- [x] system_init no longer applies layout defaults
- [x] scene config split into layout/tiles/list_profile data files
- [x] scene config audit hook in Makefile
- [x] verify scene resolve/contract smokes (contract/targets/layout/semantic passed)
