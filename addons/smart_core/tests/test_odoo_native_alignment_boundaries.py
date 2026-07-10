# -*- coding: utf-8 -*-
import importlib

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.handlers.chatter_activity_schedule import ChatterActivityScheduleHandler
from odoo.addons.smart_core.handlers.chatter_post import ChatterPostHandler
from odoo.addons.smart_core.handlers.chatter_timeline import ChatterTimelineHandler
from odoo.addons.smart_core.handlers.api_data import ApiDataHandler
from odoo.addons.smart_core.handlers.api_data_batch import ApiDataBatchHandler
from odoo.addons.smart_core.handlers.api_data_unlink import ApiDataUnlinkHandler
from odoo.addons.smart_core.handlers.api_data_write import ApiDataWriteHandler
from odoo.addons.smart_core.handlers.api_onchange import ApiOnchangeHandler
from odoo.addons.smart_core.handlers.execute_button import ExecuteButtonHandler
from odoo.addons.smart_core.handlers.file_download import FileDownloadHandler
from odoo.addons.smart_core.handlers.file_upload import FileUploadHandler
from odoo.addons.smart_core.handlers.load_contract import LoadContractHandler
from odoo.addons.smart_core.handlers.load_metadata import LoadMetadataHandler
from odoo.addons.smart_core.handlers.load_view import LoadModelViewHandler
from odoo.addons.smart_core.handlers.login import LoginHandler, LogoutHandler
from odoo.addons.smart_core.handlers.meta_describe import MetaDescribeHandler
from odoo.addons.smart_core.handlers.meta_intent_catalog import MetaIntentCatalogHandler
from odoo.addons.smart_core.handlers.permission_check import PermissionCheckHandler
from odoo.addons.smart_core.handlers.project_context import ProjectContextSearchHandler
from odoo.addons.smart_core.handlers.scene_health import SceneHealthHandler
from odoo.addons.smart_core.handlers.scene_packages_installed import ScenePackagesInstalledHandler
from odoo.addons.smart_core.handlers.app_shell import AppCatalogHandler, AppNavHandler, AppOpenHandler
from odoo.addons.smart_core.handlers.search_favorite_set import SearchFavoriteSetHandler
from odoo.addons.smart_core.handlers.session_bootstrap import SessionBootstrapHandler
from odoo.addons.smart_core.handlers.terminal_shell_v2 import TerminalShellV2Handler
from odoo.addons.smart_core.handlers import reason_codes as handler_reason_codes
from odoo.addons.smart_core.handlers.system_init import (
    SystemInitHandler,
    _resolve_industry_extension_modules,
    _resolve_startup_delivery_identity,
)
from odoo.addons.smart_core.controllers import platform_menu_api
from odoo.addons.smart_core.controllers import intent_dispatcher
from odoo.addons.smart_core.app_config_engine.controllers import contract_api
from odoo.addons.smart_core.adapters.nav_tree_cleaner import NavTreeCleaner
from odoo.addons.smart_core.adapters.odoo_nav_adapter import OdooNavAdapter
from odoo.addons.smart_core.app_config_engine.services.assemblers.client_url_report import ClientUrlReportAssembler
from odoo.addons.smart_core.app_config_engine.services.assemblers.page_assembler import PageAssembler
from odoo.addons.smart_core.app_config_engine.services.contract_service import ContractService
from odoo.addons.smart_core.app_config_engine.services.contract_governance_filter import ContractGovernanceFilterService
from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import ActionDispatcher
from odoo.addons.smart_core.app_config_engine.services.dispatchers.menu_dispatcher import MenuDispatcher
from odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher import NavDispatcher
from odoo.addons.smart_core.app_config_engine.services.native_parse_service import NativeParseService
from odoo.addons.smart_core.app_config_engine.services.normalizer import ContractNormalizer
from odoo.addons.smart_core.app_config_engine.services.parse_fallback_service import ParseFallbackService
from odoo.addons.smart_core.app_config_engine.services.resolvers.action_resolver import ActionResolver
from odoo.addons.smart_core.app_config_engine.services.view_Parser import base as view_parser_base
from odoo.addons.smart_core.app_config_engine.utils import http as contract_http_utils
from odoo.addons.smart_core.app_config_engine.utils import misc as contract_misc_utils
from odoo.addons.smart_core.app_config_engine.utils import payload as contract_payload_utils
from odoo.addons.smart_core.app_config_engine.utils.view_utils import view_utils as contract_view_utils
from odoo.addons.smart_core.view.base import BaseViewParser
from odoo.addons.smart_core.view.form_parser import FormViewParser
from odoo.addons.smart_core.view.universal_parser import UniversalViewSemanticParser
from odoo.addons.smart_core.view.view_dispatcher import ViewDispatcher
from odoo.addons.smart_core.handlers.ui_contract import UiContractHandler
from odoo.addons.smart_core.handlers.ui_contract_v2 import UiContractV2Handler
from odoo.addons.smart_core.handlers.user_view_preference import (
    UserViewPreferenceGetHandler,
    UserViewPreferenceSetHandler,
)
from odoo.addons.smart_core.handlers.versioned_handler import VersionedDataHandlerV21
from odoo.addons.smart_core.core.handler_registry import HANDLER_REGISTRY
from odoo.addons.smart_core.core import handler_registry as handler_registry_module
from odoo.addons.smart_core.core import action_target_schema
from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.core.context import RequestContext
from odoo.addons.smart_core.core import exceptions as core_exceptions
from odoo.addons.smart_core.core import hash_utils
from odoo.addons.smart_core.core.intent_execution_result import IntentExecutionResult
from odoo.addons.smart_core.core import intent_router
from odoo.addons.smart_core.core.middlewares import BaseMiddleware
from odoo.addons.smart_core.core import middlewares
from odoo.addons.smart_core.core import trace
from odoo.addons.smart_core.core import industry_orchestration_service_adapter
from odoo.addons.smart_core.core import extension_loader
from odoo.addons.smart_core.utils import extension_hooks
from odoo.addons.smart_core.core.intent_surface_builder import IntentSurfaceBuilder
from odoo.addons.smart_core.core.scene_channel_policy import SceneChannelPolicy
from odoo.addons.smart_core.core import ui_base_contract_asset_event_queue
from odoo.addons.smart_core.core import ui_base_contract_asset_repository
from odoo.addons.smart_core.core import system_init_dictionary_data_helper
from odoo.addons.smart_core.core import command_registry
from odoo.addons.smart_core.core import delivery_capability_entry_defaults
from odoo.addons.smart_core.core import delivery_menu_defaults
from odoo.addons.smart_core.core import scene_ready_contract_builder
from odoo.addons.smart_core.app_config_engine.models.app_report_config import AppReportConfig
from odoo.addons.smart_core.handlers.scene_governance import SceneGovernanceExportContractHandler
from odoo.addons.smart_core.handlers.scene_package import ScenePackageListHandler
from odoo.addons.smart_core.core import scene_registry_provider
from odoo.addons.smart_core.core import scene_provider
from odoo.addons.smart_core.core import orchestration_semantics
from odoo.addons.smart_core.core import page_contract_parser_semantic_bridge
from odoo.addons.smart_core.core import page_contract_semantic_orchestration_bridge
from odoo.addons.smart_core.core import released_scene_semantic_surface_bridge
from odoo.addons.smart_core.core import runtime_page_parser_semantic_bridge
from odoo.addons.smart_core.core import runtime_page_semantic_orchestration_bridge
from odoo.addons.smart_core.core import scene_contract_parser_semantic_bridge
from odoo.addons.smart_core.core import scene_contract_semantic_orchestration_bridge
from odoo.addons.smart_core.core import scene_governance_payload_builder
from odoo.addons.smart_core.core import scene_ready_entry_semantic_bridge
from odoo.addons.smart_core.core import scene_ready_parser_semantic_bridge
from odoo.addons.smart_core.core import scene_ready_semantic_orchestration_bridge
from odoo.addons.smart_core.core import system_init_extension_fact_merger
from odoo.addons.smart_core.core import system_init_scene_runtime_semantic_bridge
from odoo.addons.smart_core.core import native_view_contract_projection
from odoo.addons.smart_core.core import page_orchestration_data_provider
from odoo.addons.smart_core.core import scene_dsl_compiler
from odoo.addons.smart_core.core import scene_merge_resolver
from odoo.addons.smart_core.core import scene_nav_contract_builder
from odoo.addons.smart_core.core import ui_base_contract_adapter
from odoo.addons.smart_core.core import ui_base_contract_asset_producer
from odoo.addons.smart_core.core import ui_base_contract_canonicalizer
from odoo.addons.smart_core.core import unified_page_contract_lite_adapter
from odoo.addons.smart_core.core import unified_page_contract_lite_patch_normalizer
from odoo.addons.smart_core.core import unified_page_contract_lite_preview
from odoo.addons.smart_core.core import unified_page_contract_lite_source_normalizer
from odoo.addons.smart_core.core import unified_page_contract_v2_action
from odoo.addons.smart_core.core import unified_page_contract_v2_assembler
from odoo.addons.smart_core.core import unified_page_contract_v2_client
from odoo.addons.smart_core.core import unified_page_contract_v2_data
from odoo.addons.smart_core.core import unified_page_contract_v2_runtime
from odoo.addons.smart_core.core import unified_page_contract_v2_status
from odoo.addons.smart_core.core.contract_assembler import ContractAssembler
from odoo.addons.smart_core.core.scene_diagnostics_builder import SceneDiagnosticsBuilder
from odoo.addons.smart_core.core.scene_runtime_orchestrator import SceneRuntimeOrchestrator
from odoo.addons.smart_core.core.view_orchestrator import ViewOrchestrator
from odoo.addons.smart_core.core import workspace_home_contract_builder
from odoo.addons.smart_core.core import workspace_home_data_provider
from odoo.addons.smart_core.core import scene_delivery_policy
from odoo.addons.smart_core.core import project_context
from odoo.addons.smart_core.core import release_navigation_contract_builder
from odoo.addons.smart_core.core import scene_contract_builder
from odoo.addons.smart_core.core import page_contracts_builder
from odoo.addons.smart_core.core.system_init_payload_builder import SystemInitPayloadBuilder
from odoo.addons.smart_core.core.system_init_components_factory import SystemInitComponentsFactory
from odoo.addons.smart_core.core.system_init_runtime_context import SystemInitRuntimeContext
from odoo.addons.smart_core.core.system_init_surface_context import SystemInitSurfaceContext
from odoo.addons.smart_core.core.system_init_scene_runtime_surface_context import SystemInitSceneRuntimeSurfaceContext
from odoo.addons.smart_core.core.system_init_diagnostics_helper import SystemInitDiagnosticsHelper
from odoo.addons.smart_core.core.system_init_identity_payload import SystemInitIdentityPayload
from odoo.addons.smart_core.core.system_init_nav_request_builder import SystemInitNavRequestBuilder
from odoo.addons.smart_core.core.system_init_preload_builder import SystemInitPreloadBuilder
from odoo.addons.smart_core.core.system_init_response_meta_builder import SystemInitResponseMetaBuilder
from odoo.addons.smart_core.core.system_init_surface_builder import SystemInitSurfaceBuilder
from odoo.addons.smart_core.core.system_init_scene_runtime_surface_builder import SystemInitSceneRuntimeSurfaceBuilder
from odoo.addons.smart_core.core.request_diagnostics import RequestDiagnosticsCollector
from odoo.addons.smart_core.core import runtime_page_contract_builder
from odoo.addons.smart_core.core import capability_provider
from odoo.addons.smart_core.app_config_engine.models.app_action_config import AppActionConfig
from odoo.addons.smart_core.app_config_engine.models.app_model_config import AppModelConfig
from odoo.addons.smart_core.app_config_engine.models.app_nav_config import AppMenuConfig
from odoo.addons.smart_core.app_config_engine.models.app_permission_config import AppPermissionConfig
from odoo.addons.smart_core.app_config_engine.models.app_validator_config import AppValidatorConfig
from odoo.addons.smart_core.app_config_engine.models.app_view_config import AppViewConfig
from odoo.addons.smart_core.app_config_engine.models.app_view_fragment import AppViewFragment
from odoo.addons.smart_core.app_config_engine.models.app_view_variant import AppViewVariant
from odoo.addons.smart_core.app_config_engine.models.app_workflow_config import AppWorkflowConfig
from odoo.addons.smart_core.app_config_engine.models.contract_mixin import ContractSchemaMixin
from odoo.addons.smart_core.models.app_action_gateway import AppActionGateway
from odoo.addons.smart_core.models.ui_base_contract_asset import UiBaseContractAsset
from odoo.addons.smart_core.models.ui_base_contract_asset_event_trigger import IrUiViewAssetTrigger
from odoo.addons.smart_core.models.user_view_preference import ScUserViewPreference
from odoo.addons.smart_core.delivery.product_policy_service import (
    ProductPolicyService,
    default_policy_node_source_authority_contract,
)
from odoo.addons.smart_core.delivery import product_identity
from odoo.addons.smart_core.governance.scene_drift_engine import SceneDriftEngine
from odoo.addons.smart_core.governance.capability_surface_engine import CapabilitySurfaceEngine
from odoo.addons.smart_core.governance.scene_normalizer import SceneNormalizer
from odoo.addons.smart_core.identity.identity_resolver import IdentityResolver
from odoo.addons.smart_core.delivery.delivery_engine import DeliveryEngine
from odoo.addons.smart_core.delivery.capability_service import CapabilityService
from odoo.addons.smart_core.delivery.menu_fact_service import MenuFactService
from odoo.addons.smart_core.delivery.menu_service import MenuService
from odoo.addons.smart_core.delivery.scene_service import SceneService
from odoo.addons.smart_core.delivery.scene_snapshot_service import SceneSnapshotService
from odoo.addons.smart_core.delivery.edition_release_snapshot_service import EditionReleaseSnapshotService
from odoo.addons.smart_core.delivery.edition_release_snapshot_promotion_service import EditionReleaseSnapshotPromotionService
from odoo.addons.smart_core.delivery.release_approval_policy_service import ReleaseApprovalPolicyService
from odoo.addons.smart_core.delivery.release_audit_trail_service import ReleaseAuditTrailService
from odoo.addons.smart_core.delivery.release_operator_read_model_service import ReleaseOperatorReadModelService
from odoo.addons.smart_core.delivery.release_operator_surface_service import ReleaseOperatorSurfaceService
from odoo.addons.smart_core.delivery.menu_target_interpreter_service import MenuTargetInterpreterService
from odoo.addons.smart_core.delivery import release_operator_contract_registry
from odoo.addons.smart_core.delivery import release_operator_contract_versions
from odoo.addons.smart_core.utils import reason_codes
from odoo.addons.smart_core.utils import contract_governance
from odoo.addons.smart_core.utils import delete_policy
from odoo.addons.smart_core.utils import idempotency
from odoo.addons.smart_core.utils import response_builder
from odoo.addons.smart_core.security import intent_permission
from odoo.addons.smart_core.security import auth as smart_auth
from odoo.addons.smart_core.model.ui_dynamic_config import UIDynamicConfig
from odoo.addons.smart_core.runtime.auto_degrade_engine import AutoDegradeEngine
from odoo.addons.smart_core.tools import intent_acl_mode_guard
from odoo.addons.smart_core.tools import intent_write_guard
from odoo.addons.smart_core.orchestration.base_scene_entry_orchestrator import BaseSceneEntryOrchestrator
from odoo.addons.smart_core.orchestration.cost_tracking_contract_orchestrator import CostTrackingContractOrchestrator
from odoo.addons.smart_core.orchestration.payment_slice_contract_orchestrator import PaymentSliceContractOrchestrator
from odoo.addons.smart_core.orchestration.project_dashboard_scene_orchestrator import ProjectDashboardSceneOrchestrator
from odoo.addons.smart_core.orchestration.project_execution_scene_orchestrator import ProjectExecutionSceneOrchestrator
from odoo.addons.smart_core.orchestration.project_plan_bootstrap_scene_orchestrator import (
    ProjectPlanBootstrapSceneOrchestrator,
)
from odoo.addons.smart_core.orchestration.settlement_slice_contract_orchestrator import (
    SettlementSliceContractOrchestrator,
)


@tagged("post_install", "-at_install", "smart_core", "native_alignment")
class TestOdooNativeAlignmentBoundaries(TransactionCase):
    def test_search_config_declares_odoo_native_authorities(self):
        cfg = self.env["app.search.config"]
        source = cfg._source_contract("project.project")

        self.assertEqual(source.get("kind"), "odoo_native_search_projection")
        self.assertTrue(source.get("rebuildable"))
        self.assertTrue(source.get("no_business_fact_authority"))
        self.assertIn("ir.ui.view:search", source.get("authorities") or [])
        self.assertIn("ir.filters", source.get("authorities") or [])

    def test_user_view_preference_scope_is_ui_only_and_action_scoped(self):
        pref = self.env["sc.user.view.preference"]

        scope = pref.build_scope_key(
            preference_key="list_columns",
            view_type="list",
            action_id=42,
            model_name="project.project",
        )

        self.assertEqual(scope, "ui:list_columns:list:action:42")
        self.assertEqual(pref.normalize_preference_key("unknown"), "list_columns")

    def test_formal_list_surface_rejects_test_placeholder_contract(self):
        action = self.env.ref("smart_construction_core.action_sc_project_list", raise_if_not_found=False)
        if not action:
            self.skipTest("smart_construction_core.action_sc_project_list not installed")

        with self.assertRaises(ValidationError):
            self.env["ui.business.config.contract"].create({
                "name": "codex_view_orch_surface_test:tree",
                "model": "project.project",
                "view_type": "tree",
                "action_id": action.id,
                "status": "published",
                "contract_json": {
                    "view_orchestration": {
                        "views": {
                            "tree": {
                                "columns": [
                                    {"name": "name", "label": "CODEX_NAME_COLUMN", "sequence": 10},
                                ],
                            },
                        },
                    },
                },
            })

    def test_collaboration_handlers_declare_odoo_native_authorities(self):
        self.assertEqual(ChatterTimelineHandler.SOURCE_KIND, "odoo_collaboration_timeline_projection")
        self.assertEqual(ChatterPostHandler.SOURCE_AUTHORITY, "mail.message")
        self.assertEqual(ChatterActivityScheduleHandler.SOURCE_AUTHORITY, "mail.activity")
        self.assertEqual(ChatterPostHandler.source_authority_contract().get("kind"), "odoo_collaboration_message_write_proxy")
        self.assertTrue(ChatterPostHandler.source_authority_contract().get("write_proxy"))
        self.assertTrue(ChatterPostHandler.source_authority_contract().get("no_business_fact_authority"))
        self.assertEqual(ChatterActivityScheduleHandler.source_authority_contract().get("kind"), "odoo_collaboration_activity_write_proxy")
        self.assertTrue(ChatterActivityScheduleHandler.source_authority_contract().get("write_proxy"))
        self.assertTrue(ChatterActivityScheduleHandler.source_authority_contract().get("no_business_fact_authority"))
        self.assertTrue(ChatterTimelineHandler.source_authority_contract().get("no_business_fact_authority"))
        self.assertIn("mail.message", ChatterTimelineHandler.SOURCE_AUTHORITIES)
        self.assertIn("mail.activity", ChatterTimelineHandler.SOURCE_AUTHORITIES)
        self.assertIn("ir.attachment", ChatterTimelineHandler.SOURCE_AUTHORITIES)

    def test_file_handlers_declare_attachment_authority(self):
        self.assertEqual(FileUploadHandler.SOURCE_AUTHORITY, "ir.attachment")
        self.assertEqual(FileDownloadHandler.SOURCE_AUTHORITY, "ir.attachment")
        self.assertEqual(FileUploadHandler.source_authority_contract().get("kind"), "odoo_attachment_upload_proxy")
        self.assertTrue(FileUploadHandler.source_authority_contract().get("write_proxy"))
        self.assertTrue(FileUploadHandler.source_authority_contract().get("no_business_fact_authority"))
        self.assertEqual(FileDownloadHandler.source_authority_contract().get("kind"), "odoo_attachment_download_projection")
        self.assertTrue(FileDownloadHandler.source_authority_contract().get("no_business_fact_authority"))

    def test_data_intents_declare_orm_proxy_authorities(self):
        self.assertEqual(ApiDataHandler.SOURCE_KIND, "odoo_orm_proxy")
        self.assertIn("odoo.orm", ApiDataHandler.SOURCE_AUTHORITIES)
        self.assertIn("ir.rule", ApiDataHandler.SOURCE_AUTHORITIES)
        self.assertEqual(ApiDataWriteHandler.SOURCE_KIND, "odoo_orm_write_proxy")
        self.assertIn("odoo.orm", ApiDataWriteHandler.SOURCE_AUTHORITIES)
        self.assertEqual(ApiDataUnlinkHandler.SOURCE_KIND, "odoo_orm_unlink_proxy")
        self.assertIn("odoo.orm", ApiDataUnlinkHandler.SOURCE_AUTHORITIES)
        unlink_policy_source = delete_policy.source_authority_contract()
        self.assertEqual(unlink_policy_source.get("kind"), "unlink_policy_projection")
        self.assertTrue(unlink_policy_source.get("no_business_fact_authority"))
        self.assertEqual(ApiDataBatchHandler.SOURCE_KIND, "odoo_orm_batch_write_proxy")
        self.assertIn("ir.model.access", ApiDataBatchHandler.SOURCE_AUTHORITIES)
        read_source = ApiDataHandler(self.env)._source_authority_contract("res.partner", "list")
        write_source = ApiDataWriteHandler(self.env)._source_authority_contract("res.partner", "write")
        for source in (read_source, write_source):
            self.assertTrue(source.get("proxy_only"))
            self.assertTrue(source.get("no_business_fact_authority"))
            self.assertTrue(source.get("field_value_passthrough_only"))

    def test_onchange_and_button_intents_declare_native_runtime_authorities(self):
        self.assertEqual(ApiOnchangeHandler.SOURCE_KIND, "odoo_onchange_proxy")
        self.assertIn("odoo.onchange", ApiOnchangeHandler.SOURCE_AUTHORITIES)
        self.assertEqual(ExecuteButtonHandler.SOURCE_KIND, "odoo_model_button_proxy")
        self.assertIn("odoo.model.method", ExecuteButtonHandler.SOURCE_AUTHORITIES)
        self.assertIn("ir.actions", ExecuteButtonHandler.SOURCE_AUTHORITIES)

    def test_load_contract_declares_native_view_authorities(self):
        self.assertEqual(LoadContractHandler.SOURCE_KIND, "odoo_native_contract_projection")
        self.assertIn("ir.ui.view", LoadContractHandler.SOURCE_AUTHORITIES)
        self.assertIn("ir.actions.act_window", LoadContractHandler.SOURCE_AUTHORITIES)
        self.assertIn("ir.model.fields", LoadContractHandler.SOURCE_AUTHORITIES)
        self.assertEqual(LoadModelViewHandler.SOURCE_AUTHORITY, "load_contract")
        self.assertEqual(LoadMetadataHandler.SOURCE_KIND, "odoo_fields_get_projection")
        self.assertIn("ir.model.fields", LoadMetadataHandler.SOURCE_AUTHORITIES)

    def test_report_config_declares_native_report_authorities(self):
        self.assertEqual(AppReportConfig.SOURCE_KIND, "odoo_native_report_projection")
        self.assertIn("ir.actions.report", AppReportConfig.SOURCE_AUTHORITIES)
        source = self.env["app.report.config"]._source_contract("project.project")
        self.assertTrue(source.get("rebuildable"))
        self.assertTrue(source.get("no_business_fact_authority"))
        self.assertEqual(source.get("model"), "project.project")

    def test_scene_delivery_handlers_do_not_claim_business_fact_authority(self):
        self.assertEqual(ScenePackageListHandler.SOURCE_KIND, "scene_delivery_governance")
        self.assertIn("ir.actions", ScenePackageListHandler.SOURCE_AUTHORITIES)
        self.assertEqual(SceneGovernanceExportContractHandler.SOURCE_KIND, "scene_delivery_governance")
        registry_source = scene_registry_provider.source_authority_contract()
        self.assertTrue(registry_source.get("projection_only"))
        self.assertTrue(registry_source.get("no_business_fact_authority"))
        delivery_policy_source = scene_delivery_policy.source_authority_contract()
        self.assertEqual(delivery_policy_source.get("kind"), "scene_delivery_policy_projection")
        self.assertTrue(delivery_policy_source.get("no_business_fact_authority"))
        self.assertEqual(delivery_policy_source.get("legacy_surface_alias_source"), "legacy_scene_surface_alias_projection")
        alias_source = scene_delivery_policy.legacy_surface_alias_source_authority_contract()
        self.assertEqual(alias_source.get("kind"), "legacy_scene_surface_alias_projection")
        self.assertTrue(alias_source.get("legacy_compatibility"))
        product_policy_source = ProductPolicyService.source_authority_contract()
        product_identity_source = product_identity.source_authority_contract()
        self.assertEqual(product_policy_source.get("kind"), "delivery_product_policy_projection")
        self.assertTrue(product_policy_source.get("projection_only"))
        self.assertTrue(product_policy_source.get("rebuildable"))
        self.assertTrue(product_policy_source.get("no_business_fact_authority"))
        self.assertIn("sc.product.policy", product_policy_source.get("authorities") or [])
        default_policy_source = ProductPolicyService.default_policy_source_authority_contract()
        self.assertEqual(default_policy_source.get("kind"), "platform_default_product_policy_provider")
        self.assertTrue(default_policy_source.get("no_business_fact_authority"))
        self.assertEqual(default_policy_source.get("default_policy_node_source"), "platform_default_product_policy_node_projection")
        node_source = default_policy_node_source_authority_contract()
        self.assertEqual(node_source.get("kind"), "platform_default_product_policy_node_projection")
        self.assertTrue(node_source.get("platform_default"))
        self.assertEqual(product_identity_source.get("kind"), "delivery_product_identity_resolver")
        self.assertTrue(product_identity_source.get("no_business_fact_authority"))
        self.assertEqual(product_identity_source.get("default_base_source"), "platform_default_base_product_projection")
        default_base_source = product_identity.legacy_default_base_source_authority_contract()
        self.assertEqual(default_base_source.get("kind"), "platform_default_base_product_projection")
        self.assertTrue(default_base_source.get("platform_default"))
        scene_contract_source = scene_contract_builder.source_authority_contract()
        legacy_title_source = scene_contract_builder.legacy_product_title_source_authority_contract()
        self.assertEqual(scene_contract_source.get("kind"), "release_surface_scene_contract_projection")
        self.assertTrue(scene_contract_source.get("no_business_fact_authority"))
        self.assertEqual(legacy_title_source.get("kind"), "legacy_release_product_title_projection")
        self.assertTrue(legacy_title_source.get("legacy_compatibility"))
        page_contract_source = page_contracts_builder.source_authority_contract()
        page_copy_source = page_contracts_builder.page_text_override_source_authority_contract()
        self.assertEqual(page_contract_source.get("kind"), "page_contract_projection")
        self.assertTrue(page_contract_source.get("no_business_fact_authority"))
        self.assertEqual(page_copy_source.get("kind"), "page_text_override_projection")
        self.assertTrue(page_copy_source.get("extension_policy"))
        startup_source = SystemInitPayloadBuilder.source_authority_contract()
        self.assertEqual(startup_source.get("kind"), "system_init_startup_payload_projection")
        self.assertTrue(startup_source.get("no_business_fact_authority"))
        runtime_page_source = runtime_page_contract_builder.source_authority_contract()
        self.assertEqual(runtime_page_source.get("kind"), "runtime_page_contract_projection")
        self.assertTrue(runtime_page_source.get("no_business_fact_authority"))
        snapshot_source = EditionReleaseSnapshotService.source_authority_contract()
        snapshot_role_source = EditionReleaseSnapshotService.legacy_default_role_source_authority_contract()
        self.assertEqual(snapshot_source.get("kind"), "edition_release_snapshot_projection")
        self.assertTrue(snapshot_source.get("no_business_fact_authority"))
        self.assertEqual(snapshot_role_source.get("kind"), "legacy_release_snapshot_default_role_projection")
        self.assertTrue(snapshot_role_source.get("legacy_compatibility"))
        promotion_source = EditionReleaseSnapshotPromotionService.source_authority_contract()
        self.assertEqual(promotion_source.get("kind"), "edition_release_snapshot_promotion_proxy")
        self.assertTrue(promotion_source.get("write_proxy"))
        self.assertTrue(promotion_source.get("no_business_fact_authority"))
        snapshot_cache_source = SceneSnapshotService.source_authority_contract()
        scene_source = SceneService.source_authority_contract()
        self.assertEqual(snapshot_cache_source.get("kind"), "scene_snapshot_projection")
        self.assertTrue(snapshot_cache_source.get("no_business_fact_authority"))
        self.assertEqual(scene_source.get("kind"), "delivery_scene_projection")
        self.assertTrue(scene_source.get("no_business_fact_authority"))
        capability_source = CapabilityService.source_authority_contract()
        startup_capability_source = capability_provider.source_authority_contract()
        self.assertEqual(capability_source.get("kind"), "delivery_capability_projection")
        self.assertTrue(capability_source.get("no_business_fact_authority"))
        self.assertEqual(startup_capability_source.get("kind"), "capability_startup_surface_projection")
        self.assertIn("sc.capability", startup_capability_source.get("authorities") or [])
        self.assertTrue(startup_capability_source.get("no_business_fact_authority"))
        scene_provider_source = scene_provider.source_authority_contract()
        auto_degrade_source = AutoDegradeEngine.source_authority_contract()
        health_source = SceneHealthHandler.source_authority_contract()
        self.assertEqual(scene_provider_source.get("kind"), "scene_runtime_provider_projection")
        self.assertTrue(scene_provider_source.get("no_business_fact_authority"))
        self.assertEqual(auto_degrade_source.get("kind"), "scene_auto_degrade_governance_proxy")
        self.assertTrue(auto_degrade_source.get("write_proxy"))
        self.assertTrue(auto_degrade_source.get("no_business_fact_authority"))
        self.assertEqual(health_source.get("kind"), "scene_delivery_health_projection")
        self.assertTrue(health_source.get("no_business_fact_authority"))
        package_registry_source = ScenePackagesInstalledHandler.source_authority_contract()
        self.assertEqual(package_registry_source.get("kind"), "scene_package_registry_projection")
        self.assertTrue(package_registry_source.get("no_business_fact_authority"))
        for handler_cls, kind in (
            (AppCatalogHandler, "scene_delivery_catalog_projection"),
            (AppNavHandler, "scene_delivery_navigation_projection"),
            (AppOpenHandler, "scene_delivery_open_projection"),
        ):
            with self.subTest(handler=handler_cls.__name__):
                source = handler_cls.source_authority_contract()
                self.assertEqual(source.get("kind"), kind)
                self.assertTrue(source.get("projection_only"))
                self.assertTrue(source.get("no_business_fact_authority"))

    def test_release_product_identity_resolver_is_not_construction_locked(self):
        identity = product_identity.resolve_product_identity(product_key="platform.preview")
        defaults = product_identity.default_operator_product_keys(base_product_key=identity.get("base_product_key"))
        default_identity = product_identity.resolve_product_identity()

        self.assertEqual(identity.get("product_key"), "platform.preview")
        self.assertEqual(identity.get("base_product_key"), "platform")
        self.assertEqual(identity.get("edition_key"), "preview")
        self.assertEqual(defaults, ("platform.standard", "platform.preview"))
        self.assertEqual(
            ((default_identity.get("default_base_source_authority") or {}).get("kind")),
            "platform_default_base_product_projection",
        )

    def test_release_operator_default_base_product_can_be_configured(self):
        self.env["ir.config_parameter"].sudo().set_param("smart_core.release_operator.default_base_product_key", "platform")
        service = ReleaseOperatorReadModelService(self.env)

        identity = service._resolve_identity(product_key="")

        self.assertEqual(identity.get("product_key"), "platform.standard")
        self.assertEqual(identity.get("default_base_source"), "config")
        self.assertEqual((identity.get("source_authority") or {}).get("kind"), "delivery_product_identity_resolver")

    def test_non_construction_missing_product_policy_uses_minimal_default(self):
        policy = ProductPolicyService(self.env).get_policy(product_key="platform.standard")
        delivery = DeliveryEngine(self.env).build(
            data={"role_surface": {"role_code": "operator"}},
            product_key="platform.standard",
        )

        self.assertEqual(policy.get("product_key"), "platform.standard")
        self.assertEqual(policy.get("base_product_key"), "platform")
        self.assertEqual(((policy.get("policy_source_authority") or {}).get("kind")), "minimal_default_product_policy_provider")
        self.assertEqual(policy.get("menu_groups") or [], [])
        self.assertEqual(policy.get("scenes") or [], [])
        self.assertNotIn("settlement", policy.get("scene_version_bindings") or {})
        self.assertEqual(((delivery.get("product_policy") or {}).get("policy_source_kind")), "minimal_default_product_policy_provider")
        self.assertTrue((delivery.get("product_policy") or {}).get("policy_empty"))
        self.assertEqual(((delivery.get("meta") or {}).get("policy_empty_reason")), "MINIMAL_DEFAULT_PRODUCT_POLICY")
        self.assertEqual(
            ((((delivery.get("meta") or {}).get("nav_source_authority") or {}).get("kind"))),
            "delivery_menu_projection",
        )
        self.assertEqual(
            ((((delivery.get("meta") or {}).get("capability_source_authority") or {}).get("kind"))),
            "delivery_capability_projection",
        )

    def test_construction_missing_product_policy_uses_minimal_default(self):
        policy = ProductPolicyService(self.env).get_policy(product_key="construction.standard")
        delivery = DeliveryEngine(self.env).build(
            data={"role_surface": {"role_code": "operator"}},
            product_key="construction.standard",
        )

        self.assertEqual(policy.get("product_key"), "construction.standard")
        self.assertEqual(policy.get("base_product_key"), "construction")
        self.assertEqual(((policy.get("policy_source_authority") or {}).get("kind")), "minimal_default_product_policy_provider")
        self.assertEqual(policy.get("menu_groups") or [], [])
        self.assertEqual(policy.get("scenes") or [], [])
        self.assertEqual(policy.get("capabilities") or [], [])
        self.assertEqual(((delivery.get("product_policy") or {}).get("policy_source_kind")), "minimal_default_product_policy_provider")
        self.assertTrue((delivery.get("product_policy") or {}).get("policy_empty"))

    def test_release_delivery_services_declare_projection_boundaries(self):
        services = (
            (DeliveryEngine, "delivery_engine_projection"),
            (ReleaseApprovalPolicyService, "release_approval_policy_projection"),
            (ReleaseAuditTrailService, "release_audit_trail_projection"),
            (ReleaseOperatorReadModelService, "release_operator_read_model_projection"),
            (ReleaseOperatorSurfaceService, "release_operator_surface_projection"),
        )
        for service_cls, kind in services:
            with self.subTest(service=service_cls.__name__):
                source = service_cls.source_authority_contract()
                self.assertEqual(source.get("kind"), kind)
                self.assertTrue(source.get("projection_only"))
                self.assertTrue(source.get("no_business_fact_authority"))
        approval_source = ReleaseApprovalPolicyService.source_authority_contract()
        self.assertIn("extension_role_resolver", approval_source.get("authorities") or [])
        nav_source = release_navigation_contract_builder.source_authority_contract()
        self.assertEqual(nav_source.get("kind"), "release_navigation_projection")
        self.assertTrue(nav_source.get("no_business_fact_authority"))

    def test_release_navigation_prefers_delivery_engine_payload(self):
        payload = release_navigation_contract_builder.build_release_navigation_contract(
            {
                "delivery_engine_v1": {
                    "contract_version": "v1",
                    "role_code": "operator",
                    "product_key": "platform.standard",
                    "edition_key": "standard",
                    "nav": [{"key": "platform.home", "children": []}],
                }
            }
        )

        self.assertEqual(payload.get("source"), "delivery_engine_v1")
        self.assertFalse((payload.get("meta") or {}).get("fallback_used"))
        self.assertEqual((payload.get("nav") or [])[0].get("key"), "platform.home")

    def test_release_navigation_legacy_fallback_marks_leaf_source(self):
        payload = release_navigation_contract_builder.build_release_navigation_contract({"role_surface": {"role_code": "pm"}})
        root = (payload.get("nav") or [{}])[0]
        groups = root.get("children") or []
        leaves = (groups[0].get("children") if groups else []) or []
        first_meta = (leaves[0].get("meta") if leaves else {}) or {}

        self.assertTrue((payload.get("meta") or {}).get("fallback_used"))
        self.assertEqual((first_meta.get("source_authority") or {}).get("kind"), "legacy_release_navigation_fallback")
        self.assertTrue(first_meta.get("legacy_compatibility"))

    def test_reason_code_registry_separates_legacy_business_reason_provider(self):
        source = reason_codes.source_authority_contract()
        legacy_source = reason_codes.legacy_business_reason_source_authority_contract()
        handler_source = handler_reason_codes.source_authority_contract()

        self.assertEqual(source.get("kind"), "reason_code_metadata_registry")
        self.assertTrue(source.get("no_business_fact_authority"))
        self.assertEqual(handler_source.get("kind"), "reason_code_handler_projection")
        self.assertTrue(handler_source.get("no_business_fact_authority"))
        self.assertTrue(handler_source.get("metadata_proxy_only"))
        self.assertEqual(legacy_source.get("kind"), "legacy_business_reason_metadata_provider")
        self.assertTrue(legacy_source.get("legacy_compatibility"))
        self.assertEqual(reason_codes.legacy_business_reason_meta_mapping(), {})

    def test_contract_governance_declares_legacy_industry_profiles(self):
        source = contract_governance.source_authority_contract()
        legacy_source = contract_governance.legacy_industry_governance_source_authority_contract()
        model_policy_source = contract_governance.legacy_user_surface_model_policy_source_authority_contract()

        self.assertEqual(source.get("kind"), "ui_contract_governance_projection")
        self.assertTrue(source.get("no_business_fact_authority"))
        self.assertEqual(source.get("legacy_industry_governance_profile"), "legacy_industry_governance_profile")
        self.assertEqual(source.get("legacy_user_surface_model_policy"), "legacy_user_surface_model_policy")
        self.assertTrue(source.get("field_label_projection_only"))
        self.assertTrue(source.get("no_partner_classification"))
        self.assertEqual(legacy_source.get("kind"), "legacy_industry_governance_profile")
        self.assertTrue(legacy_source.get("legacy_compatibility"))
        self.assertEqual(model_policy_source.get("kind"), "legacy_user_surface_model_policy")
        self.assertTrue(model_policy_source.get("legacy_compatibility"))

    def test_scene_entry_orchestrators_are_runtime_adapters_not_fact_authorities(self):
        classes = (
            CostTrackingContractOrchestrator,
            PaymentSliceContractOrchestrator,
            ProjectDashboardSceneOrchestrator,
            ProjectExecutionSceneOrchestrator,
            ProjectPlanBootstrapSceneOrchestrator,
            SettlementSliceContractOrchestrator,
        )
        for orchestrator_cls in classes:
            with self.subTest(orchestrator=orchestrator_cls.__name__):
                self.assertEqual(orchestrator_cls.SOURCE_KIND, "scene_entry_runtime_projection_adapter")
                self.assertTrue(orchestrator_cls.NO_BUSINESS_FACT_AUTHORITY)
                self.assertEqual(orchestrator_cls.ADAPTER_LAYER, "industry_orchestration_adapter")

        class DummyBusinessFactService:
            @classmethod
            def source_authority_contract(cls):
                return {
                    "kind": "payment_slice_business_fact_projection",
                    "authorities": ["payment.request", "odoo.orm"],
                    "projection_only": True,
                }

        source = BaseSceneEntryOrchestrator(
            self.env,
            DummyBusinessFactService(),
        ).source_authority_contract()
        self.assertEqual(source.get("kind"), "scene_entry_runtime_projection_adapter")
        self.assertTrue(source.get("projection_only"))
        self.assertTrue(source.get("no_business_fact_authority"))
        self.assertEqual(source.get("legacy_scene_copy_source"), "legacy_scene_entry_copy_projection")
        self.assertNotIn("payment.request", source.get("authorities") or [])
        delegated = source.get("delegated_source_authority") or {}
        self.assertEqual(delegated.get("kind"), "payment_slice_business_fact_projection")
        self.assertIn("payment.request", delegated.get("authorities") or [])
        copy_source = BaseSceneEntryOrchestrator(
            self.env,
            DummyBusinessFactService(),
        ).legacy_scene_copy_source_authority_contract()
        self.assertEqual(copy_source.get("kind"), "legacy_scene_entry_copy_projection")
        self.assertTrue(copy_source.get("legacy_compatibility"))

    def test_industry_orchestration_adapter_does_not_claim_business_fact_authority(self):
        source = industry_orchestration_service_adapter.source_authority_contract()

        self.assertEqual(source.get("kind"), "industry_orchestration_adapter")
        self.assertTrue(source.get("projection_only"))
        self.assertTrue(source.get("no_business_fact_authority"))
        self.assertEqual(source.get("adapter_layer"), "industry_orchestration_adapter")
        self.assertIn("smart_core.extension_hooks", source.get("authorities") or [])
        fallback_source = industry_orchestration_service_adapter._FallbackCostTrackingService.source_authority_contract()
        self.assertEqual(fallback_source.get("kind"), "cost_tracking_missing_extension_degraded_projection")
        self.assertTrue(fallback_source.get("no_business_fact_authority"))
        self.assertNotIn("project.project", fallback_source.get("authorities") or [])

    def test_app_config_models_declare_native_metadata_projection_sources(self):
        self.assertEqual(AppModelConfig.SOURCE_KIND, "odoo_model_fields_projection")
        self.assertIn("ir.model.fields", AppModelConfig.SOURCE_AUTHORITIES)
        self.assertEqual(AppActionConfig.SOURCE_KIND, "odoo_native_action_projection")
        self.assertIn("ir.actions.act_window", AppActionConfig.SOURCE_AUTHORITIES)
        self.assertEqual(AppMenuConfig.SOURCE_KIND, "odoo_native_menu_projection")
        self.assertIn("ir.ui.menu", AppMenuConfig.SOURCE_AUTHORITIES)
        self.assertEqual(AppPermissionConfig.SOURCE_KIND, "odoo_native_permission_projection")
        self.assertIn("ir.rule", AppPermissionConfig.SOURCE_AUTHORITIES)
        self.assertEqual(AppViewConfig.SOURCE_KIND, "odoo_native_view_projection")
        self.assertIn("ir.ui.view", AppViewConfig.SOURCE_AUTHORITIES)
        self.assertEqual(AppValidatorConfig.SOURCE_KIND, "odoo_model_constraint_projection")
        self.assertIn("odoo.sql_constraints", AppValidatorConfig.SOURCE_AUTHORITIES)
        self.assertEqual(AppWorkflowConfig.SOURCE_KIND, "odoo_native_workflow_projection")
        self.assertIn("ir.ui.view:form.buttons", AppWorkflowConfig.SOURCE_AUTHORITIES)
        model_source = self.env["app.model.config"]._source_contract("project.project")
        action_source = self.env["app.action.config"]._source_contract("project.project")
        menu_source = self.env["app.menu.config"]._source_contract("project.project", "web")
        permission_source = self.env["app.permission.config"]._source_contract("project.project", "model")
        view_source = self.env["app.view.config"]._source_contract("project.project", "tree")
        validator_source = self.env["app.validator.config"]._source_contract("project.project")
        workflow_source = self.env["app.workflow.config"]._source_contract("project.project")
        self.assertEqual(workflow_source.get("runtime_authority"), "odoo_model_methods_and_mail_activity")
        for source in (
            model_source,
            action_source,
            menu_source,
            permission_source,
            view_source,
            validator_source,
            workflow_source,
        ):
            self.assertTrue(source.get("no_business_fact_authority"))

    def test_app_menu_config_normalizes_business_scene_keys_to_menu_scene_families(self):
        cfg = self.env["app.menu.config"]

        source = cfg._source_contract("project.project", "projects.list")
        domain = cfg._menu_config_domain(model_name="project.project", scene="projects.list")

        self.assertEqual(source.get("scene"), "pm")
        self.assertIn(("scene", "=", "pm"), domain)

    def test_view_config_projection_identity_is_action_scoped(self):
        action = self.env["ir.actions.act_window"].sudo().create({
            "name": "Scoped Partner Tree",
            "res_model": "res.partner",
            "view_mode": "tree,form",
        })

        generic_identity = self.env["app.view.config"]._projection_identity("res.partner", "tree")
        action_identity = self.env["app.view.config"].with_context(
            contract_action_id=action.id,
        )._projection_identity("res.partner", "tree")

        self.assertEqual(generic_identity.get("projection_scope"), "generic:res.partner:tree")
        self.assertIn(f"action:{action.id}:res.partner:tree", action_identity.get("projection_scope") or "")
        self.assertNotEqual(generic_identity.get("projection_scope"), action_identity.get("projection_scope"))

    def test_view_config_runtime_readonly_projection_does_not_write_cache(self):
        action = self.env["ir.actions.act_window"].sudo().create({
            "name": "Readonly Projection Partner Tree",
            "res_model": "res.partner",
            "view_mode": "tree,form",
        })
        ViewConfig = self.env["app.view.config"].sudo()
        scope = f"action:{action.id}:res.partner:tree:view:0"
        before_count = ViewConfig.search_count([("projection_scope", "=", scope)])

        transient = self.env["app.view.config"].with_context(
            contract_action_id=action.id,
            contract_projection_readonly=True,
        )._generate_from_fields_view_get("res.partner", "tree")

        after_count = ViewConfig.search_count([("projection_scope", "=", scope)])
        self.assertEqual(before_count, after_count)
        self.assertEqual(transient.projection_scope, scope)
        self.assertEqual(transient.version, 0)

    def test_view_config_projection_identity_accepts_explicit_view_id(self):
        view = self.env.ref("base.view_partner_form")
        ViewConfig = self.env["app.view.config"].sudo()

        identity = ViewConfig.with_context(contract_view_id=view.id)._projection_identity("res.partner", "form")

        self.assertEqual(identity.get("action_id"), False)
        self.assertEqual(identity.get("source_view_id"), view.id)
        self.assertEqual(identity.get("projection_scope"), f"view:{view.id}:res.partner:form")

    def test_form_field_policy_view_scope_only_applies_to_matching_view(self):
        view = self.env.ref("base.view_partner_form")
        Policy = self.env["ui.form.field.policy"].sudo()
        policy = Policy.create({
            "model": "res.partner",
            "field_name": "phone",
            "visible": False,
            "view_id": view.id,
        })
        base_contract = {
            "layout": [
                {
                    "type": "sheet",
                    "children": [
                        {
                            "type": "group",
                            "children": [
                                {"type": "field", "name": "name"},
                                {"type": "field", "name": "phone"},
                            ],
                        }
                    ],
                }
            ],
            "field_modifiers": {"phone": {"readonly": False}},
        }

        generic = Policy.apply_to_view_contract(
            dict(base_contract),
            model_name="res.partner",
            view_type="form",
        )
        scoped = Policy.apply_to_view_contract(
            dict(base_contract),
            model_name="res.partner",
            view_type="form",
            view_id=view.id,
        )

        self.assertFalse((generic.get("governance") or {}).get("form_field_policy"))
        scoped_fields = policy._collect_contract_field_nodes(scoped.get("layout") or [])
        self.assertNotIn("phone", scoped_fields)
        governance = (scoped.get("governance") or {}).get("form_field_policy") or {}
        self.assertEqual(governance.get("hidden_fields"), ["phone"])

    def test_form_field_policy_role_group_scope_overrides_global_policy(self):
        group = self.env["res.groups"].sudo().create({"name": "Form Policy Role Scope Probe"})
        Policy = self.env["ui.form.field.policy"].sudo()
        Policy.create({
            "model": "res.partner",
            "field_name": "phone",
            "visible": False,
            "sequence": 10,
        })
        Policy.create({
            "model": "res.partner",
            "field_name": "phone",
            "visible": True,
            "sequence": 20,
            "role_group_ids": [(6, 0, [group.id])],
        })
        base_contract = {
            "layout": [
                {
                    "type": "sheet",
                    "children": [
                        {
                            "type": "group",
                            "children": [
                                {"type": "field", "name": "name"},
                                {"type": "field", "name": "phone", "invisible": True},
                            ],
                        }
                    ],
                }
            ],
            "field_modifiers": {"phone": {"invisible": True}},
        }

        without_group = self.env["ui.form.field.policy"].apply_to_view_contract(
            dict(base_contract),
            model_name="res.partner",
            view_type="form",
        )
        self.assertNotIn("phone", Policy._collect_contract_field_nodes(without_group.get("layout") or []))

        self.env.user.write({"groups_id": [(4, group.id)]})
        with_group = self.env["ui.form.field.policy"].apply_to_view_contract(
            dict(base_contract),
            model_name="res.partner",
            view_type="form",
        )

        fields = Policy._collect_contract_field_nodes(with_group.get("layout") or [])
        self.assertIn("phone", fields)
        self.assertFalse(Policy._contract_node_has_invisible(fields["phone"]))
        governance = (with_group.get("governance") or {}).get("form_field_policy") or {}
        self.assertEqual(governance.get("visible_fields"), ["phone"])
        self.assertTrue(governance.get("role_group_scoped"))

    def test_form_field_policy_appends_missing_visible_fields_by_group_title(self):
        Policy = self.env["ui.form.field.policy"].sudo()
        Policy.create({
            "model": "res.partner",
            "field_name": "phone",
            "visible": True,
            "group_title": "联系字段",
            "sequence": 10,
        })
        Policy.create({
            "model": "res.partner",
            "field_name": "email",
            "visible": True,
            "group_title": "扩展字段",
            "sequence": 20,
        })
        contract = {
            "layout": [
                {
                    "type": "sheet",
                    "children": [
                        {
                            "type": "group",
                            "children": [{"type": "field", "name": "name"}],
                        }
                    ],
                }
            ],
        }

        result = Policy.apply_to_view_contract(contract, model_name="res.partner", view_type="form")

        sheet = result["layout"][0]
        appended = [
            node for node in sheet.get("children", [])
            if str(node.get("name") or "").startswith("business_config_field_policy_group_")
        ]
        self.assertEqual([node.get("string") for node in appended], ["联系字段", "扩展字段"])
        self.assertEqual([[child.get("name") for child in node.get("children", [])] for node in appended], [["phone"], ["email"]])

    def test_view_orchestrator_consumes_business_config_contract_for_form(self):
        self.env["ui.business.config.contract"].sudo().create({
            "name": "Partner Form Orchestration",
            "model": "res.partner",
            "view_type": "form",
            "status": "published",
            "contract_json": {
                "view_orchestration": {
                    "views": {
                        "form": {
                            "fields": [
                                {"name": "email", "label": "Email Alias", "sequence": 5},
                                {"name": "phone", "visible": False, "sequence": 10},
                            ],
                        }
                    }
                }
            },
        })
        contract = {
            "layout": [
                {
                    "type": "sheet",
                    "children": [
                        {
                            "type": "group",
                            "children": [
                                {"type": "field", "name": "name"},
                                {"type": "field", "name": "phone"},
                            ],
                        }
                    ],
                }
            ],
        }

        result = ViewOrchestrator(self.env).compose(contract, model_name="res.partner", view_type="form")

        fields = self.env["ui.form.field.policy"]._collect_contract_field_nodes(result.get("layout") or [])
        self.assertNotIn("phone", fields)
        self.assertIn("email", fields)
        self.assertEqual(fields["email"].get("label"), "Email Alias")
        governance = (result.get("governance") or {}).get("view_orchestration") or {}
        self.assertEqual(governance.get("owner_layer"), "business_view_orchestration")
        self.assertTrue(governance.get("business_config_contracts"))

    def test_view_orchestrator_consumes_business_config_contract_for_list_columns(self):
        self.env["ui.business.config.contract"].sudo().create({
            "name": "Partner List Orchestration",
            "model": "res.partner",
            "view_type": "tree",
            "status": "published",
            "contract_json": {
                "view_orchestration": {
                    "views": {
                        "tree": {
                            "columns": [
                                {"name": "email", "label": "Email Alias", "sequence": 5},
                                {"name": "name", "sequence": 10},
                                {"name": "phone", "visible": False, "sequence": 20},
                            ],
                        }
                    }
                }
            },
        })
        contract = {
            "columns": ["name", "phone", "email"],
            "columns_schema": [
                {"name": "name", "label": "Name"},
                {"name": "phone", "label": "Phone"},
                {"name": "email", "label": "Email"},
            ],
        }

        result = ViewOrchestrator(self.env).compose(contract, model_name="res.partner", view_type="tree")

        self.assertEqual(result.get("columns"), ["email", "name"])
        self.assertEqual([row.get("name") for row in result.get("columns_schema") or []], ["email", "name"])
        self.assertEqual((result.get("columns_schema") or [])[0].get("label"), "Email Alias")

    def test_form_field_policy_revalidates_action_and_view_scope_on_write(self):
        Policy = self.env["ui.form.field.policy"].sudo()
        policy = Policy.create({
            "model": "res.partner",
            "field_name": "phone",
            "visible": False,
        })
        other_action = self.env["ir.actions.act_window"].sudo().create({
            "name": "Project Action Scope Probe",
            "res_model": "project.project",
            "view_mode": "tree,form",
        })
        other_view = self.env["ir.ui.view"].sudo().search([
            ("model", "!=", "res.partner"),
            ("type", "=", "form"),
        ], limit=1)

        with self.assertRaises(ValidationError):
            policy.write({"action_id": other_action.id})
        if other_view:
            with self.assertRaises(ValidationError):
                policy.write({"view_id": other_view.id})

    def test_form_field_policy_onchange_action_sets_business_object(self):
        action = self.env["ir.actions.act_window"].sudo().create({
            "name": "Customer Field Config Probe",
            "res_model": "res.partner",
            "view_mode": "tree,form",
        })

        policy = self.env["ui.form.field.policy"].new({"action_id": action.id})
        policy._onchange_action_id()

        self.assertEqual(policy.model, "res.partner")
        self.assertEqual(policy.model_id.model, "res.partner")

    def test_form_contract_declares_current_page_field_settings_action(self):
        group = self.env.ref("smart_construction_core.group_sc_cap_business_config_admin")
        self.env.user.write({"groups_id": [(4, group.id)]})
        action = self.env["ir.actions.act_window"].sudo().create({
            "name": "Customer Current Form Settings Probe",
            "res_model": "res.partner",
            "view_mode": "tree,form",
        })
        assembler = PageAssembler(self.env, self.env["ir.model"].sudo().env)
        data = {
            "buttons": [],
            "toolbar": {"header": [], "sidebar": [], "footer": []},
            "views": {"form": {}},
            "fields": {"name": {"string": "名称", "type": "char"}},
            "render_profile": "edit",
        }

        assembler._inject_current_form_settings_action(
            data,
            model_name="res.partner",
            action_id=action.id,
            render_profile="edit",
        )

        actions = [row for row in data.get("toolbar", {}).get("header", []) if row.get("key") == "current_form_field_settings"]
        self.assertEqual(len(actions), 1)
        settings = actions[0]
        self.assertEqual(settings.get("kind"), "client")
        self.assertEqual(settings.get("intent"), "ui.local_mode")
        self.assertEqual(settings.get("label"), "表单设置")
        self.assertEqual((settings.get("target") or {}).get("mode"), "form_field_configuration")
        governance = data.get("governance", {}).get("current_form_field_settings") or {}
        self.assertEqual(governance.get("action_id"), action.id)
        self.assertEqual(governance.get("model"), "res.partner")
        self.assertEqual(governance.get("model_label"), "Contact")
        action_groups = data.get("action_groups") or []
        field_config_group = next((row for row in action_groups if row.get("key") == "current_form_field_configuration"), {})
        self.assertTrue(field_config_group)
        self.assertTrue(any(row.get("intent") == "ui.form_custom_field.create" for row in field_config_group.get("actions") or []))
        low_code_config = field_config_group.get("low_code_config") or {}
        self.assertEqual(low_code_config.get("config_source"), "ui.business.config.contract")
        self.assertEqual(low_code_config.get("legacy_overlay"), "ui.form.field.policy")
        source_authority = field_config_group.get("source_authority") or {}
        self.assertEqual(source_authority.get("owner_layer"), "business_view_orchestration")
        self.assertIn("ui.business.config.contract", source_authority.get("authorities") or [])

        result = UiContractV2Handler(self.env, su_env=self.env["ir.model"].sudo().env).handle({
            "model": "res.partner",
            "view_type": "form",
            "action_id": action.id,
            "render_profile": "edit",
        })
        envelope = result.to_legacy_dict() if hasattr(result, "to_legacy_dict") else result
        self.assertTrue(envelope.get("ok", True))
        action_rows = envelope["data"]["actionContract"]["actionRuleList"]
        settings_rows = [
            row for row in action_rows
            if row.get("actionKey") == "current_form_field_settings"
        ]
        self.assertEqual(len(settings_rows), 1)
        v2_action = settings_rows[0]
        self.assertEqual(v2_action.get("sourceWidgetId"), "page.header")
        self.assertEqual(v2_action.get("targetScope"), "page")
        self.assertEqual(v2_action.get("triggerType"), "click")
        self.assertEqual(v2_action.get("intent"), "ui.local_mode")
        self.assertEqual((v2_action.get("target") or {}).get("mode"), "form_field_configuration")
        dependency_graph = envelope["data"]["actionContract"]["dependencyGraph"]
        self.assertIn(v2_action.get("actionId"), dependency_graph.get("page.header") or [])
        self.assertTrue(any(
            row.get("sourceWidgetId") == "mode.form_field_configuration"
            and row.get("intent") == "ui.form_custom_field.create"
            for row in action_rows
        ))
        self.assertTrue(any(
            row.get("sourceWidgetId") == "field.name"
            and row.get("intent") == "ui.form_field_policy.set"
            for row in action_rows
        ))

    def test_custom_field_wizard_action_first_flow_autogenerates_field_name(self):
        action = self.env["ir.actions.act_window"].sudo().create({
            "name": "Customer Custom Field Probe",
            "res_model": "res.partner",
            "view_mode": "tree,form",
        })

        wizard = self.env["ui.form.custom.field.wizard"].new({
            "action_id": action.id,
            "label": "项目联系人",
            "ttype": "char",
        })
        wizard._onchange_action_id()
        wizard._onchange_label()

        self.assertEqual(wizard.model_id.model, "res.partner")
        self.assertTrue(str(wizard.field_name or "").startswith("x_custom_field"))

    def test_ui_overlay_and_asset_models_do_not_claim_business_fact_authority(self):
        self.assertEqual(AppViewFragment.SOURCE_KIND, "ui_contract_fragment_overlay")
        self.assertEqual(AppViewVariant.SOURCE_KIND, "ui_contract_variant_overlay")
        source = self.env["sc.ui.base.contract.asset"].source_authority_contract()
        self.assertEqual(UiBaseContractAsset.SOURCE_KIND, "ui_base_contract_asset_cache")
        self.assertTrue(source.get("cache_only"))
        self.assertTrue(source.get("rebuildable"))
        self.assertTrue(source.get("no_business_fact_authority"))

    def test_startup_ui_permission_and_catalog_handlers_declare_projection_sources(self):
        self.assertEqual(SystemInitHandler.SOURCE_KIND, "odoo_native_startup_surface_projection")
        self.assertIn("ir.ui.menu", SystemInitHandler.SOURCE_AUTHORITIES)
        self.assertEqual(UiContractHandler.SOURCE_KIND, "odoo_native_ui_contract_projection")
        self.assertIn("ir.ui.view", UiContractHandler.SOURCE_AUTHORITIES)
        self.assertIn("ir.actions.act_window", UiContractHandler.SOURCE_AUTHORITIES)
        self.assertEqual(UiContractV2Handler.source_authority_contract().get("kind"), "unified_page_contract_v2")
        self.assertTrue(UiContractV2Handler.source_authority_contract().get("no_business_fact_authority"))
        self.assertEqual(PermissionCheckHandler.SOURCE_KIND, "odoo_native_permission_projection")
        self.assertIn("sc.capability", PermissionCheckHandler.SOURCE_AUTHORITIES)
        permission_source = PermissionCheckHandler.source_authority_contract()
        self.assertEqual(permission_source.get("kind"), "odoo_native_permission_projection")
        self.assertTrue(permission_source.get("no_business_fact_authority"))
        intent_permission_source = intent_permission.source_authority_contract()
        self.assertEqual(intent_permission_source.get("kind"), "odoo_native_permission_projection")
        self.assertTrue(intent_permission_source.get("no_business_fact_authority"))
        menu_fact_source = MenuFactService.source_authority_contract()
        self.assertEqual(menu_fact_source.get("kind"), "odoo_menu_fact_projection")
        self.assertIn("ir.ui.menu", menu_fact_source.get("authorities") or [])
        self.assertTrue(menu_fact_source.get("no_business_fact_authority"))
        delivery_menu_source = MenuService.source_authority_contract()
        self.assertEqual(delivery_menu_source.get("kind"), "delivery_menu_projection")
        self.assertIn("odoo_menu_fact_projection", delivery_menu_source.get("authorities") or [])
        self.assertTrue(delivery_menu_source.get("no_business_fact_authority"))
        self.assertEqual(ProjectContextSearchHandler.SOURCE_KIND, "record_context_projection")
        self.assertIn("record_context_model", ProjectContextSearchHandler.SOURCE_AUTHORITIES)
        project_context_source = project_context.source_authority_contract()
        self.assertEqual(project_context_source.get("kind"), "record_context_projection")
        self.assertTrue(project_context_source.get("no_business_fact_authority"))
        self.assertEqual(project_context_source.get("legacy_default_model"), "project.project")
        scope_source = project_context.legacy_project_scope_source_authority_contract()
        self.assertEqual(scope_source.get("kind"), "legacy_project_scope_adapter")
        self.assertTrue(scope_source.get("no_business_fact_authority"))
        self.assertEqual(MetaDescribeHandler.SOURCE_KIND, "odoo_fields_get_projection")
        self.assertEqual(MetaIntentCatalogHandler.SOURCE_KIND, "intent_delivery_catalog_projection")
        self.assertEqual(MetaDescribeHandler.source_authority_contract().get("kind"), "odoo_fields_get_projection")
        self.assertTrue(MetaDescribeHandler.source_authority_contract().get("no_business_fact_authority"))
        self.assertEqual(LoadMetadataHandler.source_authority_contract().get("kind"), "odoo_fields_get_projection")
        self.assertTrue(LoadMetadataHandler.source_authority_contract().get("no_business_fact_authority"))
        self.assertEqual(MetaIntentCatalogHandler.source_authority_contract().get("kind"), "intent_delivery_catalog_projection")
        self.assertTrue(MetaIntentCatalogHandler.source_authority_contract().get("no_business_fact_authority"))
        self.assertEqual(IntentSurfaceBuilder.source_authority_contract().get("kind"), "intent_surface_projection")
        self.assertTrue(IntentSurfaceBuilder.source_authority_contract().get("no_business_fact_authority"))
        self.assertEqual(SceneHealthHandler.SOURCE_KIND, "scene_delivery_health_projection")
        self.assertEqual(ScenePackagesInstalledHandler.SOURCE_KIND, "scene_package_registry_projection")
        menu_source = platform_menu_api.source_authority_contract()
        self.assertEqual(menu_source.get("kind"), "platform_menu_delivery_projection")
        self.assertTrue(menu_source.get("no_business_fact_authority"))
        self.assertIn("extension_business_config_role_resolver", menu_source.get("authorities") or [])

    def test_menu_runtime_default_whitelist_includes_form_field_governance_models(self):
        patterns = set(self.env["app.menu.config"].DEFAULT_MODEL_WHITELIST_PATTERNS)

        self.assertIn(r"^ui\.form\.field\.policy$", patterns)
        self.assertIn(r"^ui\.form\.custom\.field\.wizard$", patterns)

    def test_workspace_home_startup_surface_does_not_claim_business_fact_authority(self):
        source = workspace_home_contract_builder.source_authority_contract()
        provider_source = workspace_home_data_provider.source_authority_contract()

        self.assertEqual(source.get("kind"), "workspace_home_startup_surface_projection")
        self.assertTrue(source.get("projection_only"))
        self.assertTrue(source.get("no_business_fact_authority"))
        self.assertIn("extension_fact_contributions", source.get("authorities") or [])
        self.assertEqual(source.get("legacy_workspace_keyword_policy"), "legacy_workspace_keyword_policy_projection")
        keyword_source = workspace_home_contract_builder.legacy_workspace_keyword_policy_source_authority_contract()
        self.assertEqual(keyword_source.get("kind"), "legacy_workspace_keyword_policy_projection")
        self.assertTrue(keyword_source.get("legacy_compatibility"))
        self.assertTrue(keyword_source.get("no_business_fact_authority"))
        self.assertEqual(provider_source.get("kind"), "workspace_home_industry_content_provider_adapter")
        self.assertTrue(provider_source.get("no_business_fact_authority"))

    def test_system_init_delivery_identity_is_parameterized_not_hardcoded_to_construction(self):
        identity = _resolve_startup_delivery_identity(
            self.env,
            {
                "delivery_product_key": "platform.standard",
                "delivery_base_product_key": "platform",
                "delivery_edition_key": "standard",
            },
        )

        self.assertEqual(identity.get("product_key"), "platform.standard")
        self.assertEqual(identity.get("base_product_key"), "platform")
        self.assertEqual(identity.get("edition_key"), "standard")
        self.assertEqual(identity.get("source"), "params")
        self.assertTrue(identity.get("no_business_fact_authority"))

    def test_system_init_industry_extension_modules_are_configurable(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "smart_core.industry_extension_modules",
            "vertical_alpha, vertical_beta",
        )

        self.assertEqual(_resolve_industry_extension_modules(self.env), ["vertical_alpha", "vertical_beta"])

    def test_auth_search_preference_and_gateway_sources_are_not_business_facts(self):
        self.assertEqual(LoginHandler.SOURCE_KIND, "odoo_auth_session_proxy")
        self.assertIn("res.users", LoginHandler.SOURCE_AUTHORITIES)
        self.assertEqual(LogoutHandler.SOURCE_KIND, "odoo_auth_session_proxy")
        self.assertEqual(SessionBootstrapHandler.SOURCE_KIND, "dev_test_auth_bootstrap_proxy")
        self.assertTrue(SessionBootstrapHandler.source_authority_contract().get("dev_test_only"))
        self.assertTrue(SessionBootstrapHandler.source_authority_contract().get("no_business_fact_authority"))
        self.assertEqual(SearchFavoriteSetHandler.SOURCE_KIND, "odoo_filter_write_proxy")
        self.assertIn("ir.filters", SearchFavoriteSetHandler.SOURCE_AUTHORITIES)
        self.assertTrue(LoginHandler.source_authority_contract().get("no_business_fact_authority"))
        self.assertTrue(LogoutHandler.source_authority_contract().get("no_business_fact_authority"))
        self.assertTrue(SearchFavoriteSetHandler.source_authority_contract().get("write_proxy"))
        self.assertTrue(SearchFavoriteSetHandler.source_authority_contract().get("no_business_fact_authority"))
        self.assertEqual(UserViewPreferenceGetHandler.SOURCE_KIND, "ui_only_user_preference")
        self.assertEqual(UserViewPreferenceSetHandler.SOURCE_KIND, "ui_only_user_preference")
        self.assertFalse(UserViewPreferenceGetHandler.source_authority_contract().get("write_proxy"))
        self.assertTrue(UserViewPreferenceSetHandler.source_authority_contract().get("write_proxy"))
        self.assertTrue(UserViewPreferenceSetHandler.source_authority_contract().get("no_business_fact_authority"))
        self.assertEqual(ScUserViewPreference.SOURCE_KIND, "ui_only_user_preference")
        self.assertTrue(self.env["sc.user.view.preference"].source_authority_contract().get("no_business_fact_authority"))
        self.assertEqual(TerminalShellV2Handler.source_authority_contract().get("kind"), "terminal_shell_contract_v2")
        self.assertTrue(TerminalShellV2Handler.source_authority_contract().get("no_business_fact_authority"))
        self.assertEqual(AppActionGateway.SOURCE_KIND, "odoo_runtime_action_gateway")
        self.assertIn("odoo.model.method", AppActionGateway.SOURCE_AUTHORITIES)
        self.assertTrue(self.env["app.action.gateway"].source_authority_contract().get("no_business_fact_authority"))
        self.assertEqual(ContractSchemaMixin.SOURCE_KIND, "ui_contract_sanitizer")
        self.assertTrue(self.env["contract.schema.mixin"].source_authority_contract().get("no_business_fact_authority"))
        self.assertEqual(IrUiViewAssetTrigger.SOURCE_KIND, "ui_base_contract_asset_invalidation_trigger")
        self.assertTrue(self.env["ir.ui.view"].source_authority_contract().get("no_business_fact_authority"))
        self.assertEqual(VersionedDataHandlerV21.SOURCE_KIND, "test_versioned_handler_projection")
        self.assertTrue(VersionedDataHandlerV21.source_authority_contract().get("no_business_fact_authority"))

    def test_runtime_infrastructure_sources_are_not_business_facts(self):
        sources = (
            extension_loader.source_authority_contract(),
            extension_hooks.source_authority_contract(),
            SceneChannelPolicy.source_authority_contract(),
            ui_base_contract_asset_event_queue.source_authority_contract(),
            ui_base_contract_asset_repository.source_authority_contract(),
            system_init_dictionary_data_helper.source_authority_contract(),
        )
        expected_kinds = {
            "smart_core_extension_loader",
            "smart_core_extension_hook_resolver",
            "scene_channel_policy_projection",
            "ui_base_contract_asset_event_queue",
            "ui_base_contract_asset_repository",
            "system_init_dictionary_data_projection",
        }
        self.assertEqual({source.get("kind") for source in sources}, expected_kinds)
        for source in sources:
            self.assertTrue(source.get("no_business_fact_authority"))
        self.assertTrue(ui_base_contract_asset_event_queue.source_authority_contract().get("write_proxy"))
        self.assertTrue(ui_base_contract_asset_repository.source_authority_contract().get("write_proxy"))

    def test_system_init_auth_menu_target_release_and_ui_overlay_sources_are_not_business_facts(self):
        sources = (
            SystemInitComponentsFactory.source_authority_contract(),
            SystemInitRuntimeContext.source_authority_contract(),
            SystemInitSurfaceContext.source_authority_contract(),
            SystemInitSceneRuntimeSurfaceContext.source_authority_contract(),
            SystemInitDiagnosticsHelper.source_authority_contract(),
            SystemInitIdentityPayload.source_authority_contract(),
            SystemInitNavRequestBuilder.source_authority_contract(),
            SystemInitPreloadBuilder.source_authority_contract(),
            SystemInitResponseMetaBuilder.source_authority_contract(),
            SystemInitSurfaceBuilder.source_authority_contract(),
            SystemInitSceneRuntimeSurfaceBuilder.source_authority_contract(),
            RequestDiagnosticsCollector.source_authority_contract(),
            smart_auth.source_authority_contract(),
            MenuTargetInterpreterService.source_authority_contract(),
            release_operator_contract_registry.source_authority_contract(),
            release_operator_contract_versions.source_authority_contract(),
            self.env["ui.dynamic.config"].source_authority_contract(),
            command_registry.source_authority_contract(),
            delivery_capability_entry_defaults.source_authority_contract(),
            delivery_menu_defaults.source_authority_contract(),
            scene_ready_contract_builder.source_authority_contract(),
        )
        expected_kinds = {
            "system_init_runtime_components_factory",
            "system_init_runtime_context_carrier",
            "system_init_surface_context_carrier",
            "system_init_scene_runtime_surface_context_carrier",
            "system_init_diagnostics_projection",
            "system_init_identity_payload_projection",
            "system_init_nav_request_projection",
            "system_init_preload_contract_projection",
            "system_init_response_meta_projection",
            "system_init_surface_projection_builder",
            "system_init_scene_runtime_surface_projection_builder",
            "request_diagnostics_projection",
            "jwt_auth_session_proxy",
            "menu_target_interpreter_projection",
            "release_operator_contract_registry_projection",
            "release_operator_contract_version_registry",
            "ui_dynamic_config_overlay",
            "legacy_command_registry_projection",
            "delivery_capability_entry_default_projection",
            "delivery_menu_default_projection",
            "scene_ready_contract_projection",
        }
        self.assertEqual({source.get("kind") for source in sources}, expected_kinds)
        for source in sources:
            self.assertTrue(source.get("no_business_fact_authority"))
        self.assertTrue(smart_auth.source_authority_contract().get("write_proxy"))
        self.assertTrue(SystemInitIdentityPayload.source_authority_contract().get("identity_surface_only"))
        self.assertTrue(SystemInitResponseMetaBuilder.source_authority_contract().get("response_envelope_only"))
        self.assertTrue(SystemInitSceneRuntimeSurfaceBuilder.source_authority_contract().get("scene_runtime_surface_only"))
        self.assertTrue(RequestDiagnosticsCollector.source_authority_contract().get("diagnostics_only"))
        self.assertTrue(MenuTargetInterpreterService.source_authority_contract().get("facts_remain_unchanged"))
        self.assertTrue(release_operator_contract_registry.source_authority_contract().get("contract_metadata_only"))
        self.assertEqual(UIDynamicConfig.SOURCE_KIND, "ui_dynamic_config_overlay")
        self.assertTrue(self.env["ui.dynamic.config"].source_authority_contract().get("ui_overlay_only"))
        self.assertTrue(delivery_menu_defaults.source_authority_contract().get("synthetic_navigation_only"))
        self.assertTrue(delivery_capability_entry_defaults.source_authority_contract().get("capability_entry_default_only"))
        self.assertTrue(scene_ready_contract_builder.source_authority_contract().get("scene_runtime_contract_only"))

    def test_contract_controller_handler_registry_view_mixins_and_static_guards_are_not_business_facts(self):
        tree_form = importlib.import_module(
            "odoo.addons.smart_core.app_config_engine.services.view_Parser.parsers Tree Form"
        )
        kanban_pivot_graph = importlib.import_module(
            "odoo.addons.smart_core.app_config_engine.services.view_Parser.parsers Kanban Pivot Graph"
        )
        calendar_gantt_activity = importlib.import_module(
            "odoo.addons.smart_core.app_config_engine.services.view_Parser.parsers_Calendar_Gantt Activity"
        )
        sources = (
            contract_api.source_authority_contract(),
            contract_api.SmartCoreContractController.source_authority_contract(),
            handler_registry_module.source_authority_contract(),
            tree_form._TreeFormParserMixin.source_authority_contract(),
            kanban_pivot_graph._KanbanPivotGraphParserMixin.source_authority_contract(),
            calendar_gantt_activity._CalendarGanttActivitySearchParserMixin.source_authority_contract(),
            intent_acl_mode_guard.source_authority_contract(),
            intent_write_guard.source_authority_contract(),
        )
        expected_kinds = {
            "app_config_contract_http_controller",
            "intent_handler_registry_projection",
            "odoo_tree_form_view_parser_mixin",
            "odoo_kanban_pivot_graph_view_parser_mixin",
            "odoo_calendar_gantt_activity_search_view_parser_mixin",
            "intent_acl_mode_static_guard",
            "intent_write_static_guard",
        }
        self.assertEqual({source.get("kind") for source in sources}, expected_kinds)
        for source in sources:
            self.assertTrue(source.get("no_business_fact_authority"))
        self.assertTrue(contract_api.source_authority_contract().get("http_controller_only"))
        self.assertTrue(handler_registry_module.source_authority_contract().get("runtime_registry_only"))
        self.assertTrue(tree_form._TreeFormParserMixin.source_authority_contract().get("view_parser_mixin_only"))
        self.assertTrue(intent_write_guard.source_authority_contract().get("static_guard_only"))

    def test_app_config_service_layer_sources_are_not_business_facts(self):
        sources = (
            ContractService.source_authority_contract(),
            ActionDispatcher.source_authority_contract(),
            MenuDispatcher.source_authority_contract(),
            NavDispatcher.source_authority_contract(),
            ActionResolver.source_authority_contract(),
            PageAssembler.source_authority_contract(),
            ClientUrlReportAssembler.source_authority_contract(),
        )
        expected_kinds = {
            "app_config_contract_service_projection",
            "app_config_action_dispatch_proxy",
            "app_config_menu_dispatch_projection",
            "app_config_nav_dispatch_projection",
            "odoo_action_resolution_projection",
            "app_config_page_contract_projection",
            "client_url_report_contract_projection",
        }
        self.assertEqual({source.get("kind") for source in sources}, expected_kinds)
        for source in sources:
            self.assertTrue(source.get("no_business_fact_authority"))
        self.assertTrue(ActionDispatcher.source_authority_contract().get("write_proxy"))
        self.assertTrue(ActionResolver.source_authority_contract().get("write_proxy"))

    def test_view_parse_and_contract_utility_sources_are_not_business_facts(self):
        sources = (
            NativeParseService.source_authority_contract(),
            ParseFallbackService.source_authority_contract(),
            ContractGovernanceFilterService.source_authority_contract(),
            ContractNormalizer.source_authority_contract(),
            view_parser_base.source_authority_contract(),
            self.env["app.view.parser"].source_authority_contract(),
            contract_http_utils.source_authority_contract(),
            contract_misc_utils.source_authority_contract(),
            contract_payload_utils.source_authority_contract(),
            contract_view_utils.source_authority_contract(),
            BaseViewParser.source_authority_contract(),
            FormViewParser.source_authority_contract(),
            ViewDispatcher.source_authority_contract(),
            UniversalViewSemanticParser.source_authority_contract(),
        )
        expected_kinds = {
            "odoo_native_view_parse_coordinator",
            "odoo_view_parse_fallback_coordinator",
            "ui_contract_runtime_governance_filter",
            "ui_contract_shape_normalizer",
            "odoo_view_parser_base_projection",
            "odoo_view_contract_parser_projection",
            "http_json_payload_reader",
            "contract_utility_projection",
            "contract_request_payload_normalizer",
            "odoo_tree_view_column_projection",
            "legacy_view_parser_base_projection",
            "legacy_form_view_parser_projection",
            "legacy_view_dispatch_projection",
            "legacy_universal_view_semantic_projection",
        }
        self.assertEqual({source.get("kind") for source in sources}, expected_kinds)
        for source in sources:
            self.assertTrue(source.get("no_business_fact_authority"))

    def test_semantic_bridge_scene_runtime_and_identity_sources_are_not_business_facts(self):
        sources = (
            orchestration_semantics.source_authority_contract(),
            page_contract_parser_semantic_bridge.source_authority_contract(),
            page_contract_semantic_orchestration_bridge.source_authority_contract(),
            released_scene_semantic_surface_bridge.source_authority_contract(),
            runtime_page_parser_semantic_bridge.source_authority_contract(),
            runtime_page_semantic_orchestration_bridge.source_authority_contract(),
            scene_contract_parser_semantic_bridge.source_authority_contract(),
            scene_contract_semantic_orchestration_bridge.source_authority_contract(),
            scene_governance_payload_builder.source_authority_contract(),
            scene_ready_entry_semantic_bridge.source_authority_contract(),
            scene_ready_parser_semantic_bridge.source_authority_contract(),
            scene_ready_semantic_orchestration_bridge.source_authority_contract(),
            system_init_extension_fact_merger.source_authority_contract(),
            system_init_scene_runtime_semantic_bridge.source_authority_contract(),
            SceneDiagnosticsBuilder.source_authority_contract(),
            SceneRuntimeOrchestrator.source_authority_contract(),
            SceneDriftEngine.source_authority_contract(),
            IdentityResolver.source_authority_contract(),
        )
        expected_kinds = {
            "ui_orchestration_semantics_registry",
            "page_contract_parser_semantic_bridge",
            "page_contract_semantic_orchestration_bridge",
            "released_scene_semantic_surface_bridge",
            "runtime_page_parser_semantic_bridge",
            "runtime_page_semantic_orchestration_bridge",
            "scene_contract_parser_semantic_bridge",
            "scene_contract_semantic_orchestration_bridge",
            "scene_governance_payload_projection",
            "scene_ready_entry_semantic_bridge",
            "scene_ready_parser_semantic_bridge",
            "scene_ready_semantic_orchestration_bridge",
            "system_init_extension_fact_contribution_merger",
            "system_init_scene_runtime_semantic_bridge",
            "scene_diagnostics_projection",
            "scene_runtime_orchestration_projection",
            "scene_drift_health_projection",
            "role_identity_surface_projection",
        }
        self.assertEqual({source.get("kind") for source in sources}, expected_kinds)
        for source in sources:
            self.assertTrue(source.get("no_business_fact_authority"))
        self.assertTrue(system_init_extension_fact_merger.source_authority_contract().get("delegates_business_fact_authority"))

    def test_intent_runtime_envelope_sources_are_not_business_facts(self):
        sources = (
            intent_dispatcher.source_authority_contract(),
            BaseIntentHandler.source_authority_contract(),
            RequestContext.source_authority_contract(),
            core_exceptions.source_authority_contract(),
            hash_utils.source_authority_contract(),
            IntentExecutionResult.source_authority_contract(),
            intent_router.source_authority_contract(),
            BaseMiddleware.source_authority_contract(),
            middlewares.source_authority_contract(),
            trace.source_authority_contract(),
            idempotency.source_authority_contract(),
            response_builder.source_authority_contract(),
        )
        expected_kinds = {
            "http_intent_dispatch_controller",
            "intent_handler_runtime_base",
            "http_request_context_projection",
            "intent_error_envelope_registry",
            "stable_hash_utility",
            "intent_execution_result_envelope",
            "intent_router_runtime_dispatch",
            "intent_middleware_runtime_pipeline",
            "request_trace_id_projection",
            "idempotency_audit_replay_projection",
            "http_json_response_builder",
        }
        self.assertEqual({source.get("kind") for source in sources}, expected_kinds)
        for source in sources:
            self.assertTrue(source.get("no_business_fact_authority"))
        self.assertTrue(intent_dispatcher.source_authority_contract().get("write_proxy"))
        self.assertTrue(intent_router.source_authority_contract().get("write_proxy"))
        self.assertTrue(BaseIntentHandler.source_authority_contract().get("write_proxy"))

    def test_navigation_scene_and_unified_page_sources_are_not_business_facts(self):
        sources = (
            NavTreeCleaner.source_authority_contract(),
            OdooNavAdapter.source_authority_contract(),
            action_target_schema.source_authority_contract(),
            native_view_contract_projection.source_authority_contract(),
            page_orchestration_data_provider.source_authority_contract(),
            scene_dsl_compiler.source_authority_contract(),
            scene_merge_resolver.source_authority_contract(),
            scene_nav_contract_builder.source_authority_contract(),
            SceneNormalizer.source_authority_contract(),
            CapabilitySurfaceEngine.source_authority_contract(),
            unified_page_contract_lite_adapter.source_authority_contract(),
            unified_page_contract_lite_patch_normalizer.source_authority_contract(),
            unified_page_contract_lite_preview.source_authority_contract(),
            unified_page_contract_lite_source_normalizer.source_authority_contract(),
            unified_page_contract_v2_action.source_authority_contract(),
            unified_page_contract_v2_assembler.source_authority_contract(),
            unified_page_contract_v2_client.source_authority_contract(),
            unified_page_contract_v2_data.source_authority_contract(),
            unified_page_contract_v2_runtime.source_authority_contract(),
            unified_page_contract_v2_status.source_authority_contract(),
            ui_base_contract_adapter.source_authority_contract(),
            ui_base_contract_asset_producer.source_authority_contract(),
            ui_base_contract_canonicalizer.source_authority_contract(),
            ContractAssembler.source_authority_contract(),
        )
        expected_kinds = {
            "nav_tree_shape_cleaner",
            "odoo_navigation_scene_projection_adapter",
            "ui_action_target_schema_projection",
            "native_view_primary_contract_projection",
            "page_orchestration_static_data_provider",
            "scene_dsl_contract_compiler_projection",
            "scene_contract_merge_resolver_projection",
            "scene_navigation_contract_projection",
            "scene_registry_normalization_projection",
            "capability_surface_summary_projection",
            "unified_page_contract_lite_projection",
            "unified_page_contract_lite_patch_normalizer",
            "unified_page_contract_lite_preview_projection",
            "unified_page_contract_lite_source_normalizer",
            "unified_page_contract_v2_action_projection",
            "unified_page_contract_v2_assembler_projection",
            "unified_page_contract_v2_client_projection",
            "unified_page_contract_v2_data_projection",
            "unified_page_contract_v2_runtime_projection",
            "unified_page_contract_v2_status_projection",
            "ui_base_contract_adapter_projection",
            "ui_base_contract_asset_producer_projection",
            "ui_base_contract_canonicalizer_projection",
            "system_init_contract_meta_assembler",
        }
        self.assertEqual({source.get("kind") for source in sources}, expected_kinds)
        for source in sources:
            self.assertTrue(source.get("no_business_fact_authority"))
        self.assertTrue(ui_base_contract_asset_producer.source_authority_contract().get("write_proxy"))
        self.assertTrue(ui_base_contract_asset_producer.source_authority_contract().get("fallback_model_is_ui_placeholder"))

    def test_registered_handlers_declare_source_authority(self):
        missing = []
        for intent, handler_cls in sorted(HANDLER_REGISTRY.items()):
            source_kind = str(getattr(handler_cls, "SOURCE_KIND", "") or "").strip()
            source_authority = str(getattr(handler_cls, "SOURCE_AUTHORITY", "") or "").strip()
            source_authorities = getattr(handler_cls, "SOURCE_AUTHORITIES", None)
            has_authorities = isinstance(source_authorities, (list, tuple)) and bool(source_authorities)
            if not source_kind and not source_authority:
                missing.append(f"{intent}:{handler_cls.__module__}.{handler_cls.__name__}:source_kind")
            if not source_authority and not has_authorities:
                missing.append(f"{intent}:{handler_cls.__module__}.{handler_cls.__name__}:source_authority")

        self.assertFalse(missing, "registered handlers missing source authority: %s" % ", ".join(missing))
