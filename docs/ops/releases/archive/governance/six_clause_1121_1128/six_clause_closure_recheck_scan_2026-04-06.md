# Six-Clause Closure Recheck Scan (2026-04-06)

> Stage: `scan` (low-cost governance)
>
> Scope rule: only collect file-backed evidence candidates; no closure conclusion in this stage.

## Clause-1: 行业模块不再直接写平台注册表

- evidence: `addons/smart_construction_core/core_extension.py:253` defines `get_intent_handler_contributions` provider.
- evidence: `addons/smart_core/core/intent_contribution_loader.py:122` performs final `registry[intent] = handler` in platform loader.
- evidence: `scripts/verify/architecture_intent_registry_single_owner_guard.py:16` guards against `registry[...]` assignment in industry extension.
- scan note: candidate indicates platform final-write path exists with industry provider pattern.

## Clause-2: capability registry 主权回到平台

- evidence: `addons/smart_core/core/capability_contribution_loader.py:36` documents platform-owned collection path.
- evidence: `addons/smart_construction_core/core_extension.py:434` provides `get_capability_contributions`.
- evidence: `addons/smart_construction_core/core_extension.py:464` provides `get_capability_group_contributions`.
- evidence: `addons/smart_core/core/capability_provider.py:90` still calls legacy hook `smart_core_list_capabilities_for_user`.
- evidence: `addons/smart_core/core/capability_provider.py:97` still calls legacy hook `smart_core_capability_groups`.
- scan note: candidate indicates coexistence of new contribution loader and legacy runtime hook path.

## Clause-3: scene 子系统访问不再经过行业桥接

- evidence: `addons/smart_core/core/scene_registry_provider.py:9` imports scene registry directly from `smart_construction_scene` first.
- evidence: `addons/smart_core/core/scene_registry_provider.py:15` fallback still calls `smart_core_load_scene_configs` extension hook.
- evidence: `addons/smart_core/core/scene_registry_provider.py:26` fallback still calls `smart_core_has_db_scenes` extension hook.
- evidence: `addons/smart_core/core/scene_registry_provider.py:39` fallback still calls `smart_core_get_scene_version` extension hook.
- evidence: `addons/smart_core/core/scene_registry_provider.py:53` fallback still calls `smart_core_get_schema_version` extension hook.
- scan note: candidate indicates direct path is present and legacy bridge fallback is still retained.

## Clause-4: 平台规则常量不再由行业模块 owning

- evidence: `addons/smart_core/core/platform_policy_defaults.py:56` still accepts legacy extension hook `smart_core_server_action_window_map`.
- evidence: `addons/smart_core/core/platform_policy_defaults.py:70` still accepts legacy extension hook `smart_core_file_upload_allowed_models`.
- evidence: `addons/smart_core/core/platform_policy_defaults.py:97` still accepts legacy extension hook `smart_core_api_data_write_allowlist`.
- evidence: `addons/smart_core/core/platform_policy_defaults.py:126` (same file) still accepts legacy hook `smart_core_api_data_unlink_allowed_models`.
- evidence: `addons/smart_core/core/platform_policy_defaults.py:139` (same file) still accepts legacy hook `smart_core_model_code_mapping`.
- evidence: `addons/smart_core/core/platform_policy_defaults.py:155` (same file) still accepts legacy hook `smart_core_create_field_fallbacks`.
- scan note: candidate indicates platform defaults owner exists with legacy industry hook compatibility path.

## Clause-5: system.init 扩展改为 contribution protocol

- evidence: `addons/smart_core/core/system_init_extension_fact_merger.py:26` consumes provider `get_system_init_fact_contributions`.
- evidence: `addons/smart_construction_core/core_extension.py:485` provides `get_system_init_fact_contributions`.
- evidence: `addons/smart_core/handlers/system_init.py:538` still runs legacy hook `smart_core_extend_system_init`.
- evidence: `addons/smart_core/core/runtime_fetch_bootstrap_helper.py:25` still runs legacy hook `smart_core_extend_system_init` in runtime fetch helper.
- scan note: candidate indicates contribution protocol is active with legacy extension hook retained.

## Clause-6: workspace 重数据从 startup 主链解耦

- evidence: `addons/smart_core/handlers/system_init.py:539` uses `merge_extension_facts(data, include_workspace_collections=False)`.
- evidence: `addons/smart_core/core/runtime_fetch_bootstrap_helper.py:26` uses `merge_extension_facts_fn(data, include_workspace_collections=True)`.
- evidence: `addons/smart_core/core/system_init_extension_fact_merger.py:64` introduces explicit mode parameter `include_workspace_collections`.
- scan note: candidate indicates startup/runtime merge mode split is explicitly coded.

## Scan Output Constraints

- this file intentionally avoids PASS/FAIL closure judgment.
- screening/classification should be done in a dedicated `screen` stage task.
