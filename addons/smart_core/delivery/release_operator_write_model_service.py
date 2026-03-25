# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from .release_operator_contract_versions import RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION


def _text(value: Any) -> str:
    return str(value or "").strip()


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value in (1, "1", "true", "True", "yes", "on"):
        return True
    if value in (0, "0", "false", "False", "no", "off"):
        return False
    return bool(default)


class ReleaseOperatorWriteModelService:
    def __init__(self, env):
        self.env = env

    def _resolve_identity(self, *, product_key: str) -> dict[str, str]:
        resolved = _text(product_key) or "construction.standard"
        if "." in resolved:
            base_product_key, edition_key = resolved.split(".", 1)
        else:
            base_product_key, edition_key = "construction", "standard"
        return {
            "product_key": resolved,
            "base_product_key": _text(base_product_key) or "construction",
            "edition_key": _text(edition_key) or "standard",
        }

    def _approve_identity(self, *, action_id: int) -> dict[str, str]:
        rec = self.env["sc.release.action"].sudo().browse(int(action_id or 0))
        if not rec.exists() or not rec.active:
            raise ValueError("RELEASE_ACTION_NOT_FOUND")
        return {
            "product_key": _text(rec.product_key),
            "base_product_key": _text(rec.base_product_key) or "construction",
            "edition_key": _text(rec.edition_key) or "standard",
        }

    def build_promote_write_model(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        from .release_operator_contract_registry import build_release_operator_contract_registry

        params = params if isinstance(params, dict) else {}
        identity = self._resolve_identity(product_key=_text(params.get("product_key")))
        snapshot_id = int(params.get("snapshot_id") or 0)
        if snapshot_id <= 0:
            raise ValueError("SNAPSHOT_ID_REQUIRED")
        return {
            "contract_version": RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
            "contract_registry": build_release_operator_contract_registry(),
            "operation": "promote_snapshot",
            "identity": identity,
            "payload": {
                "snapshot_id": snapshot_id,
                "replace_active": _bool(params.get("replace_active"), default=True),
                "note": _text(params.get("note")),
            },
        }

    def build_approve_write_model(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        from .release_operator_contract_registry import build_release_operator_contract_registry

        params = params if isinstance(params, dict) else {}
        action_id = int(params.get("action_id") or 0)
        if action_id <= 0:
            raise ValueError("ACTION_ID_REQUIRED")
        identity = self._approve_identity(action_id=action_id)
        return {
            "contract_version": RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
            "contract_registry": build_release_operator_contract_registry(),
            "operation": "approve_action",
            "identity": identity,
            "payload": {
                "action_id": action_id,
                "execute_after_approval": _bool(params.get("execute_after_approval"), default=True),
                "note": _text(params.get("note")),
            },
        }

    def build_rollback_write_model(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        from .release_operator_contract_registry import build_release_operator_contract_registry

        params = params if isinstance(params, dict) else {}
        identity = self._resolve_identity(product_key=_text(params.get("product_key")))
        return {
            "contract_version": RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
            "contract_registry": build_release_operator_contract_registry(),
            "operation": "rollback_snapshot",
            "identity": identity,
            "payload": {
                "target_snapshot_id": int(params.get("target_snapshot_id") or 0) or 0,
                "note": _text(params.get("note")),
            },
        }

    def build_from_intent(self, *, intent: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        intent_name = _text(intent)
        if intent_name == "release.operator.promote":
            return self.build_promote_write_model(params)
        if intent_name == "release.operator.approve":
            return self.build_approve_write_model(params)
        if intent_name == "release.operator.rollback":
            return self.build_rollback_write_model(params)
        raise ValueError(f"UNSUPPORTED_RELEASE_OPERATOR_INTENT:{intent_name}")
