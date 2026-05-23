# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo.addons.smart_core.core.source_authority import build_source_authority_contract

from .release_operator_read_model_service import ReleaseOperatorReadModelService
from .release_operator_contract_versions import RELEASE_OPERATOR_SURFACE_CONTRACT_VERSION



class ReleaseOperatorSurfaceService:
    SOURCE_KIND = "release_operator_surface_projection"
    SOURCE_AUTHORITIES = ("release_operator_read_model_projection",)
    NO_BUSINESS_FACT_AUTHORITY = True

    def __init__(self, env):
        self.env = env
        self.read_model_service = ReleaseOperatorReadModelService(env)

    @classmethod
    def source_authority_contract(cls) -> dict[str, Any]:
        return build_source_authority_contract(
            kind=cls.SOURCE_KIND,
            authorities=cls.SOURCE_AUTHORITIES,
            no_business_fact_authority=cls.NO_BUSINESS_FACT_AUTHORITY,
            runtime_carrier="release_operator_surface",
        )

    def build_surface(self, *, product_key: str = "", action_limit: int = 20) -> dict[str, Any]:
        from .release_operator_contract_registry import build_release_operator_contract_registry

        read_model = self.read_model_service.build_read_model(product_key=product_key, action_limit=action_limit)
        return {
            "contract_version": RELEASE_OPERATOR_SURFACE_CONTRACT_VERSION,
            "contract_registry": build_release_operator_contract_registry(),
            "source_authority": self.source_authority_contract(),
            "read_model_v1": read_model,
            "copy": dict(read_model.get("copy") or {}),
            "identity": dict(read_model.get("identity") or {}),
            "products": list(read_model.get("products") or []),
            "product_delivery_console": dict(read_model.get("product_delivery_console") or {}),
            "control_scope": dict(read_model.get("control_scope") or {}),
            "release_pipeline": dict(read_model.get("release_pipeline") or {}),
            "release_state": dict(read_model.get("current_release_state") or {}),
            "pending_approval": dict(read_model.get("pending_approval_queue") or {}),
            "candidate_snapshots": list(read_model.get("candidate_snapshots") or []),
            "release_history": dict(read_model.get("release_history_summary") or {}),
            "available_actions": dict(read_model.get("available_operator_actions") or {}),
        }
