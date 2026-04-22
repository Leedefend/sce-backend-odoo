# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DELIVERY_DIR = ROOT / "addons" / "smart_core" / "delivery"


def _load_module(module_name: str, relative_path: str):
    target = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, target)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


sys.modules.setdefault("odoo", types.ModuleType("odoo"))
sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
smart_core_pkg.__path__ = [str(DELIVERY_DIR.parent)]
delivery_pkg = sys.modules.setdefault("odoo.addons.smart_core.delivery", types.ModuleType("odoo.addons.smart_core.delivery"))
delivery_pkg.__path__ = [str(DELIVERY_DIR)]
smart_core_pkg.delivery = delivery_pkg

approval_stub = types.ModuleType("odoo.addons.smart_core.delivery.release_approval_policy_service")
approval_stub.ReleaseApprovalPolicyService = type(
    "ReleaseApprovalPolicyService",
    (),
    {"__init__": lambda self, env: None},
)
sys.modules["odoo.addons.smart_core.delivery.release_approval_policy_service"] = approval_stub

audit_stub = types.ModuleType("odoo.addons.smart_core.delivery.release_audit_trail_service")
audit_stub.ReleaseAuditTrailService = type(
    "ReleaseAuditTrailService",
    (),
    {"__init__": lambda self, env: None},
)
sys.modules["odoo.addons.smart_core.delivery.release_audit_trail_service"] = audit_stub

_load_module(
    "odoo.addons.smart_core.delivery.release_operator_contract_versions",
    "addons/smart_core/delivery/release_operator_contract_versions.py",
)
_load_module(
    "odoo.addons.smart_core.delivery.release_operator_contract_registry",
    "addons/smart_core/delivery/release_operator_contract_registry.py",
)
_load_module(
    "odoo.addons.smart_core.delivery.release_operator_read_model_service",
    "addons/smart_core/delivery/release_operator_read_model_service.py",
)
TARGET = _load_module(
    "odoo.addons.smart_core.delivery.release_operator_surface_service",
    "addons/smart_core/delivery/release_operator_surface_service.py",
)


class _ApprovalPolicyService:
    def _release_identity(self, *, product_key: str):
        edition_key = "preview" if product_key.endswith("preview") else "standard"
        return {
            "product_key": product_key,
            "base_product_key": "construction",
            "edition_key": edition_key,
        }

    def resolve_policy(self, *, action_type: str, product_key: str):
        return {"allowed_executor_role_codes": ["release_manager"]}

    def resolve_actor_role_codes(self, user):
        return ["release_manager"]

    def roles_match(self, actor_roles, allowed_roles):
        return bool(set(actor_roles or []).intersection(set(allowed_roles or [])))

    def can_approve(self, *, action, user):
        return True, "OK", {"source": "test"}


class _AuditTrailService:
    def build_audit_trail(self, *, product_key: str, action_limit: int):
        return {
            "active_released_snapshot": {
                "id": 11,
                "product_key": product_key,
                "edition_key": "standard",
                "version": "v11",
                "state": "released",
                "rollback_target_snapshot_id": 7,
            },
            "release_actions": [
                {"id": 21, "action_type": "promote_snapshot", "state": "done", "approval_state": "approved"}
            ],
            "release_snapshots": [
                {"id": 11, "product_key": product_key, "edition_key": "standard", "version": "v11", "state": "released"},
                {"id": 12, "product_key": product_key, "edition_key": "standard", "version": "v12", "state": "candidate"},
            ],
            "runtime": {
                "release_audit_trail_summary": {
                    "active_snapshot_version": "v11",
                    "latest_action_type": "promote_snapshot",
                    "latest_action_approval_state": "approved",
                },
                "released_snapshot_lineage": {"active_snapshot_id": 11},
            },
        }


class _RecordSet(list):
    def sudo(self):
        return self

    def search(self, domain, order=None, limit=None):
        return self


class _ReleaseActionRow:
    def to_runtime_dict(self):
        return {
            "id": 31,
            "action_type": "rollback_snapshot",
            "product_key": "construction.standard",
            "approval_state": "pending_approval",
            "state": "pending",
        }


class _Env(dict):
    def __init__(self):
        super().__init__()
        self.user = object()
        self["sc.release.action"] = _RecordSet([_ReleaseActionRow()])


class TestReleaseOperatorSurfaceCopyBackend(unittest.TestCase):
    def test_surface_build_includes_backend_owned_copy_payload(self):
        service = TARGET.ReleaseOperatorSurfaceService(_Env())
        service.read_model_service.audit_service = _AuditTrailService()
        service.read_model_service.approval_policy_service = _ApprovalPolicyService()

        payload = service.build_surface(product_key="construction.standard", action_limit=5)

        self.assertEqual((payload.get("copy") or {}).get("title"), "发布控制台")
        self.assertIn("候选快照", (payload.get("copy") or {}).get("hint_candidate", ""))
        self.assertEqual((((payload.get("read_model_v1") or {}).get("copy") or {}).get("section_pending")), "待审批动作")
        self.assertEqual((((payload.get("read_model_v1") or {}).get("copy") or {}).get("rollback_action_label")), "执行回滚")

    def test_preview_product_copy_mentions_preview_edition(self):
        service = TARGET.ReleaseOperatorSurfaceService(_Env())
        service.read_model_service.audit_service = _AuditTrailService()
        service.read_model_service.approval_policy_service = _ApprovalPolicyService()

        payload = service.build_surface(product_key="construction.preview", action_limit=5)

        self.assertIn("预览版", (payload.get("copy") or {}).get("description", ""))


if __name__ == "__main__":
    unittest.main()
