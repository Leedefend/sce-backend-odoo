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

## Notes

- Behavior intended to remain consistent with r0.1; changes are data relocation and system_init reduction only.
