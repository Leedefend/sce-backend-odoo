# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .edition_release_snapshot_service import EditionReleaseSnapshotService


RELEASE_AUDIT_TRAIL_CONTRACT_VERSION = "release_audit_trail_surface_v1"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


class ReleaseAuditTrailService:
    def __init__(self, env):
        self.env = env
        self.snapshot_service = EditionReleaseSnapshotService(env)

    def _snapshot_model(self):
        return self.env["sc.edition.release.snapshot"].sudo()

    def _action_model(self):
        return self.env["sc.release.action"].sudo()

    def _release_identity(self, *, product_key: str) -> dict[str, str]:
        product = _text(product_key)
        if "." in product:
            base_product_key, edition_key = product.split(".", 1)
        else:
            base_product_key, edition_key = "construction", "standard"
        return {
            "product_key": product,
            "base_product_key": _text(base_product_key) or "construction",
            "edition_key": _text(edition_key) or "standard",
        }

    def _freeze_surface_summary(self, snapshot_json: dict[str, Any]) -> dict[str, Any]:
        identity = _dict(snapshot_json.get("identity"))
        policy = _dict(snapshot_json.get("policy"))
        runtime_meta = _dict(snapshot_json.get("runtime_meta"))
        nav = _list(snapshot_json.get("nav"))
        capabilities = _list(snapshot_json.get("capabilities"))
        scenes = _list(snapshot_json.get("scenes"))
        bindings = _dict(snapshot_json.get("resolved_scene_version_bindings"))
        return {
            "contract_version": _text(snapshot_json.get("contract_version")) or "edition_freeze_surface_v1",
            "identity": {
                "product_key": _text(identity.get("product_key")),
                "base_product_key": _text(identity.get("base_product_key")),
                "edition_key": _text(identity.get("edition_key")),
                "version": _text(identity.get("version")) or "v1",
                "channel": _text(identity.get("channel")) or "stable",
            },
            "policy": {
                "product_key": _text(policy.get("product_key")),
                "state": _text(policy.get("state")),
                "access_level": _text(policy.get("access_level")),
                "version": _text(policy.get("version")) or "v1",
            },
            "surface_counts": {
                "nav": len(nav),
                "capabilities": len(capabilities),
                "scenes": len(scenes),
                "scene_bindings": len(bindings),
            },
            "runtime_meta": deepcopy(runtime_meta),
        }

    def _snapshot_entry(self, rec) -> dict[str, Any]:
        payload = rec.to_runtime_dict()
        snapshot_json = _dict(payload.get("snapshot_json"))
        meta_json = _dict(payload.get("meta_json"))
        return {
            "id": int(payload.get("id") or 0),
            "product_key": _text(payload.get("product_key")),
            "base_product_key": _text(payload.get("base_product_key")),
            "edition_key": _text(payload.get("edition_key")),
            "version": _text(payload.get("version")) or "v1",
            "label": _text(payload.get("label")),
            "channel": _text(payload.get("channel")) or "stable",
            "state": _text(payload.get("state")) or "candidate",
            "is_active": bool(payload.get("is_active")),
            "frozen_at": _text(payload.get("frozen_at")),
            "approved_at": _text(payload.get("approved_at")),
            "released_at": _text(payload.get("released_at")),
            "activated_at": _text(payload.get("activated_at")),
            "superseded_at": _text(payload.get("superseded_at")),
            "source_policy_id": int(payload.get("source_policy_id") or 0),
            "promoted_from_snapshot_id": int(payload.get("promoted_from_snapshot_id") or 0),
            "rollback_target_snapshot_id": int(payload.get("rollback_target_snapshot_id") or 0),
            "replaced_by_snapshot_id": int(payload.get("replaced_by_snapshot_id") or 0),
            "state_reason": _text(payload.get("state_reason")),
            "promotion_note": _text(payload.get("promotion_note")),
            "note": _text(payload.get("note")),
            "freeze_surface": self._freeze_surface_summary(snapshot_json),
            "meta": deepcopy(meta_json),
        }

    def _action_entry(self, rec) -> dict[str, Any]:
        payload = rec.to_runtime_dict()
        return {
            "id": int(payload.get("id") or 0),
            "name": _text(payload.get("name")),
            "action_type": _text(payload.get("action_type")),
            "state": _text(payload.get("state")) or "pending",
            "product_key": _text(payload.get("product_key")),
            "base_product_key": _text(payload.get("base_product_key")),
            "edition_key": _text(payload.get("edition_key")),
            "requested_by_user_id": int(payload.get("requested_by_user_id") or 0),
            "requested_at": _text(payload.get("requested_at")),
            "executed_at": _text(payload.get("executed_at")),
            "completed_at": _text(payload.get("completed_at")),
            "source_snapshot_id": int(payload.get("source_snapshot_id") or 0),
            "target_snapshot_id": int(payload.get("target_snapshot_id") or 0),
            "result_snapshot_id": int(payload.get("result_snapshot_id") or 0),
            "reason_code": _text(payload.get("reason_code")),
            "note": _text(payload.get("note")),
            "request_payload_json": deepcopy(_dict(payload.get("request_payload_json"))),
            "result_payload_json": deepcopy(_dict(payload.get("result_payload_json"))),
            "diagnostics_json": deepcopy(_dict(payload.get("diagnostics_json"))),
        }

    def _active_released_snapshot(self, *, product_key: str):
        return self._snapshot_model().search(
            [
                ("product_key", "=", _text(product_key)),
                ("state", "=", "released"),
                ("is_active", "=", True),
                ("active", "=", True),
            ],
            order="released_at desc, activated_at desc, id desc",
            limit=1,
        )

    def build_runtime_summary(self, *, product_key: str) -> dict[str, Any]:
        identity = self._release_identity(product_key=product_key)
        active = self._active_released_snapshot(product_key=identity["product_key"])
        latest_action = self._action_model().search(
            [("product_key", "=", identity["product_key"]), ("active", "=", True)],
            order="requested_at desc, id desc",
            limit=1,
        )
        active_released_count = self._snapshot_model().search_count(
            [
                ("product_key", "=", identity["product_key"]),
                ("state", "=", "released"),
                ("is_active", "=", True),
                ("active", "=", True),
            ]
        )
        return {
            "contract_version": RELEASE_AUDIT_TRAIL_CONTRACT_VERSION,
            "product_key": identity["product_key"],
            "base_product_key": identity["base_product_key"],
            "edition_key": identity["edition_key"],
            "active_snapshot_id": int(active.id) if active else 0,
            "active_snapshot_version": _text(active.version) if active else "",
            "active_snapshot_state": _text(active.state) if active else "",
            "rollback_target_snapshot_id": int(active.rollback_target_snapshot_id.id) if active and active.rollback_target_snapshot_id else 0,
            "latest_action_id": int(latest_action.id) if latest_action else 0,
            "latest_action_type": _text(latest_action.action_type) if latest_action else "",
            "latest_action_state": _text(latest_action.state) if latest_action else "",
            "active_released_uniqueness_ok": active_released_count <= 1,
            "audit_exportable": True,
        }

    def build_audit_trail(self, *, product_key: str, action_limit: int = 20) -> dict[str, Any]:
        identity = self._release_identity(product_key=product_key)
        snapshots = self._snapshot_model().search(
            [("product_key", "=", identity["product_key"]), ("active", "=", True)],
            order="released_at desc, activated_at desc, frozen_at desc, id desc",
        )
        actions = self._action_model().search(
            [("product_key", "=", identity["product_key"]), ("active", "=", True)],
            order="requested_at desc, id desc",
            limit=max(int(action_limit or 0), 1),
        )
        snapshot_rows = [self._snapshot_entry(row) for row in snapshots]
        action_rows = [self._action_entry(row) for row in actions]
        snapshot_index = {int(row["id"]): row for row in snapshot_rows if int(row.get("id") or 0) > 0}
        active = next((row for row in snapshot_rows if row.get("state") == "released" and row.get("is_active") is True), {})
        rollback_target_id = int(active.get("rollback_target_snapshot_id") or 0)
        rollback_target = snapshot_index.get(rollback_target_id, {})
        runtime_lineage = self.snapshot_service.resolve_active_snapshot_lineage(product_key=identity["product_key"])
        summary = self.build_runtime_summary(product_key=identity["product_key"])
        promotion_actions = [row for row in action_rows if row.get("action_type") == "promote_snapshot"]
        rollback_actions = [row for row in action_rows if row.get("action_type") == "rollback_snapshot"]
        return {
            "contract_version": RELEASE_AUDIT_TRAIL_CONTRACT_VERSION,
            "identity": identity,
            "active_released_snapshot": deepcopy(active),
            "release_actions": action_rows,
            "release_snapshots": snapshot_rows,
            "lineage": {
                "active_snapshot_id": int(active.get("id") or 0),
                "active_snapshot_version": _text(active.get("version")) or "v1",
                "active_released_uniqueness_ok": bool(summary.get("active_released_uniqueness_ok")),
                "released_snapshot_lineage": deepcopy(runtime_lineage),
                "promotion_action_ids": [int(row.get("id") or 0) for row in promotion_actions],
                "rollback_action_ids": [int(row.get("id") or 0) for row in rollback_actions],
                "snapshot_ids": [int(row.get("id") or 0) for row in snapshot_rows],
            },
            "rollback_evidence": {
                "rollback_target_snapshot_id": rollback_target_id,
                "rollback_target_exists": bool(rollback_target),
                "rollback_target_version": _text(rollback_target.get("version")),
                "latest_rollback_action_id": int(rollback_actions[0].get("id") or 0) if rollback_actions else 0,
                "latest_rollback_result_snapshot_id": int(rollback_actions[0].get("result_snapshot_id") or 0) if rollback_actions else 0,
            },
            "runtime": {
                "released_snapshot_lineage": deepcopy(runtime_lineage),
                "release_audit_trail_summary": deepcopy(summary),
            },
        }
