# -*- coding: utf-8 -*-
from __future__ import annotations

from .release_operator_read_model_service import ReleaseOperatorReadModelService


RELEASE_OPERATOR_SURFACE_CONTRACT_VERSION = "release_operator_surface_v1"


class ReleaseOperatorSurfaceService:
    def __init__(self, env):
        self.env = env
        self.read_model_service = ReleaseOperatorReadModelService(env)

    def build_surface(self, *, product_key: str = "", action_limit: int = 20) -> dict[str, Any]:
        read_model = self.read_model_service.build_read_model(product_key=product_key, action_limit=action_limit)
        return {
            "contract_version": RELEASE_OPERATOR_SURFACE_CONTRACT_VERSION,
            "read_model_v1": read_model,
            "identity": dict(read_model.get("identity") or {}),
            "products": list(read_model.get("products") or []),
            "release_state": dict(read_model.get("current_release_state") or {}),
            "pending_approval": dict(read_model.get("pending_approval_queue") or {}),
            "candidate_snapshots": list(read_model.get("candidate_snapshots") or []),
            "release_history": dict(read_model.get("release_history_summary") or {}),
            "available_actions": dict(read_model.get("available_operator_actions") or {}),
        }
