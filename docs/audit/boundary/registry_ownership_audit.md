# Registry Ownership Audit (Phase B-3 / Scan)

- Stage: `scan` (fact-only; no final ownership verdict)
- Scope: `core_extension.py`, `capability_registry.py`, `smart_core/**`, `smart_construction_scene/**`

## Source Counts

- `addons/smart_construction_core/core_extension.py` evidence lines: `99`
- core_extension registry bindings (`registry[...]`): `42`
- core_extension scene hook evidence: `10`
- core_extension capability hook evidence: `2`
- `addons/smart_construction_core/services/capability_registry.py` evidence lines: `3`
- `addons/smart_core/**` registry-related evidence lines: `39`
- `addons/smart_construction_scene/**` registry-related evidence lines: `42`

## core_extension Registry Binding Evidence

- `addons/smart_construction_core/core_extension.py:380` → `registry["system.ping.construction"] = SystemPingConstructionHandler`
- `addons/smart_construction_core/core_extension.py:381` → `registry["capability.describe"] = CapabilityDescribeHandler`
- `addons/smart_construction_core/core_extension.py:382` → `registry["my.work.summary"] = MyWorkSummaryHandler`
- `addons/smart_construction_core/core_extension.py:383` → `registry["my.work.complete"] = MyWorkCompleteHandler`
- `addons/smart_construction_core/core_extension.py:384` → `registry["my.work.complete_batch"] = MyWorkCompleteBatchHandler`
- `addons/smart_construction_core/core_extension.py:385` → `registry["usage.track"] = UsageTrackHandler`
- `addons/smart_construction_core/core_extension.py:386` → `registry["telemetry.track"] = TelemetryTrackHandler`
- `addons/smart_construction_core/core_extension.py:387` → `registry["usage.report"] = UsageReportHandler`
- `addons/smart_construction_core/core_extension.py:388` → `registry["usage.export.csv"] = UsageExportCsvHandler`
- `addons/smart_construction_core/core_extension.py:389` → `registry["capability.visibility.report"] = CapabilityVisibilityReportHandler`
- `addons/smart_construction_core/core_extension.py:390` → `registry["payment.request.submit"] = PaymentRequestSubmitHandler`
- `addons/smart_construction_core/core_extension.py:391` → `registry["payment.request.approve"] = PaymentRequestApproveHandler`
- `addons/smart_construction_core/core_extension.py:392` → `registry["payment.request.reject"] = PaymentRequestRejectHandler`
- `addons/smart_construction_core/core_extension.py:393` → `registry["payment.request.done"] = PaymentRequestDoneHandler`
- `addons/smart_construction_core/core_extension.py:394` → `registry["payment.request.available_actions"] = PaymentRequestAvailableActionsHandler`
- `addons/smart_construction_core/core_extension.py:395` → `registry["payment.request.execute"] = PaymentRequestExecuteHandler`
- `addons/smart_construction_core/core_extension.py:396` → `registry["project.dashboard"] = ProjectDashboardHandler`
- `addons/smart_construction_core/core_extension.py:397` → `registry["project.dashboard.open"] = ProjectDashboardOpenHandler`
- `addons/smart_construction_core/core_extension.py:398` → `registry["project.dashboard.enter"] = ProjectDashboardEnterHandler`
- `addons/smart_construction_core/core_extension.py:399` → `registry["project.entry.context.resolve"] = ProjectEntryContextResolveHandler`
- `addons/smart_construction_core/core_extension.py:400` → `registry["project.entry.context.options"] = ProjectEntryContextOptionsHandler`
- `addons/smart_construction_core/core_extension.py:401` → `registry["business.evidence.trace"] = BusinessEvidenceTraceHandler`
- `addons/smart_construction_core/core_extension.py:402` → `registry["project.dashboard.block.fetch"] = ProjectDashboardBlockFetchHandler`
- `addons/smart_construction_core/core_extension.py:403` → `registry["project.plan_bootstrap.enter"] = ProjectPlanBootstrapEnterHandler`
- `addons/smart_construction_core/core_extension.py:404` → `registry["project.plan_bootstrap.block.fetch"] = ProjectPlanBootstrapBlockFetchHandler`
- `addons/smart_construction_core/core_extension.py:405` → `registry["project.execution.enter"] = ProjectExecutionEnterHandler`
- `addons/smart_construction_core/core_extension.py:406` → `registry["project.execution.block.fetch"] = ProjectExecutionBlockFetchHandler`
- `addons/smart_construction_core/core_extension.py:407` → `registry["project.execution.advance"] = ProjectExecutionAdvanceHandler`
- `addons/smart_construction_core/core_extension.py:408` → `registry["project.connection.transition"] = ProjectConnectionTransitionHandler`
- `addons/smart_construction_core/core_extension.py:409` → `registry["cost.tracking.enter"] = CostTrackingEnterHandler`
- `addons/smart_construction_core/core_extension.py:410` → `registry["cost.tracking.block.fetch"] = CostTrackingBlockFetchHandler`
- `addons/smart_construction_core/core_extension.py:411` → `registry["cost.tracking.record.create"] = CostTrackingRecordCreateHandler`
- `addons/smart_construction_core/core_extension.py:412` → `registry["payment.enter"] = PaymentSliceEnterHandler`
- `addons/smart_construction_core/core_extension.py:413` → `registry["payment.block.fetch"] = PaymentSliceBlockFetchHandler`
- `addons/smart_construction_core/core_extension.py:414` → `registry["payment.record.create"] = PaymentSliceRecordCreateHandler`
- `addons/smart_construction_core/core_extension.py:415` → `registry["settlement.enter"] = SettlementSliceEnterHandler`
- `addons/smart_construction_core/core_extension.py:416` → `registry["settlement.block.fetch"] = SettlementSliceBlockFetchHandler`
- `addons/smart_construction_core/core_extension.py:417` → `registry["project.initiation.enter"] = ProjectInitiationEnterHandler`
- `addons/smart_construction_core/core_extension.py:418` → `registry["risk.action.execute"] = RiskActionExecuteHandler`
- `addons/smart_construction_core/core_extension.py:419` → `registry["app.catalog"] = AppCatalogHandler`
- `addons/smart_construction_core/core_extension.py:420` → `registry["app.nav"] = AppNavHandler`
- `addons/smart_construction_core/core_extension.py:421` → `registry["app.open"] = AppOpenHandler`

## core_extension Cross-Module Hook Evidence

- `addons/smart_construction_core/core_extension.py:466` → `from odoo.addons.smart_construction_core.services.capability_registry import (`
- `addons/smart_construction_core/core_extension.py:481` → `from odoo.addons.smart_construction_core.services.capability_registry import CAPABILITY_GROUPS`
- `addons/smart_construction_core/core_extension.py:487` → `def smart_core_scene_package_service_class(env):`
- `addons/smart_construction_core/core_extension.py:490` → `from odoo.addons.smart_construction_scene.services.scene_package_service import ScenePackageService`
- `addons/smart_construction_core/core_extension.py:493` → `return ScenePackageService`
- `addons/smart_construction_core/core_extension.py:496` → `def smart_core_scene_governance_service_class(env):`
- `addons/smart_construction_core/core_extension.py:499` → `from odoo.addons.smart_construction_scene.services.scene_governance_service import SceneGovernanceService`
- `addons/smart_construction_core/core_extension.py:502` → `return SceneGovernanceService`
- `addons/smart_construction_core/core_extension.py:507` → `from odoo.addons.smart_construction_scene.scene_registry import load_scene_configs`
- `addons/smart_construction_core/core_extension.py:518` → `from odoo.addons.smart_construction_scene.scene_registry import has_db_scenes`
- `addons/smart_construction_core/core_extension.py:530` → `from odoo.addons.smart_construction_scene.scene_registry import get_scene_version`
- `addons/smart_construction_core/core_extension.py:542` → `from odoo.addons.smart_construction_scene.scene_registry import get_schema_version`

## smart_core Registry-Side Evidence (sample)

- `addons/smart_core/__init__.py:25` → `# Ensure intent controllers are registered on module load`
- `addons/smart_core/models/ui_base_contract_asset_event_trigger.py:8` → `from odoo.addons.smart_core.core.scene_registry_provider import load_scene_configs as registry_load_scene_configs`
- `addons/smart_core/adapters/odoo_nav_adapter.py:26` → `payload = call_extension_hook_first(env, "smart_core_nav_scene_maps", env)`
- `addons/smart_core/view/native_view_parser_registry.py:30` → `def register_parser(view_type: str, parser_cls: Type) -> None:`
- `addons/smart_core/view/native_view_parser_registry.py:41` → `def list_registered_view_types() -> list[str]:`
- `addons/smart_core/core/workspace_home_provider_defaults.py:43` → `"ds_capability_groups": {"source_type": "capability_registry", "provider": "workspace.capability.groups", "section_keys": ["group_overview"]},`
- `addons/smart_core/handlers/scene_packages_installed.py:9` → `service_cls = call_extension_hook_first(env, "smart_core_scene_package_service_class", env)`
- `addons/smart_core/handlers/scene_packages_installed.py:19` → `REQUIRED_GROUPS = ["smart_core.group_smart_core_scene_admin"]`
- `addons/smart_core/handlers/scene_package.py:17` → `service_cls = call_extension_hook_first(env, "smart_core_scene_package_service_class", env)`
- `addons/smart_core/handlers/scene_package.py:24` → `REQUIRED_GROUPS = ["smart_core.group_smart_core_scene_admin"]`
- `addons/smart_core/core/workspace_home_contract_builder.py:1148` → `"source_type": "capability_registry",`
- `addons/smart_core/handlers/enhanced_ui_contract.py:264` → `def register_middlewares(router):`
- `addons/smart_core/utils/contract_governance.py:2713` → `def register_contract_domain_override(`
- `addons/smart_core/handlers/scene_governance.py:16` → `service_cls = call_extension_hook_first(env, "smart_core_scene_governance_service_class", env)`
- `addons/smart_core/handlers/scene_governance.py:23` → `REQUIRED_GROUPS = ["smart_core.group_smart_core_scene_admin"]`
- `addons/smart_core/handlers/scene_catalog.py:8` → `from odoo.addons.smart_scene.core.scene_registry_engine import load_scene_registry_content_entries`
- `addons/smart_core/handlers/scene_catalog.py:23` → `rows = load_scene_registry_content_entries(Path(__file__))`
- `addons/smart_core/core/orchestration_semantics.py:25` → `DATA_SOURCE_TYPES = ("static", "scene_context", "api.data", "computed", "capability_registry", "role_profile", "mixed")`
- `addons/smart_core/core/ui_base_contract_asset_producer.py:12` → `from odoo.addons.smart_core.core.scene_registry_provider import (`
- `addons/smart_core/core/handler_registry.py:21` → `def register_all_handlers():`
- `addons/smart_core/core/handler_registry.py:80` → `register_all_handlers()`
- `addons/smart_core/core/extension_loader.py:24` → `Load external modules and let them register handlers into registry.`
- `addons/smart_core/core/extension_loader.py:25` → `Expected hook: smart_core_register(registry)`
- `addons/smart_core/core/extension_loader.py:66` → `hook = getattr(m, "smart_core_register", None)`
- `addons/smart_core/core/extension_loader.py:73` → `log("[extension_loader] registered module: %s (handlers +%s)", mod, after - before)`
- `addons/smart_core/core/extension_loader.py:79` → `_logger.warning("[extension_loader] no smart_core_register in %s", mod)`
- `addons/smart_core/core/scene_governance_payload_builder.py:166` → `scene_registry_count = max(delivery_input_count, nav_input_count)`
- `addons/smart_core/core/scene_governance_payload_builder.py:172` → `"scene_registry_count": int(scene_registry_count),`
- `addons/smart_core/core/scene_dsl_compiler.py:673` → `issues.append(f"provider not registered: {provider}")`
- `addons/smart_core/core/scene_registry_provider.py:8` → `payload = call_extension_hook_first(env, "smart_core_load_scene_configs", env, drift=drift)`
- `addons/smart_core/core/scene_registry_provider.py:13` → `result = call_extension_hook_first(env, "smart_core_has_db_scenes", env)`
- `addons/smart_core/core/scene_registry_provider.py:18` → `result = call_extension_hook_first(env, "smart_core_get_scene_version", env)`
- `addons/smart_core/tests/test_native_view_parser_skeleton.py:77` → `self.assertIn("form", registry_module.list_registered_view_types())`
- `addons/smart_core/core/scene_provider.py:10` → `from odoo.addons.smart_core.core.scene_registry_provider import (`
- `addons/smart_core/core/scene_provider.py:25` → `payload = call_extension_hook_first(env, "smart_core_critical_scene_target_overrides", env)`
- `addons/smart_core/core/scene_provider.py:34` → `payload = call_extension_hook_first(env, "smart_core_critical_scene_target_route_overrides", env)`
- `addons/smart_core/tests/test_v1_intent_smoke.py:228` → `self.assertIn("scene_registry_count", scene_metrics)`
- `addons/smart_core/tests/test_contract_governance_project_form.py:7` → `register_contract_domain_override,`
- `addons/smart_core/tests/test_contract_governance_project_form.py:291` → `register_contract_domain_override(`

## smart_construction_scene Registry-Side Evidence (sample)

- `addons/smart_construction_scene/__init__.py:2` → `from . import scene_registry  # noqa: F401`
- `addons/smart_construction_scene/__init__.py:8` → `smart_core_register,`
- `addons/smart_construction_scene/__init__.py:11` → `smart_core_nav_scene_maps,`
- `addons/smart_construction_scene/__init__.py:16` → `smart_core_critical_scene_target_overrides,`
- `addons/smart_construction_scene/__init__.py:17` → `smart_core_critical_scene_target_route_overrides,`
- `addons/smart_construction_scene/services/scene_package_service.py:10` → `from odoo.addons.smart_construction_scene import scene_registry`
- `addons/smart_construction_scene/services/scene_package_service.py:17` → `class ScenePackageService:`
- `addons/smart_construction_scene/services/scene_package_service.py:400` → `existing = scene_registry.load_scene_configs(self.env)`
- `addons/smart_construction_scene/services/scene_package_service.py:454` → `existing = scene_registry.load_scene_configs(self.env)`
- `addons/smart_construction_scene/services/scene_governance_service.py:10` → `class SceneGovernanceService:`
- `addons/smart_construction_scene/core_extension.py:188` → `def smart_core_register(registry):`
- `addons/smart_construction_scene/core_extension.py:203` → `def smart_core_nav_scene_maps(env):`
- `addons/smart_construction_scene/core_extension.py:232` → `def smart_core_critical_scene_target_overrides(env):`
- `addons/smart_construction_scene/core_extension.py:237` → `def smart_core_critical_scene_target_route_overrides(env):`
- `addons/smart_construction_scene/services/project_management_entry_target.py:6` → `from odoo.addons.smart_construction_scene.scene_registry import load_scene_configs`
- `addons/smart_construction_scene/bootstrap/register_scene_providers.py:7` → `def register_scene_content_providers(registry, addons_root: Path) -> None:`
- `addons/smart_construction_scene/bootstrap/register_scene_providers.py:15` → `registry.register_spec(`
- `addons/smart_construction_scene/bootstrap/register_scene_providers.py:23` → `registry.register_spec(`
- `addons/smart_construction_scene/bootstrap/register_scene_providers.py:31` → `registry.register_spec(`
- `addons/smart_construction_scene/bootstrap/register_scene_providers.py:33` → `provider_key="construction.scene_registry.v1",`
- `addons/smart_construction_scene/bootstrap/register_scene_providers.py:35` → `provider_path=addons_root / scene_module / "profiles" / "scene_registry_content.py",`
- `addons/smart_construction_scene/bootstrap/register_scene_providers.py:39` → `registry.register_spec(`
- `addons/smart_construction_scene/bootstrap/register_scene_providers.py:47` → `registry.register_spec(`
- `addons/smart_construction_scene/services/capability_scene_targets.py:6` → `from odoo.addons.smart_construction_scene import scene_registry`
- `addons/smart_construction_scene/services/capability_scene_targets.py:76` → `scenes = scene_registry.load_scene_configs(env)`
- `addons/smart_construction_scene/bootstrap/register_nav_policy.py:7` → `def register_nav_product_policies(registry, addons_root: Path) -> None:`
- `addons/smart_construction_scene/bootstrap/register_nav_policy.py:11` → `registry.register_spec(`
- `addons/smart_construction_scene/profiles/workspace_home_scene_content.py:556` → `"source_type": "capability_registry",`
- `addons/smart_construction_scene/scene_registry.py:16` → `def _load_scene_registry_engine_module():`
- `addons/smart_construction_scene/scene_registry.py:20` → `engine_path = Path(__file__).resolve().parents[1] / "smart_scene" / "core" / "scene_registry_engine.py"`
- `addons/smart_construction_scene/scene_registry.py:22` → `spec = spec_from_file_location("smart_scene_scene_registry_engine", engine_path)`
- `addons/smart_construction_scene/scene_registry.py:34` → `def _load_scene_registry_content_module():`
- `addons/smart_construction_scene/scene_registry.py:38` → `engine = _load_scene_registry_engine_module()`
- `addons/smart_construction_scene/scene_registry.py:39` → `loader = getattr(engine, "load_scene_registry_content_module", None) if engine else None`
- `addons/smart_construction_scene/scene_registry.py:48` → `def _load_scene_registry_content_entries():`
- `addons/smart_construction_scene/scene_registry.py:50` → `content_path = Path(__file__).resolve().parent / "profiles" / "scene_registry_content.py"`
- `addons/smart_construction_scene/scene_registry.py:54` → `spec = spec_from_file_location("smart_construction_scene_registry_content", content_path)`
- `addons/smart_construction_scene/scene_registry.py:64` → `engine = _load_scene_registry_engine_module()`
- `addons/smart_construction_scene/scene_registry.py:65` → `loader = getattr(engine, "load_scene_registry_content_entries", None) if engine else None`
- `addons/smart_construction_scene/scene_registry.py:307` → `for scene in _load_scene_registry_content_entries():`

## Scan Notes

- This document reports registration/hook evidence only.
- Single-source vs dual-source ownership conclusion is deferred to next `screen` batch.
