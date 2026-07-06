# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo import api, fields, models
from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first


def _text(value: Any) -> str:
    return str(value or "").strip()


class ScProductPolicy(models.Model):
    _name = "sc.product.policy"
    _description = "SC Product Release Policy"
    _order = "base_product_key, edition_key, product_key, id"

    active = fields.Boolean(default=True)
    product_key = fields.Char(required=True, index=True)
    base_product_key = fields.Char(required=True, index=True, default="platform")
    edition_key = fields.Char(required=True, index=True, default="standard")
    state = fields.Selection(
        [("draft", "Draft"), ("preview", "Preview"), ("stable", "Stable"), ("archived", "Archived")],
        default="draft",
        required=True,
        index=True,
    )
    access_level = fields.Selection(
        [("public", "Public"), ("internal", "Internal"), ("role_restricted", "Role Restricted")],
        default="public",
        required=True,
    )
    label = fields.Char(required=True)
    version = fields.Char(default="v1")
    allowed_role_codes = fields.Json(default=list)
    scene_version_bindings = fields.Json(default=dict)
    menu_groups = fields.Json(default=list)
    scenes = fields.Json(default=list)
    capabilities = fields.Json(default=list)
    note = fields.Text()

    _sql_constraints = [
        ("sc_product_policy_product_key_uniq", "unique(product_key)", "Product key must be unique."),
    ]

    @api.model
    def ensure_platform_default_product_policies(self):
        from odoo.addons.smart_core.delivery.product_policy_service import ProductPolicyService
        from odoo.addons.smart_core.delivery.product_policy_catalog_sync_service import ProductPolicyCatalogSyncService

        service = ProductPolicyService(self.env)
        catalog_sync = ProductPolicyCatalogSyncService(self.env)
        extension_defaults = call_extension_hook_first(
            self.env,
            "smart_core_default_product_policy_specs",
            self.env,
        )
        defaults = list(extension_defaults) if isinstance(extension_defaults, (list, tuple)) else []
        defaults += [
            ("platform.standard", "平台内核标准版"),
            ("platform.preview", "平台内核预览版"),
        ]
        for product_key, label in defaults:
            identity_base = product_key.split(".", 1)[0] if "." in product_key else product_key
            if catalog_sync._is_catalog_backed_product(
                identity={
                    "product_key": product_key,
                    "base_product_key": identity_base,
                    "edition_key": product_key.split(".", 1)[1] if "." in product_key else "standard",
                }
            ):
                policy = catalog_sync.build_catalog_policy_payload(product_key=product_key)
            else:
                policy = service.get_policy(product_key=product_key)
            values = {
                "active": True,
                "product_key": product_key,
                "base_product_key": _text(policy.get("base_product_key")) or product_key.split(".", 1)[0],
                "edition_key": _text(policy.get("edition_key")) or product_key.split(".", 1)[1],
                "state": "preview" if product_key.endswith(".preview") else (_text(policy.get("state")) or "stable"),
                "access_level": _text(policy.get("access_level")) or "public",
                "allowed_role_codes": policy.get("allowed_role_codes") if isinstance(policy.get("allowed_role_codes"), list) else [],
                "label": label,
                "version": _text(policy.get("version")) or "v1",
                "scene_version_bindings": policy.get("scene_version_bindings") if isinstance(policy.get("scene_version_bindings"), dict) else {},
                "menu_groups": policy.get("menu_groups") if isinstance(policy.get("menu_groups"), list) else [],
                "scenes": policy.get("scenes") if isinstance(policy.get("scenes"), list) else [],
                "capabilities": policy.get("capabilities") if isinstance(policy.get("capabilities"), list) else [],
                "note": "platform seeded product policy",
            }
            rec = self.sudo().search([("product_key", "=", product_key)], limit=1)
            if rec:
                rec.write(values)
            else:
                self.sudo().create(values)
        self.env["ir.config_parameter"].sudo().set_param(
            "smart_core.release_operator.product_base_keys",
            ",".join(dict.fromkeys([_text(key).split(".", 1)[0] for key, _label in defaults if _text(key)])),
        )
        return True

    def to_runtime_dict(self) -> dict[str, Any]:
        from odoo.addons.smart_core.delivery.product_policy_service import ProductPolicyService

        self.ensure_one()
        return {
            "id": int(self.id),
            "active": bool(self.active),
            "product_key": _text(self.product_key),
            "base_product_key": _text(self.base_product_key),
            "edition_key": _text(self.edition_key),
            "state": _text(self.state),
            "access_level": _text(self.access_level),
            "allowed_role_codes": self.allowed_role_codes if isinstance(self.allowed_role_codes, list) else [],
            "label": _text(self.label),
            "version": _text(self.version) or "v1",
            "scene_version_bindings": self.scene_version_bindings if isinstance(self.scene_version_bindings, dict) else {},
            "menu_groups": self.menu_groups if isinstance(self.menu_groups, list) else [],
            "scenes": self.scenes if isinstance(self.scenes, list) else [],
            "capabilities": self.capabilities if isinstance(self.capabilities, list) else [],
            "note": _text(self.note),
            "policy_source_authority": ProductPolicyService.source_authority_contract(),
        }

    def action_freeze_candidate(self):
        from odoo.addons.smart_core.delivery.edition_release_snapshot_service import EditionReleaseSnapshotService

        for rec in self:
            EditionReleaseSnapshotService(rec.env).freeze_release_surface(
                product_key=rec.product_key,
                version=rec.version or "v1",
                note="frozen by platform product policy action",
                replace_active=False,
            )
        return True


class ScSceneSnapshot(models.Model):
    _name = "sc.scene.snapshot"
    _description = "SC Scene Release Snapshot"
    _order = "scene_key, product_key, version desc, id desc"

    active = fields.Boolean(default=True)
    scene_key = fields.Char(required=True, index=True)
    product_key = fields.Char(required=True, index=True)
    version = fields.Char(default="v1", required=True, index=True)
    channel = fields.Char(default="stable", required=True, index=True)
    state = fields.Selection(
        [("draft", "Draft"), ("stable", "Stable"), ("archived", "Archived")],
        default="draft",
        required=True,
        index=True,
    )
    is_active = fields.Boolean(default=False, index=True)
    contract_json = fields.Json(default=dict)
    meta_json = fields.Json(default=dict)
    source_ref = fields.Char()
    note = fields.Text()

    def to_runtime_dict(self) -> dict[str, Any]:
        self.ensure_one()
        return {
            "id": int(self.id),
            "active": bool(self.active),
            "scene_key": _text(self.scene_key),
            "product_key": _text(self.product_key),
            "version": _text(self.version) or "v1",
            "channel": _text(self.channel) or "stable",
            "state": _text(self.state),
            "is_active": bool(self.is_active),
            "contract_json": self.contract_json if isinstance(self.contract_json, dict) else {},
            "meta_json": self.meta_json if isinstance(self.meta_json, dict) else {},
            "source_ref": _text(self.source_ref),
            "note": _text(self.note),
        }


class ScEditionReleaseSnapshot(models.Model):
    _name = "sc.edition.release.snapshot"
    _description = "SC Edition Release Snapshot"
    _order = "released_at desc, activated_at desc, frozen_at desc, id desc"

    active = fields.Boolean(default=True)
    state = fields.Selection(
        [("candidate", "Candidate"), ("approved", "Approved"), ("released", "Released"), ("superseded", "Superseded")],
        default="candidate",
        required=True,
        index=True,
    )
    product_key = fields.Char(required=True, index=True)
    base_product_key = fields.Char(required=True, index=True)
    edition_key = fields.Char(required=True, index=True)
    label = fields.Char()
    version = fields.Char(default="v1", required=True, index=True)
    channel = fields.Char(default="stable", required=True, index=True)
    is_active = fields.Boolean(default=False, index=True)
    frozen_at = fields.Datetime()
    approved_at = fields.Datetime()
    released_at = fields.Datetime()
    activated_at = fields.Datetime()
    superseded_at = fields.Datetime()
    source_policy_id = fields.Many2one("sc.product.policy", ondelete="set null")
    promoted_from_snapshot_id = fields.Many2one("sc.edition.release.snapshot", ondelete="set null")
    rollback_target_snapshot_id = fields.Many2one("sc.edition.release.snapshot", ondelete="set null")
    replaced_by_snapshot_id = fields.Many2one("sc.edition.release.snapshot", ondelete="set null")
    snapshot_json = fields.Json(default=dict)
    meta_json = fields.Json(default=dict)
    state_reason = fields.Char()
    promotion_note = fields.Char()
    note = fields.Text()

    def to_runtime_dict(self) -> dict[str, Any]:
        self.ensure_one()
        return {
            "id": int(self.id),
            "active": bool(self.active),
            "state": _text(self.state) or "candidate",
            "product_key": _text(self.product_key),
            "base_product_key": _text(self.base_product_key),
            "edition_key": _text(self.edition_key),
            "label": _text(self.label),
            "version": _text(self.version) or "v1",
            "channel": _text(self.channel) or "stable",
            "is_active": bool(self.is_active),
            "frozen_at": self.frozen_at.isoformat() if self.frozen_at else "",
            "approved_at": self.approved_at.isoformat() if self.approved_at else "",
            "released_at": self.released_at.isoformat() if self.released_at else "",
            "activated_at": self.activated_at.isoformat() if self.activated_at else "",
            "superseded_at": self.superseded_at.isoformat() if self.superseded_at else "",
            "source_policy_id": int(self.source_policy_id.id) if self.source_policy_id else 0,
            "promoted_from_snapshot_id": int(self.promoted_from_snapshot_id.id) if self.promoted_from_snapshot_id else 0,
            "rollback_target_snapshot_id": int(self.rollback_target_snapshot_id.id) if self.rollback_target_snapshot_id else 0,
            "replaced_by_snapshot_id": int(self.replaced_by_snapshot_id.id) if self.replaced_by_snapshot_id else 0,
            "snapshot_json": self.snapshot_json if isinstance(self.snapshot_json, dict) else {},
            "meta_json": self.meta_json if isinstance(self.meta_json, dict) else {},
            "state_reason": _text(self.state_reason),
            "promotion_note": _text(self.promotion_note),
            "note": _text(self.note),
        }

    def action_approve(self):
        from odoo.addons.smart_core.delivery.edition_release_snapshot_promotion_service import EditionReleaseSnapshotPromotionService

        service = EditionReleaseSnapshotPromotionService(self.env)
        for rec in self:
            service.promote_to_approved(int(rec.id), state_reason="approved_from_platform_admin", promotion_note="approved from platform admin")
        return True

    def action_release(self):
        from odoo.addons.smart_core.delivery.edition_release_snapshot_promotion_service import EditionReleaseSnapshotPromotionService

        service = EditionReleaseSnapshotPromotionService(self.env)
        for rec in self:
            service.promote_to_released(
                int(rec.id),
                replace_active=True,
                state_reason="released_from_platform_admin",
                promotion_note="released from platform admin",
            )
        return True

    def action_supersede(self):
        from odoo.addons.smart_core.delivery.edition_release_snapshot_promotion_service import EditionReleaseSnapshotPromotionService

        service = EditionReleaseSnapshotPromotionService(self.env)
        for rec in self:
            service.supersede(int(rec.id), state_reason="superseded_from_platform_admin", promotion_note="superseded from platform admin")
        return True


class ScReleaseAction(models.Model):
    _name = "sc.release.action"
    _description = "SC Release Action"
    _order = "requested_at desc, id desc"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    action_type = fields.Char(required=True, index=True)
    state = fields.Selection(
        [("pending", "Pending"), ("running", "Running"), ("done", "Done"), ("failed", "Failed"), ("canceled", "Canceled")],
        default="pending",
        required=True,
        index=True,
    )
    product_key = fields.Char(required=True, index=True)
    base_product_key = fields.Char(index=True)
    edition_key = fields.Char(index=True)
    requested_by_user_id = fields.Many2one("res.users", ondelete="set null")
    requested_at = fields.Datetime(default=fields.Datetime.now)
    executed_at = fields.Datetime()
    completed_at = fields.Datetime()
    source_snapshot_id = fields.Many2one("sc.edition.release.snapshot", ondelete="set null")
    target_snapshot_id = fields.Many2one("sc.edition.release.snapshot", ondelete="set null")
    result_snapshot_id = fields.Many2one("sc.edition.release.snapshot", ondelete="set null")
    policy_key = fields.Char()
    approval_required = fields.Boolean(default=False)
    approval_state = fields.Selection(
        [("not_required", "Not Required"), ("pending_approval", "Pending Approval"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="not_required",
        required=True,
    )
    approved_by_user_id = fields.Many2one("res.users", ondelete="set null")
    approved_at = fields.Datetime()
    approval_note = fields.Char()
    allowed_executor_role_codes_json = fields.Json(default=list)
    required_approver_role_codes_json = fields.Json(default=list)
    policy_snapshot_json = fields.Json(default=dict)
    reason_code = fields.Char()
    note = fields.Text()
    request_payload_json = fields.Json(default=dict)
    result_payload_json = fields.Json(default=dict)
    diagnostics_json = fields.Json(default=dict)
    execution_protocol_version = fields.Char(default="v1")
    execution_trace_json = fields.Json(default=dict)

    def to_runtime_dict(self) -> dict[str, Any]:
        self.ensure_one()
        return {
            "id": int(self.id),
            "active": bool(self.active),
            "name": _text(self.name),
            "action_type": _text(self.action_type),
            "state": _text(self.state) or "pending",
            "product_key": _text(self.product_key),
            "base_product_key": _text(self.base_product_key),
            "edition_key": _text(self.edition_key),
            "requested_by_user_id": int(self.requested_by_user_id.id) if self.requested_by_user_id else 0,
            "requested_at": self.requested_at.isoformat() if self.requested_at else "",
            "executed_at": self.executed_at.isoformat() if self.executed_at else "",
            "completed_at": self.completed_at.isoformat() if self.completed_at else "",
            "source_snapshot_id": int(self.source_snapshot_id.id) if self.source_snapshot_id else 0,
            "target_snapshot_id": int(self.target_snapshot_id.id) if self.target_snapshot_id else 0,
            "result_snapshot_id": int(self.result_snapshot_id.id) if self.result_snapshot_id else 0,
            "policy_key": _text(self.policy_key),
            "approval_required": bool(self.approval_required),
            "approval_state": _text(self.approval_state) or "not_required",
            "approved_by_user_id": int(self.approved_by_user_id.id) if self.approved_by_user_id else 0,
            "approved_at": self.approved_at.isoformat() if self.approved_at else "",
            "approval_note": _text(self.approval_note),
            "allowed_executor_role_codes_json": self.allowed_executor_role_codes_json if isinstance(self.allowed_executor_role_codes_json, list) else [],
            "required_approver_role_codes_json": self.required_approver_role_codes_json if isinstance(self.required_approver_role_codes_json, list) else [],
            "policy_snapshot_json": self.policy_snapshot_json if isinstance(self.policy_snapshot_json, dict) else {},
            "reason_code": _text(self.reason_code),
            "note": _text(self.note),
            "request_payload_json": self.request_payload_json if isinstance(self.request_payload_json, dict) else {},
            "result_payload_json": self.result_payload_json if isinstance(self.result_payload_json, dict) else {},
            "diagnostics_json": self.diagnostics_json if isinstance(self.diagnostics_json, dict) else {},
            "execution_protocol_version": _text(self.execution_protocol_version),
            "execution_trace_json": self.execution_trace_json if isinstance(self.execution_trace_json, dict) else {},
        }
