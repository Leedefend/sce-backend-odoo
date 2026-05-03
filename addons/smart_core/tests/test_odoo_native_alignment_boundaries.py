# -*- coding: utf-8 -*-
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
from odoo.addons.smart_core.handlers.search_favorite_set import SearchFavoriteSetHandler
from odoo.addons.smart_core.handlers.session_bootstrap import SessionBootstrapHandler
from odoo.addons.smart_core.handlers.ui_contract import UiContractHandler
from odoo.addons.smart_core.handlers.user_view_preference import (
    UserViewPreferenceGetHandler,
    UserViewPreferenceSetHandler,
)
from odoo.addons.smart_core.handlers.versioned_handler import VersionedDataHandlerV21
from odoo.addons.smart_core.app_config_engine.models.app_report_config import AppReportConfig
from odoo.addons.smart_core.handlers.scene_governance import SceneGovernanceExportContractHandler
from odoo.addons.smart_core.handlers.scene_package import ScenePackageListHandler
from odoo.addons.smart_core.core import scene_registry_provider
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


@tagged("post_install", "-at_install", "smart_core", "native_alignment")
class TestOdooNativeAlignmentBoundaries(TransactionCase):
    def test_search_config_declares_odoo_native_authorities(self):
        cfg = self.env["app.search.config"]
        source = cfg._source_contract("project.project")

        self.assertEqual(source.get("kind"), "odoo_native_search_projection")
        self.assertTrue(source.get("rebuildable"))
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

    def test_collaboration_handlers_declare_odoo_native_authorities(self):
        self.assertEqual(ChatterPostHandler.SOURCE_AUTHORITY, "mail.message")
        self.assertEqual(ChatterActivityScheduleHandler.SOURCE_AUTHORITY, "mail.activity")
        self.assertIn("mail.message", ChatterTimelineHandler.SOURCE_AUTHORITIES)
        self.assertIn("mail.activity", ChatterTimelineHandler.SOURCE_AUTHORITIES)
        self.assertIn("ir.attachment", ChatterTimelineHandler.SOURCE_AUTHORITIES)

    def test_file_handlers_declare_attachment_authority(self):
        self.assertEqual(FileUploadHandler.SOURCE_AUTHORITY, "ir.attachment")
        self.assertEqual(FileDownloadHandler.SOURCE_AUTHORITY, "ir.attachment")

    def test_data_intents_declare_orm_proxy_authorities(self):
        self.assertEqual(ApiDataHandler.SOURCE_KIND, "odoo_orm_proxy")
        self.assertIn("odoo.orm", ApiDataHandler.SOURCE_AUTHORITIES)
        self.assertIn("ir.rule", ApiDataHandler.SOURCE_AUTHORITIES)
        self.assertEqual(ApiDataWriteHandler.SOURCE_KIND, "odoo_orm_write_proxy")
        self.assertIn("odoo.orm", ApiDataWriteHandler.SOURCE_AUTHORITIES)
        self.assertEqual(ApiDataUnlinkHandler.SOURCE_KIND, "odoo_orm_unlink_proxy")
        self.assertIn("odoo.orm", ApiDataUnlinkHandler.SOURCE_AUTHORITIES)
        self.assertEqual(ApiDataBatchHandler.SOURCE_KIND, "odoo_orm_batch_write_proxy")
        self.assertIn("ir.model.access", ApiDataBatchHandler.SOURCE_AUTHORITIES)

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
        self.assertEqual(source.get("model"), "project.project")

    def test_scene_delivery_handlers_do_not_claim_business_fact_authority(self):
        self.assertEqual(ScenePackageListHandler.SOURCE_KIND, "scene_delivery_governance")
        self.assertIn("ir.actions", ScenePackageListHandler.SOURCE_AUTHORITIES)
        self.assertEqual(SceneGovernanceExportContractHandler.SOURCE_KIND, "scene_delivery_governance")
        registry_source = scene_registry_provider.source_authority_contract()
        self.assertTrue(registry_source.get("projection_only"))
        self.assertTrue(registry_source.get("no_business_fact_authority"))

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
        workflow_source = self.env["app.workflow.config"]._source_contract("project.project")
        self.assertEqual(workflow_source.get("runtime_authority"), "odoo_model_methods_and_mail_activity")

    def test_ui_overlay_and_asset_models_do_not_claim_business_fact_authority(self):
        self.assertEqual(AppViewFragment.SOURCE_KIND, "ui_contract_fragment_overlay")
        self.assertEqual(AppViewVariant.SOURCE_KIND, "ui_contract_variant_overlay")
        source = self.env["sc.ui.base.contract.asset"].source_authority_contract()
        self.assertEqual(UiBaseContractAsset.SOURCE_KIND, "ui_base_contract_asset_cache")
        self.assertTrue(source.get("cache_only"))
        self.assertTrue(source.get("rebuildable"))
        self.assertTrue(source.get("no_business_fact_authority"))

    def test_startup_ui_permission_and_catalog_handlers_declare_projection_sources(self):
        self.assertEqual(UiContractHandler.SOURCE_KIND, "odoo_native_ui_contract_projection")
        self.assertIn("ir.ui.view", UiContractHandler.SOURCE_AUTHORITIES)
        self.assertIn("ir.actions.act_window", UiContractHandler.SOURCE_AUTHORITIES)
        self.assertEqual(PermissionCheckHandler.SOURCE_KIND, "odoo_native_permission_projection")
        self.assertIn("sc.capability", PermissionCheckHandler.SOURCE_AUTHORITIES)
        self.assertEqual(ProjectContextSearchHandler.SOURCE_KIND, "odoo_project_context_projection")
        self.assertIn("project.project", ProjectContextSearchHandler.SOURCE_AUTHORITIES)
        self.assertEqual(MetaDescribeHandler.SOURCE_KIND, "odoo_fields_get_projection")
        self.assertEqual(MetaIntentCatalogHandler.SOURCE_KIND, "intent_delivery_catalog_projection")
        self.assertEqual(SceneHealthHandler.SOURCE_KIND, "scene_delivery_health_projection")
        self.assertEqual(ScenePackagesInstalledHandler.SOURCE_KIND, "scene_package_registry_projection")

    def test_auth_search_preference_and_gateway_sources_are_not_business_facts(self):
        self.assertEqual(LoginHandler.SOURCE_KIND, "odoo_auth_session_proxy")
        self.assertIn("res.users", LoginHandler.SOURCE_AUTHORITIES)
        self.assertEqual(LogoutHandler.SOURCE_KIND, "odoo_auth_session_proxy")
        self.assertEqual(SessionBootstrapHandler.SOURCE_KIND, "dev_test_auth_bootstrap_proxy")
        self.assertEqual(SearchFavoriteSetHandler.SOURCE_KIND, "odoo_filter_write_proxy")
        self.assertIn("ir.filters", SearchFavoriteSetHandler.SOURCE_AUTHORITIES)
        self.assertEqual(UserViewPreferenceGetHandler.SOURCE_KIND, "ui_only_user_preference")
        self.assertEqual(UserViewPreferenceSetHandler.SOURCE_KIND, "ui_only_user_preference")
        self.assertEqual(ScUserViewPreference.SOURCE_KIND, "ui_only_user_preference")
        self.assertEqual(AppActionGateway.SOURCE_KIND, "odoo_runtime_action_gateway")
        self.assertIn("odoo.model.method", AppActionGateway.SOURCE_AUTHORITIES)
        self.assertEqual(ContractSchemaMixin.SOURCE_KIND, "ui_contract_sanitizer")
        self.assertEqual(IrUiViewAssetTrigger.SOURCE_KIND, "ui_base_contract_asset_invalidation_trigger")
        self.assertEqual(VersionedDataHandlerV21.SOURCE_KIND, "test_versioned_handler_projection")
