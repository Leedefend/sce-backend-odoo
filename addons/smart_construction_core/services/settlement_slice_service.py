# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from odoo.addons.smart_construction_core.services.cost_tracking_native_adapter import CostTrackingNativeAdapter
from odoo.addons.smart_construction_core.services.payment_slice_native_adapter import PaymentSliceNativeAdapter


class SettlementSliceService:
    """Prepared settlement slice service backed by cost/payment facts."""

    RUNTIME_BLOCK_MAP = {
        "settlement_summary": "block.settlement.slice_summary",
        "summary": "block.settlement.slice_summary",
        "next_actions": "block.settlement.slice_next_actions",
    }

    def __init__(self, env):
        self.env = env
        self._cost_adapter = CostTrackingNativeAdapter(env)
        self._payment_adapter = PaymentSliceNativeAdapter(env)
        from odoo.addons.smart_construction_core.services.settlement_slice_builders import BUILDERS

        self._builders = [builder_cls(env) for builder_cls in BUILDERS]
        self._builder_map = {builder.block_key: builder for builder in self._builders}

    def build_block(self, block_key, project=None, context=None):
        normalized_key = str(block_key or "").strip().lower()
        builder_key = self.RUNTIME_BLOCK_MAP.get(normalized_key)
        if not builder_key:
            return self.error_block(normalized_key or "unknown", "UNSUPPORTED_BLOCK_KEY")
        builder = self._builder_map.get(builder_key)
        if builder is None:
            return self.error_block(builder_key, "BLOCK_BUILDER_NOT_FOUND")
        try:
            block = builder.build(project=project, context=dict(context or {}))
        except Exception:
            block = self.error_block(builder_key, "BLOCK_BUILD_FAILED")
        return block if isinstance(block, dict) else self.error_block(builder_key, "INVALID_BLOCK_PAYLOAD")

    def _model(self, model_name):
        try:
            return self.env[model_name]
        except Exception:
            return None

    def _project_domain_for_user(self):
        model = self._model("project.project")
        if model is None:
            return []
        field_map = getattr(model, "_fields", {})
        uid = int(self.env.user.id)
        ors = []
        for field_name in ("manager_id", "owner_id", "user_id"):
            if field_name in field_map:
                ors.append((field_name, "=", uid))
        if "create_uid" in field_map:
            ors.append(("create_uid", "=", uid))
        for field_name in ("user_ids", "member_ids", "member_user_ids"):
            if field_name in field_map:
                ors.append((field_name, "in", [uid]))
        if not ors:
            return []
        if len(ors) == 1:
            return [ors[0]]
        return (["|"] * (len(ors) - 1)) + ors

    def resolve_project_with_diagnostics(self, project_id):
        Project = self._model("project.project")
        if Project is None:
            return None, {"resolved_project_id": 0, "reason": "project.project model not available"}
        requested_project_id = int(project_id or 0) if str(project_id or "").strip() else 0
        if requested_project_id > 0:
            try:
                record = Project.browse(requested_project_id).exists()
                if record:
                    return record, {"resolved_project_id": int(record.id), "reason": "explicit_project_id"}
            except Exception:
                pass
        try:
            if "create_uid" in getattr(Project, "_fields", {}):
                record = Project.search([("create_uid", "=", int(self.env.user.id))], order="create_date desc,id desc", limit=1)
                if record:
                    return record, {"resolved_project_id": int(record.id), "reason": "creator_domain"}
        except Exception:
            pass
        domain = self._project_domain_for_user()
        try:
            record = Project.search(domain, order="write_date desc,id desc", limit=1)
            if record:
                return record, {"resolved_project_id": int(record.id), "reason": "user_domain"}
        except Exception:
            pass
        try:
            record = Project.search([], order="write_date desc,id desc", limit=1)
            if record:
                return record, {"resolved_project_id": int(record.id), "reason": "global_search"}
        except Exception:
            pass
        return None, {"resolved_project_id": 0, "reason": "no project resolved"}

    def summary(self, project):
        cost_summary = self._cost_adapter.summary(project)
        payment_summary = self._payment_adapter.summary(project)
        total_cost = round(float(cost_summary.get("total_cost_amount") or 0.0), 2)
        total_payment = round(float(payment_summary.get("total_payment_amount") or 0.0), 2)
        currency_name = str(payment_summary.get("currency_name") or cost_summary.get("currency_name") or "")
        return {
            "project_id": int(getattr(project, "id", 0) or 0),
            "carrier_models": ["project.cost.ledger", "payment.request"],
            "total_cost": total_cost,
            "total_payment": total_payment,
            "delta": round(total_payment - total_cost, 2),
            "currency_name": currency_name,
            "cost_record_count": int(cost_summary.get("ledger_count") or cost_summary.get("move_count") or 0),
            "payment_record_count": int(payment_summary.get("request_count") or 0),
            "cost_scope": str(cost_summary.get("prepared_boundary") or ""),
            "payment_scope": str(payment_summary.get("prepared_boundary") or ""),
            "as_of_date": str(fields.Date.today()),
            "prepared_boundary": "project_settlement_read_only_summary_only",
        }

    def project_payload(self, project):
        def _safe_text(value):
            try:
                return str(value or "")
            except Exception:
                return ""

        def _safe_rel_name(record, field_name):
            try:
                relation = getattr(record, field_name, None)
            except Exception:
                return ""
            return _safe_text(getattr(relation, "display_name", ""))

        def _safe_field(record, field_name):
            try:
                return getattr(record, field_name, "")
            except Exception:
                return ""

        if not project:
            return {
                "id": 0,
                "name": "",
                "project_code": "",
                "manager_name": "",
                "stage_name": "",
                "date_start": "",
                "date_end": "",
                "today": str(fields.Date.today()),
            }
        summary = self.summary(project)
        return {
            "id": int(project.id),
            "name": _safe_text(_safe_field(project, "name")),
            "project_code": _safe_text(_safe_field(project, "project_code")),
            "manager_name": _safe_rel_name(project, "user_id"),
            "stage_name": _safe_rel_name(project, "stage_id"),
            "date_start": str(_safe_field(project, "date_start") or ""),
            "date_end": str(_safe_field(project, "date") or _safe_field(project, "date_end") or ""),
            "total_cost": str(summary.get("total_cost") or 0.0),
            "total_payment": str(summary.get("total_payment") or 0.0),
            "delta": str(summary.get("delta") or 0.0),
            "currency_name": _safe_text(summary.get("currency_name") or ""),
            "today": str(fields.Date.today()),
        }

    @staticmethod
    def error_block(block_key, code):
        return {
            "block_key": block_key,
            "block_type": "unknown",
            "title": block_key,
            "state": "error",
            "visibility": {"allowed": True, "reason_code": "OK", "reason": ""},
            "data": {},
            "error": {"code": code, "message": code},
        }
