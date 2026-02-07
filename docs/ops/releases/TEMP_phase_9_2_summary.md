# TEMP Phase 9.2 Summary

Date: 2026-02-07
Branch: `codex/phase-9-2-scene-data`

## Scope
- Scene orchestration data split (layout/tiles/list_profile)
- system_init reduced to validation/target resolve only
- scene_registry trimmed to targets/fallback only
- New audit hook for scene config source

## Key Changes

1. Data source split
- `addons/smart_construction_scene/data/sc_scene_orchestration.xml` now base scene records only
- New files:
  - `addons/smart_construction_scene/data/sc_scene_layout.xml`
  - `addons/smart_construction_scene/data/sc_scene_tiles.xml`
  - `addons/smart_construction_scene/data/sc_scene_list_profile.xml`

2. system_init reduction
- `addons/smart_core/handlers/system_init.py`
  - no longer applies layout defaults; only validates presence

3. scene_registry reduction
- `addons/smart_construction_scene/scene_registry.py`
  - removed layout/tiles/list_profile defaults
  - fallback contains targets only

4. Audit hook
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

## Commits
- `9922394` feat(scene): split layout/tiles/list_profile data
- `1ee587e` docs(phase9.2): record audit progress
- `f37b60f` docs(phase9.2): add closure checklist
- `7adc16a` docs(phase9.2): record contract smoke
- `9f1e6d9` docs(phase9.2): record scene smokes

## Closure Checklist
- [x] scene_registry no longer provides layout/tiles/list_profile defaults
- [x] system_init no longer applies layout defaults
- [x] scene config split into layout/tiles/list_profile data files
- [x] scene config audit hook in Makefile
- [x] scene resolve/contract smokes pass
