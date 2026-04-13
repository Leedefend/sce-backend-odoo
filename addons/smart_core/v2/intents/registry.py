from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Tuple

from ..kernel.spec import IntentSpecV2
from ..handlers.meta.describe_model import MetaDescribeModelHandlerV2
from ..handlers.meta.intent_catalog import MetaIntentCatalogHandlerV2
from ..handlers.meta.load_metadata import LoadMetadataHandlerV2
from ..handlers.meta.permission_check import PermissionCheckHandlerV2
from ..handlers.meta.registry_catalog import MetaRegistryCatalogHandlerV2
from ..handlers.api.data import ApiDataHandlerV2
from ..handlers.api.data_batch import ApiDataBatchHandlerV2
from ..handlers.api.data_create import ApiDataCreateHandlerV2
from ..handlers.api.data_unlink import ApiDataUnlinkHandlerV2
from ..handlers.api.file_download import FileDownloadHandlerV2
from ..handlers.api.file_upload import FileUploadHandlerV2
from ..handlers.api.load_contract import LoadContractHandlerV2
from ..handlers.api.onchange import ApiOnchangeHandlerV2
from ..handlers.domain.execute_button import ExecuteButtonHandlerV2
from ..handlers.ui.ui_contract import UIContractHandlerV2
from ..modules.app.handlers.catalog import AppCatalogHandlerV2
from ..modules.app.handlers.init import AppInitHandlerV2
from ..modules.app.handlers.nav import AppNavHandlerV2
from ..modules.app.handlers.open import AppOpenHandlerV2
from ..handlers.system.ping import SystemPingHandlerV2
from ..handlers.system.registry_list import SystemRegistryListHandlerV2
from ..handlers.system.session_bootstrap import SessionBootstrapHandlerV2
from ..handlers.system.system_init import SystemInitHandlerV2
from ..handlers.system.system_init_inspect import SystemInitInspectHandlerV2


@dataclass(frozen=True)
class IntentRegistration:
    intent_name: str
    handler_factory: Callable[[], object]
    request_schema: str
    response_contract: str
    capability_code: str
    permission_mode: str
    idempotent: bool
    version: str
    canonical_intent: str = ""
    intent_class: str = ""
    tags: Tuple[str, ...] = ()


class IntentRegistry:
    def __init__(self) -> None:
        self._entries: Dict[str, IntentRegistration] = {}

    def register(self, registration: IntentRegistration) -> None:
        key = str(registration.intent_name or "").strip()
        if not key:
            raise ValueError("intent_name is required")
        if key in self._entries:
            raise ValueError(f"duplicate intent registration: {key}")
        self._entries[key] = registration

    def get(self, intent_name: str) -> IntentRegistration:
        key = str(intent_name or "").strip()
        if key not in self._entries:
            raise KeyError(f"intent not registered: {key}")
        return self._entries[key]

    def list_intents(self) -> Dict[str, IntentRegistration]:
        return dict(self._entries)

    def build_spec_map(self) -> Dict[str, IntentSpecV2]:
        out: Dict[str, IntentSpecV2] = {}
        for intent_name, registration in self._entries.items():
            out[intent_name] = IntentSpecV2(
                intent_name=registration.intent_name,
                permission_mode=registration.permission_mode,
                request_schema=registration.request_schema,
                response_contract=registration.response_contract,
                version=registration.version,
                handler_factory=registration.handler_factory,
            )
        return out


def build_default_registry() -> IntentRegistry:
    registry = IntentRegistry()
    registry.register(
        IntentRegistration(
            intent_name="system.ping",
            handler_factory=SystemPingHandlerV2,
            request_schema="v2.system.ping.request.v1",
            response_contract="v2.system.ping.response.v1",
            capability_code="system.ping",
            permission_mode="public",
            idempotent=True,
            version="v1",
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="system.init",
            handler_factory=SystemInitHandlerV2,
            request_schema="v2.system.init.request.v1",
            response_contract="v2.system.init.response.v1",
            capability_code="system.init",
            permission_mode="authenticated",
            idempotent=True,
            version="v1",
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="system.init.inspect",
            handler_factory=SystemInitInspectHandlerV2,
            request_schema="v2.system.init.inspect.request.v1",
            response_contract="v2.system.init.inspect.response.v1",
            capability_code="system.init.inspect",
            permission_mode="authenticated",
            idempotent=True,
            version="v1",
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="session.bootstrap",
            canonical_intent="session.bootstrap",
            intent_class="addons.smart_core.v2.handlers.system.session_bootstrap.SessionBootstrapHandlerV2",
            handler_factory=SessionBootstrapHandlerV2,
            request_schema="addons.smart_core.v2.intents.schemas.session_bootstrap_schema.SessionBootstrapRequestSchemaV2",
            response_contract="v2.session.bootstrap.response.v1",
            capability_code="session.bootstrap",
            permission_mode="authenticated",
            idempotent=True,
            version="v1",
            tags=("stage1", "registry_closure", "bootstrap"),
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="system.registry.list",
            handler_factory=SystemRegistryListHandlerV2,
            request_schema="v2.system.registry.list.request.v1",
            response_contract="v2.system.registry.list.response.v1",
            capability_code="system.registry.list",
            permission_mode="authenticated",
            idempotent=True,
            version="v1",
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="meta.registry.catalog",
            handler_factory=MetaRegistryCatalogHandlerV2,
            request_schema="v2.meta.registry.catalog.request.v1",
            response_contract="v2.meta.registry.catalog.response.v1",
            capability_code="meta.registry.catalog",
            permission_mode="authenticated",
            idempotent=True,
            version="v1",
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="meta.describe_model",
            canonical_intent="meta.describe_model",
            intent_class="meta",
            handler_factory=MetaDescribeModelHandlerV2,
            request_schema="addons.smart_core.v2.intents.schemas.describe_model_schema.MetaDescribeModelRequestSchemaV2",
            response_contract="v2.meta.describe_model.response.v1",
            capability_code="meta.describe_model",
            permission_mode="authenticated",
            idempotent=True,
            version="v1",
            tags=("meta", "model", "schema", "describe"),
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="load_metadata",
            canonical_intent="load_metadata",
            intent_class="meta",
            handler_factory=LoadMetadataHandlerV2,
            request_schema="addons.smart_core.v2.intents.schemas.load_metadata_schema.LoadMetadataRequestSchemaV2",
            response_contract="v2.load_metadata.response.v1",
            capability_code="load_metadata",
            permission_mode="authenticated",
            idempotent=True,
            version="v1",
            tags=("meta", "load_metadata", "schema", "registry_closure"),
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="permission.check",
            handler_factory=PermissionCheckHandlerV2,
            request_schema="v2.permission.check.request.v1",
            response_contract="v2.permission.check.response.v1",
            capability_code="permission.check",
            permission_mode="authenticated",
            idempotent=True,
            version="v1",
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="api.data",
            canonical_intent="api.data",
            intent_class="api",
            handler_factory=ApiDataHandlerV2,
            request_schema="addons.smart_core.v2.intents.schemas.api_data_schema.ApiDataRequestSchemaV2",
            response_contract="v2.api.data.response.v1",
            capability_code="api.data",
            permission_mode="authenticated",
            idempotent=False,
            version="v1",
            tags=("api", "data", "read_write", "registry_closure"),
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="api.data.batch",
            canonical_intent="api.data.batch",
            intent_class="api",
            handler_factory=ApiDataBatchHandlerV2,
            request_schema="addons.smart_core.v2.intents.schemas.api_data_batch_schema.ApiDataBatchRequestSchemaV2",
            response_contract="v2.api.data.batch.response.v1",
            capability_code="api.data.batch",
            permission_mode="authenticated",
            idempotent=False,
            version="v1",
            tags=("api", "data_batch", "batch", "registry_closure"),
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="api.data.create",
            canonical_intent="api.data.create",
            intent_class="api",
            handler_factory=ApiDataCreateHandlerV2,
            request_schema="addons.smart_core.v2.intents.schemas.api_data_create_schema.ApiDataCreateRequestSchemaV2",
            response_contract="v2.api.data.create.response.v1",
            capability_code="api.data.create",
            permission_mode="authenticated",
            idempotent=False,
            version="v1",
            tags=("api", "data_create", "create", "registry_closure"),
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="api.data.unlink",
            canonical_intent="api.data.unlink",
            intent_class="api",
            handler_factory=ApiDataUnlinkHandlerV2,
            request_schema="addons.smart_core.v2.intents.schemas.api_data_unlink_schema.ApiDataUnlinkRequestSchemaV2",
            response_contract="v2.api.data.unlink.response.v1",
            capability_code="api.data.unlink",
            permission_mode="authenticated",
            idempotent=False,
            version="v1",
            tags=("api", "data_unlink", "unlink", "registry_closure"),
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="file.upload",
            canonical_intent="file.upload",
            intent_class="api",
            handler_factory=FileUploadHandlerV2,
            request_schema="addons.smart_core.v2.intents.schemas.file_upload_schema.FileUploadRequestSchemaV2",
            response_contract="v2.file.upload.response.v1",
            capability_code="file.upload",
            permission_mode="authenticated",
            idempotent=False,
            version="v1",
            tags=("api", "file_upload", "upload", "registry_closure"),
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="file.download",
            canonical_intent="file.download",
            intent_class="api",
            handler_factory=FileDownloadHandlerV2,
            request_schema="addons.smart_core.v2.intents.schemas.file_download_schema.FileDownloadRequestSchemaV2",
            response_contract="v2.file.download.response.v1",
            capability_code="file.download",
            permission_mode="authenticated",
            idempotent=False,
            version="v1",
            tags=("api", "file_download", "download", "registry_closure"),
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="load_contract",
            canonical_intent="load_contract",
            intent_class="ui",
            handler_factory=LoadContractHandlerV2,
            request_schema="addons.smart_core.v2.intents.schemas.load_contract_schema.LoadContractRequestSchemaV2",
            response_contract="v2.load_contract.response.v1",
            capability_code="load_contract",
            permission_mode="authenticated",
            idempotent=True,
            version="v1",
            tags=("ui", "load_contract", "contract", "registry_closure"),
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="api.onchange",
            canonical_intent="api.onchange",
            intent_class="api",
            handler_factory=ApiOnchangeHandlerV2,
            request_schema="addons.smart_core.v2.intents.schemas.api_onchange_schema.ApiOnchangeRequestSchemaV2",
            response_contract="v2.api.onchange.response.v1",
            capability_code="api.onchange",
            permission_mode="authenticated",
            idempotent=False,
            version="v1",
            tags=("api", "onchange", "field_linkage", "registry_closure"),
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="execute_button",
            canonical_intent="execute_button",
            intent_class="domain",
            handler_factory=ExecuteButtonHandlerV2,
            request_schema="addons.smart_core.v2.intents.schemas.execute_button_schema.ExecuteButtonRequestSchemaV2",
            response_contract="v2.execute_button.response.v1",
            capability_code="execute_button",
            permission_mode="authenticated",
            idempotent=False,
            version="v1",
            tags=("domain", "action", "button", "write_path"),
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="meta.intent_catalog",
            handler_factory=MetaIntentCatalogHandlerV2,
            request_schema="v2.meta.intent_catalog.request.v1",
            response_contract="v2.meta.intent_catalog.response.v1",
            capability_code="meta.intent_catalog",
            permission_mode="authenticated",
            idempotent=True,
            version="v1",
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="app.catalog",
            handler_factory=AppCatalogHandlerV2,
            request_schema="v2.app.catalog.request.v1",
            response_contract="v2.app.catalog.response.v1",
            capability_code="app.catalog",
            permission_mode="authenticated",
            idempotent=True,
            version="v1",
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="app.init",
            canonical_intent="app.init",
            intent_class="app",
            handler_factory=AppInitHandlerV2,
            request_schema="addons.smart_core.v2.intents.schemas.first_scenario_schema.FirstScenarioRequestSchemaV2",
            response_contract="v2.app.init.response.v1",
            capability_code="app.init",
            permission_mode="authenticated",
            idempotent=True,
            version="v1",
            tags=("scenario", "assembly", "session", "meta", "ui"),
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="app.nav",
            handler_factory=AppNavHandlerV2,
            request_schema="v2.app.nav.request.v1",
            response_contract="v2.app.nav.response.v1",
            capability_code="app.nav",
            permission_mode="authenticated",
            idempotent=True,
            version="v1",
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="app.open",
            handler_factory=AppOpenHandlerV2,
            request_schema="v2.app.open.request.v1",
            response_contract="v2.app.open.response.v1",
            capability_code="app.open",
            permission_mode="authenticated",
            idempotent=True,
            version="v1",
        )
    )
    registry.register(
        IntentRegistration(
            intent_name="ui.contract",
            canonical_intent="ui.contract",
            intent_class="ui",
            handler_factory=UIContractHandlerV2,
            request_schema="addons.smart_core.v2.intents.schemas.ui_contract_schema.UIContractRequestSchemaV2",
            response_contract="v2.ui.contract.response.v1",
            capability_code="ui.contract",
            permission_mode="authenticated",
            idempotent=True,
            version="v1",
            tags=("ui", "contract", "schema", "view"),
        )
    )
    return registry
