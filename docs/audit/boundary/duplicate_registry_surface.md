# Duplicate Registry Surface (Phase G-3 / Scan)

- Stage: `scan` (fact-only; registry surface co-location evidence)
- Scope: core_extension/capability_registry + smart_core + smart_construction_scene

- candidate_registry_keys: `51`
- duplicate_keys_across_modules: `5`

App shell registry surfaces are closed: `app.catalog`, `app.nav`, and
`app.open` are owned by `smart_core.handlers.app_shell`, and construction no
longer contributes these registry entries.

| Registry Surface Key | Module Count | Evidence Count | Modules |
|---|---|---|---|
| `surface:scene_registry` | `3` | `35` | `smart_construction_core, smart_construction_scene, smart_core` |
| `surface:load_scene_configs` | `3` | `19` | `smart_construction_core, smart_construction_scene, smart_core` |
| `surface:capability_registry` | `3` | `7` | `smart_construction_core, smart_construction_scene, smart_core` |
| `surface:CAPABILITY_GROUPS` | `2` | `12` | `smart_construction_core, smart_core` |
| `surface:list_capabilities_for_user` | `2` | `7` | `smart_construction_core, smart_core` |

## Evidence Samples

- `surface:scene_registry`
  - `smart_construction_core` `addons/smart_construction_core/core_extension.py:507` → `from odoo.addons.smart_construction_scene.scene_registry import load_scene_configs`
  - `smart_construction_core` `addons/smart_construction_core/services/capability_registry.py:8` → `from odoo.addons.smart_construction_scene import scene_registry`
  - `smart_construction_scene` `addons/smart_construction_scene/__init__.py:2` → `from . import scene_registry  # noqa: F401`
  - `smart_construction_scene` `addons/smart_construction_scene/scene_registry.py:16` → `def _load_scene_registry_engine_module():`
- `surface:load_scene_configs`
  - `smart_construction_core` `addons/smart_construction_core/core_extension.py:505` → `def smart_core_load_scene_configs(env, *, drift=None):`
  - `smart_construction_core` `addons/smart_construction_core/services/capability_registry.py:351` → `for row in (scene_registry.load_scene_configs(env) or [])`
  - `smart_construction_scene` `addons/smart_construction_scene/scene_registry.py:284` → `def load_scene_configs(env, drift=None):`
  - `smart_construction_scene` `addons/smart_construction_scene/services/scene_package_service.py:400` → `existing = scene_registry.load_scene_configs(self.env)`
- `surface:capability_registry`
  - `smart_construction_core` `addons/smart_construction_core/core_extension.py:466` → `from odoo.addons.smart_construction_core.services.capability_registry import (`
  - `smart_construction_core` `addons/smart_construction_core/services/capability_registry.py:363` → `def capability_registry_summary(env, user) -> dict[str, Any]:`
  - `smart_construction_scene` `addons/smart_construction_scene/profiles/workspace_home_scene_content.py:556` → `"source_type": "capability_registry",`
  - `smart_core` `addons/smart_core/core/workspace_home_provider_defaults.py:43` → `"ds_capability_groups": {"source_type": "capability_registry", "provider": "workspace.capability.groups", "section_keys": ["group_overview"]},`
- `surface:CAPABILITY_GROUPS`
  - `smart_construction_core` `addons/smart_construction_core/core_extension.py:481` → `from odoo.addons.smart_construction_core.services.capability_registry import CAPABILITY_GROUPS`
  - `smart_construction_core` `addons/smart_construction_core/services/capability_registry.py:17` → `CAPABILITY_GROUPS: list[dict[str, Any]] = [`
  - `smart_core` `addons/smart_core/core/capability_provider.py:8` → `DEFAULT_CAPABILITY_GROUPS,`
  - `smart_core` `addons/smart_core/core/capability_group_defaults.py:7` → `DEFAULT_CAPABILITY_GROUPS = [`
- `surface:list_capabilities_for_user`
  - `smart_construction_core` `addons/smart_construction_core/core_extension.py:464` → `def smart_core_list_capabilities_for_user(env, user):`
  - `smart_construction_core` `addons/smart_construction_core/services/capability_registry.py:228` → `def list_capabilities_for_user(env, user) -> list[dict[str, Any]]:`
  - `smart_core` `addons/smart_core/core/capability_provider.py:82` → `extension_caps = call_extension_hook_first(env, "smart_core_list_capabilities_for_user", env, user)`

## Scan Notes

- Duplicate here means same registry-surface key appears in two or more module families.
- Ownership finalization and conflict severity remain for subsequent screen/governance synthesis stage.
