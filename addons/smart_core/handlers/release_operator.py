# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.delivery.release_operator_surface_service import ReleaseOperatorSurfaceService
from odoo.addons.smart_core.delivery.release_orchestrator import ReleaseOrchestrator
from odoo.addons.smart_core.delivery.release_operator_write_model_service import ReleaseOperatorWriteModelService


def _params(payload):
    if isinstance(payload, dict) and isinstance(payload.get("params"), dict):
        return dict(payload.get("params") or {})
    return dict(payload or {}) if isinstance(payload, dict) else {}


class ReleaseOperatorSurfaceHandler(BaseIntentHandler):
    INTENT_TYPE = "release.operator.surface"
    DESCRIPTION = "返回 release operator 最小发布面"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = ["base.group_user"]

    def handle(self, payload=None, ctx=None):
        params = _params(payload)
        service = ReleaseOperatorSurfaceService(self.env)
        return service.build_surface(
            product_key=str(params.get("product_key") or "").strip(),
            action_limit=int(params.get("action_limit") or 20),
        )


class ReleaseOperatorPromoteHandler(BaseIntentHandler):
    INTENT_TYPE = "release.operator.promote"
    DESCRIPTION = "通过 operator surface 发起 release snapshot promote"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = ["base.group_user"]

    def handle(self, payload=None, ctx=None):
        params = _params(payload)
        write_model = ReleaseOperatorWriteModelService(self.env).build_from_intent(intent=self.INTENT_TYPE, params=params)
        orchestrator = ReleaseOrchestrator(self.env)
        return orchestrator.submit_write_model(write_model)


class ReleaseOperatorApproveHandler(BaseIntentHandler):
    INTENT_TYPE = "release.operator.approve"
    DESCRIPTION = "通过 operator surface 审批并执行 release action"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = ["base.group_user"]

    def handle(self, payload=None, ctx=None):
        params = _params(payload)
        write_model = ReleaseOperatorWriteModelService(self.env).build_from_intent(intent=self.INTENT_TYPE, params=params)
        orchestrator = ReleaseOrchestrator(self.env)
        return orchestrator.submit_write_model(write_model)


class ReleaseOperatorRollbackHandler(BaseIntentHandler):
    INTENT_TYPE = "release.operator.rollback"
    DESCRIPTION = "通过 operator surface 执行 rollback"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = ["base.group_user"]

    def handle(self, payload=None, ctx=None):
        params = _params(payload)
        write_model = ReleaseOperatorWriteModelService(self.env).build_from_intent(intent=self.INTENT_TYPE, params=params)
        orchestrator = ReleaseOrchestrator(self.env)
        return orchestrator.submit_write_model(write_model)
