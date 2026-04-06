# Duplicate Orchestration Surface (Phase G-2 / Scan)

- Stage: `scan` (fact-only; orchestration-surface co-location evidence)
- Scope: handlers/services/orchestration + smart_core + smart_construction_scene

- candidate_keys_scanned: `305`
- duplicate_keys_across_modules: `55`

| Surface Key | Module Count | Evidence Count | Modules |
|---|---|---|---|
| `center` | `3` | `38` | `smart_construction_core, smart_construction_scene, smart_core` |
| `plan_bootstrap` | `3` | `9` | `smart_construction_core, smart_construction_scene, smart_core` |
| `suggested_action` | `2` | `174` | `smart_construction_core, smart_core` |
| `project.initiation.enter` | `2` | `27` | `smart_construction_core, smart_construction_scene` |
| `block.fetch` | `2` | `18` | `smart_construction_core, smart_core` |
| `project.dashboard.enter` | `2` | `13` | `smart_construction_core, smart_construction_scene` |
| `risk_center` | `2` | `12` | `smart_construction_scene, smart_core` |
| `project.execution.enter` | `2` | `10` | `smart_construction_core, smart_construction_scene` |
| `app.open` | `2` | `8` | `smart_construction_core, smart_core` |
| `app.nav` | `2` | `7` | `smart_construction_core, smart_core` |
| `build_runtime_block` | `2` | `7` | `smart_construction_core, smart_core` |
| `risk.center` | `2` | `7` | `smart_construction_scene, smart_core` |
| `sc.scene.rollback` | `2` | `6` | `smart_construction_scene, smart_core` |
| `sc.scene.use_pinned` | `2` | `6` | `smart_construction_scene, smart_core` |
| `task_center` | `2` | `6` | `smart_construction_scene, smart_core` |
| `app.catalog` | `2` | `5` | `smart_construction_core, smart_core` |
| `cost_center` | `2` | `5` | `smart_construction_scene, smart_core` |
| `project.execution.block.fetch` | `2` | `5` | `smart_construction_core, smart_core` |
| `menu_sc_project_center` | `2` | `4` | `smart_construction_scene, smart_core` |
| `project.plan_bootstrap.enter` | `2` | `4` | `smart_construction_core, smart_construction_scene` |
| `action.open_landing.label` | `2` | `3` | `smart_construction_scene, smart_core` |
| `action.open_my_work.label` | `2` | `3` | `smart_construction_scene, smart_core` |
| `action.open_risk_dashboard.label` | `2` | `3` | `smart_construction_scene, smart_core` |
| `action.open_scene.label` | `2` | `3` | `smart_construction_scene, smart_core` |
| `block.entry_grid_scene.title` | `2` | `3` | `smart_construction_scene, smart_core` |
| `capability_suggested_action` | `2` | `3` | `smart_construction_core, smart_core` |
| `cost.tracking.block.fetch` | `2` | `3` | `smart_construction_core, smart_core` |
| `cost_tracking_contract_orchestrator` | `2` | `3` | `smart_construction_core, smart_core` |
| `finance_center` | `2` | `3` | `smart_construction_scene, smart_core` |
| `page.badge.runtime_ok` | `2` | `3` | `smart_construction_scene, smart_core` |
| `payment.block.fetch` | `2` | `3` | `smart_construction_core, smart_core` |
| `project.board.open` | `2` | `3` | `smart_construction_core, smart_construction_scene` |
| `project.dashboard.open` | `2` | `3` | `smart_construction_core, smart_construction_scene` |
| `project_dashboard_scene_orchestrator` | `2` | `3` | `smart_construction_core, smart_core` |
| `project_execution_scene_orchestrator` | `2` | `3` | `smart_construction_core, smart_core` |
| `project_plan_bootstrap_scene_orchestrator` | `2` | `3` | `smart_construction_core, smart_core` |
| `sc.scene.channel.default` | `2` | `3` | `smart_construction_scene, smart_core` |
| `settlement.block.fetch` | `2` | `3` | `smart_construction_core, smart_core` |
| `workspace.scene.groups` | `2` | `3` | `smart_construction_scene, smart_core` |
| `contract.center.open` | `2` | `2` | `smart_construction_core, smart_construction_scene` |
| `cost.ledger.open` | `2` | `2` | `smart_construction_core, smart_construction_scene` |
| `finance.approval.center` | `2` | `2` | `smart_construction_core, smart_construction_scene` |
| `governance.runtime.audit` | `2` | `2` | `smart_construction_core, smart_construction_scene` |
| `governance.scene.openability` | `2` | `2` | `smart_construction_core, smart_construction_scene` |
| `material.catalog.open` | `2` | `2` | `smart_construction_core, smart_construction_scene` |
| `project.dashboard.block.fetch` | `2` | `2` | `smart_construction_core, smart_core` |
| `project.document.open` | `2` | `2` | `smart_construction_core, smart_construction_scene` |
| `project.lifecycle.open` | `2` | `2` | `smart_construction_core, smart_construction_scene` |
| `project.list.open` | `2` | `2` | `smart_construction_core, smart_construction_scene` |
| `project.plan_bootstrap` | `2` | `2` | `smart_construction_scene, smart_core` |
| `project.plan_bootstrap.block.fetch` | `2` | `2` | `smart_construction_core, smart_core` |
| `project.weekly_report.open` | `2` | `2` | `smart_construction_core, smart_construction_scene` |
| `project_dashboard_contract_orchestrator` | `2` | `2` | `smart_construction_core, smart_core` |
| `sc.scene.contract.pinned` | `2` | `2` | `smart_construction_scene, smart_core` |
| `scene.open` | `2` | `2` | `smart_construction_core, smart_construction_scene` |

## Evidence Samples

- `center`
  - `smart_construction_scene` `addons/smart_construction_scene/profiles/workspace_home_scene_content.py:15` → `"risk_center": "risk.center",`
  - `smart_construction_scene` `addons/smart_construction_scene/profiles/scene_registry_content.py:100` → `"code": "task.center",`
  - `smart_construction_scene` `addons/smart_construction_scene/services/capability_scene_targets.py:28` → `"finance.approval.center": "finance.center",`
  - `smart_construction_scene` `addons/smart_construction_scene/core_extension.py:146` → `"contract.center",`
- `plan_bootstrap`
  - `smart_construction_scene` `addons/smart_construction_scene/services/capability_scene_targets.py:15` → `"project.plan_bootstrap.enter": "project.plan_bootstrap",`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py:18` → `INTENT_TYPE = "project.plan_bootstrap.enter"`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_plan_bootstrap_block_fetch.py:14` → `INTENT_TYPE = "project.plan_bootstrap.block.fetch"`
  - `smart_construction_core` `addons/smart_construction_core/services/capability_registry.py:69` → `_cap("project.plan_bootstrap.enter", "计划编排入口", "进入项目计划编排最小入口", "project_management", required_roles=["pm", "executive"]),`
- `suggested_action`
  - `smart_construction_core` `addons/smart_construction_core/handlers/settlement_slice_enter.py:78` → `"suggested_action": "fix_input",`
  - `smart_construction_core` `addons/smart_construction_core/handlers/settlement_slice_block_fetch.py:61` → `"suggested_action": "fix_input",`
  - `smart_construction_core` `addons/smart_construction_core/handlers/reason_codes.py:19` → `capability_suggested_action,`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py:54` → `"suggested_action_intent": "project.initiation.enter",`
- `project.initiation.enter`
  - `smart_construction_scene` `addons/smart_construction_scene/services/capability_scene_targets.py:10` → `"project.initiation.enter": "project.initiation",`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py:54` → `"suggested_action_intent": "project.initiation.enter",`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_plan_bootstrap_block_fetch.py:57` → `"suggested_action_intent": "project.initiation.enter",`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_initiation_enter.py:16` → `INTENT_TYPE = "project.initiation.enter"`
- `block.fetch`
  - `smart_construction_core` `addons/smart_construction_core/services/settlement_slice_builders/settlement_slice_next_actions_builder.py:31` → `intent="settlement.block.fetch",`
  - `smart_construction_core` `addons/smart_construction_core/handlers/settlement_slice_block_fetch.py:17` → `INTENT_TYPE = "settlement.block.fetch"`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_plan_bootstrap_block_fetch.py:14` → `INTENT_TYPE = "project.plan_bootstrap.block.fetch"`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_execution_block_fetch.py:17` → `INTENT_TYPE = "project.execution.block.fetch"`
- `project.dashboard.enter`
  - `smart_construction_scene` `addons/smart_construction_scene/services/capability_scene_targets.py:13` → `"project.dashboard.enter": "project.dashboard",`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_initiation_enter.py:182` → `"intent": "project.dashboard.enter",`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_dashboard_open.py:56` → `"deprecated_replacement_intent": "project.dashboard.enter",`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_dashboard_enter.py:21` → `INTENT_TYPE = "project.dashboard.enter"`
- `risk_center`
  - `smart_core` `addons/smart_core/core/workspace_home_source_routing_helper.py:116` → `return workspace_scene_resolver("risk_center")`
  - `smart_core` `addons/smart_core/core/workspace_home_shell_helper.py:14` → `"risk_center": "workspace.risk",`
  - `smart_core` `addons/smart_core/tests/test_workspace_home_source_routing_helper.py:40` → `"risk_center": "workspace.risk",`
  - `smart_core` `addons/smart_core/tests/test_workspace_home_shell_helper.py:40` → `self.assertEqual(aliases["risk_center"], "workspace.risk")`
- `project.execution.enter`
  - `smart_construction_core` `addons/smart_construction_core/services/project_risk_alert_service.py:71` → `"action": primary_action if primary_action == "project_execution_enter" else "project.execution.enter",`
  - `smart_construction_scene` `addons/smart_construction_scene/services/capability_scene_targets.py:16` → `"project.execution.enter": "project.execution",`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_execution_enter.py:21` → `INTENT_TYPE = "project.execution.enter"`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_execution_block_fetch.py:53` → `"suggested_action_intent": "project.execution.enter",`
- `app.open`
  - `smart_core` `addons/smart_core/handlers/system_init.py:343` → `"app.open",`
  - `smart_core` `addons/smart_core/handlers/app_shell.py:132` → `INTENT_TYPE = "app.open"`
  - `smart_construction_core` `addons/smart_construction_core/handlers/app_open.py:43` → `_logger.info("[app.open] feature not openable app=%s feature=%s", app_id, feature.get("key"))`
- `app.nav`
  - `smart_core` `addons/smart_core/handlers/system_init.py:342` → `"app.nav",`
  - `smart_core` `addons/smart_core/handlers/app_shell.py:90` → `INTENT_TYPE = "app.nav"`
  - `smart_construction_core` `addons/smart_construction_core/handlers/app_nav.py:33` → `意图：app.nav`
- `build_runtime_block`
  - `smart_construction_core` `addons/smart_construction_core/handlers/settlement_slice_block_fetch.py:71` → `data = orchestrator.build_runtime_block(block_key=block_key, project_id=project_id, context=ctx)`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_plan_bootstrap_block_fetch.py:89` → `data = orchestrator.build_runtime_block(block_key=block_key, project_id=project_id, context=ctx)`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_execution_block_fetch.py:92` → `data = orchestrator.build_runtime_block(block_key=block_key, project_id=project_id, context=ctx)`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_dashboard_block_fetch.py:92` → `data = orchestrator.build_runtime_block(block_key=block_key, project_id=project_id, context=ctx)`
- `risk.center`
  - `smart_construction_scene` `addons/smart_construction_scene/profiles/workspace_home_scene_content.py:15` → `"risk_center": "risk.center",`
  - `smart_construction_scene` `addons/smart_construction_scene/profiles/scene_registry_content.py:139` → `"code": "risk.center",`
  - `smart_core` `addons/smart_core/tests/test_scene_runtime_contract_chain.py:192` → `"code": "risk.center",`
- `sc.scene.rollback`
  - `smart_construction_scene` `addons/smart_construction_scene/services/scene_package_service.py:359` → `"rollback_active": str(self._config().get_param("sc.scene.rollback") or "0").strip().lower() in {"1", "true", "yes", "on"},`
  - `smart_construction_scene` `addons/smart_construction_scene/services/scene_governance_service.py:68` → `rollback_before = str(config.get_param("sc.scene.rollback") or "")`
  - `smart_core` `addons/smart_core/core/scene_channel_policy.py:21` → `is_truthy(config.get_param("sc.scene.rollback"))`
- `sc.scene.use_pinned`
  - `smart_construction_scene` `addons/smart_construction_scene/services/scene_package_service.py:360` → `"use_pinned": str(self._config().get_param("sc.scene.use_pinned") or "0").strip().lower() in {"1", "true", "yes", "on"},`
  - `smart_construction_scene` `addons/smart_construction_scene/services/scene_governance_service.py:69` → `pinned_before = str(config.get_param("sc.scene.use_pinned") or "")`
  - `smart_core` `addons/smart_core/core/scene_channel_policy.py:20` → `rollback_active = rollback_active or is_truthy(config.get_param("sc.scene.use_pinned")) or \`
- `task_center`
  - `smart_core` `addons/smart_core/core/workspace_home_source_routing_helper.py:118` → `return workspace_scene_resolver("task_center")`
  - `smart_core` `addons/smart_core/core/workspace_home_shell_helper.py:15` → `"task_center": "workspace.tasks",`
  - `smart_core` `addons/smart_core/tests/test_workspace_home_source_routing_helper.py:41` → `"task_center": "workspace.tasks",`
  - `smart_construction_scene` `addons/smart_construction_scene/profiles/workspace_home_scene_content.py:16` → `"task_center": "task.center",`
- `app.catalog`
  - `smart_core` `addons/smart_core/handlers/app_shell.py:53` → `INTENT_TYPE = "app.catalog"`
  - `smart_construction_core` `addons/smart_construction_core/handlers/app_catalog.py:145` → `意图：app.catalog`
- `cost_center`
  - `smart_core` `addons/smart_core/core/workspace_home_source_routing_helper.py:120` → `return workspace_scene_resolver("cost_center")`
  - `smart_core` `addons/smart_core/core/workspace_home_shell_helper.py:16` → `"cost_center": "workspace.cost",`
  - `smart_core` `addons/smart_core/tests/test_workspace_home_source_routing_helper.py:42` → `"cost_center": "workspace.cost",`
  - `smart_construction_scene` `addons/smart_construction_scene/profiles/workspace_home_scene_content.py:17` → `"cost_center": "cost.project_boq",`
- `project.execution.block.fetch`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_execution_block_fetch.py:17` → `INTENT_TYPE = "project.execution.block.fetch"`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_execution_advance.py:99` → `"intent": "project.execution.block.fetch",`
  - `smart_construction_core` `addons/smart_construction_core/services/project_execution_hint_service.py:10` → `"intent": "project.execution.block.fetch",`
  - `smart_core` `addons/smart_core/orchestration/project_execution_scene_orchestrator.py:19` → `block_fetch_intent = "project.execution.block.fetch"`
- `menu_sc_project_center`
  - `smart_construction_scene` `addons/smart_construction_scene/core_extension.py:10` → `"smart_construction_core.menu_sc_project_center",`
  - `smart_core` `addons/smart_core/tests/test_delivery_menu_service_native_preview.py:98` → `"meta": {"scene_key": "projects.intake", "menu_xmlid": "smart_construction_core.menu_sc_project_center", "scene_source": "native_nav", "action_id": 501, "route": "/s/projects.intake"},`
- `project.plan_bootstrap.enter`
  - `smart_construction_scene` `addons/smart_construction_scene/services/capability_scene_targets.py:15` → `"project.plan_bootstrap.enter": "project.plan_bootstrap",`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_plan_bootstrap_enter.py:18` → `INTENT_TYPE = "project.plan_bootstrap.enter"`
  - `smart_construction_core` `addons/smart_construction_core/handlers/project_plan_bootstrap_block_fetch.py:50` → `"suggested_action_intent": "project.plan_bootstrap.enter",`
  - `smart_construction_core` `addons/smart_construction_core/services/capability_registry.py:69` → `_cap("project.plan_bootstrap.enter", "计划编排入口", "进入项目计划编排最小入口", "project_management", required_roles=["pm", "executive"]),`
- `action.open_landing.label`
  - `smart_construction_scene` `addons/smart_construction_scene/profiles/workspace_home_scene_content.py:515` → `"action.open_landing.label": "打开默认入口",`
  - `smart_core` `addons/smart_core/core/workspace_home_contract_builder.py:1412` → `"action.open_landing.label": "打开默认入口",`
- `action.open_my_work.label`
  - `smart_construction_scene` `addons/smart_construction_scene/profiles/workspace_home_scene_content.py:516` → `"action.open_my_work.label": "查看全部",`
  - `smart_core` `addons/smart_core/core/workspace_home_contract_builder.py:1413` → `"action.open_my_work.label": "查看全部",`
- `action.open_risk_dashboard.label`
  - `smart_construction_scene` `addons/smart_construction_scene/profiles/workspace_home_scene_content.py:517` → `"action.open_risk_dashboard.label": "进入风险驾驶舱",`
  - `smart_core` `addons/smart_core/core/workspace_home_contract_builder.py:1414` → `"action.open_risk_dashboard.label": "进入风险驾驶舱",`
- `action.open_scene.label`
  - `smart_construction_scene` `addons/smart_construction_scene/profiles/workspace_home_scene_content.py:518` → `"action.open_scene.label": "进入场景",`
  - `smart_core` `addons/smart_core/core/workspace_home_contract_builder.py:1415` → `"action.open_scene.label": "进入场景",`
- `block.entry_grid_scene.title`
  - `smart_construction_scene` `addons/smart_construction_scene/profiles/workspace_home_scene_content.py:514` → `"block.entry_grid_scene.title": "常用功能",`
  - `smart_core` `addons/smart_core/core/workspace_home_contract_builder.py:1411` → `"block.entry_grid_scene.title": "常用功能",`
- `capability_suggested_action`
  - `smart_construction_core` `addons/smart_construction_core/handlers/reason_codes.py:19` → `capability_suggested_action,`
  - `smart_core` `addons/smart_core/utils/reason_codes.py:161` → `def capability_suggested_action(*, reason_code: str, state: str) -> str:`
- `cost.tracking.block.fetch`
  - `smart_construction_core` `addons/smart_construction_core/handlers/cost_tracking_block_fetch.py:17` → `INTENT_TYPE = "cost.tracking.block.fetch"`
  - `smart_core` `addons/smart_core/orchestration/cost_tracking_contract_orchestrator.py:15` → `block_fetch_intent = "cost.tracking.block.fetch"`
  - `smart_construction_core` `addons/smart_construction_core/services/cost_tracking_builders/cost_tracking_next_actions_builder.py:33` → `intent="cost.tracking.block.fetch",`
- `cost_tracking_contract_orchestrator`
  - `smart_construction_core` `addons/smart_construction_core/handlers/cost_tracking_enter.py:12` → `from odoo.addons.smart_core.orchestration.cost_tracking_contract_orchestrator import (`
  - `smart_construction_core` `addons/smart_construction_core/handlers/cost_tracking_block_fetch.py:11` → `from odoo.addons.smart_core.orchestration.cost_tracking_contract_orchestrator import (`
  - `smart_core` `addons/smart_core/orchestration/__init__.py:4` → `from .cost_tracking_contract_orchestrator import CostTrackingContractOrchestrator`
- `finance_center`
  - `smart_core` `addons/smart_core/core/workspace_home_shell_helper.py:17` → `"finance_center": "workspace.finance",`
  - `smart_construction_scene` `addons/smart_construction_scene/profiles/workspace_home_scene_content.py:18` → `"finance_center": "finance.center",`
- `page.badge.runtime_ok`
  - `smart_construction_scene` `addons/smart_construction_scene/profiles/workspace_home_scene_content.py:521` → `"page.badge.runtime_ok": "运行正常",`
  - `smart_core` `addons/smart_core/core/workspace_home_contract_builder.py:1418` → `"page.badge.runtime_ok": "运行正常",`

## Scan Notes

- Duplicate here means same orchestration-surface key appears in two or more module families.
- Ownership and conflict severity judgment are deferred to subsequent screen batch.
