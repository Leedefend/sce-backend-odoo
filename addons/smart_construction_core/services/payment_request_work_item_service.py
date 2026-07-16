# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.exceptions import AccessError

from odoo.addons.smart_construction_core.handlers.payment_request_available_actions import (
    PaymentRequestAvailableActionsHandler,
)


class PaymentRequestWorkItemService:
    """Current-user payment work projection.

    The service intentionally uses the caller environment.  ACLs, record rules,
    active companies and the canonical available-actions contract are therefore
    all part of the result.  It never turns an inaccessible record into a work
    item and derives counters from the returned rows.
    """

    VERSION = "payment-request-workspace-v1"
    MODEL = "payment.request"
    # Use the same formal product entry as the finance navigation and financial
    # workspace.  The legacy menu points at a technically valid action but is
    # outside the role-scoped navigation contract and is therefore denied.
    ACTION_XMLID = "smart_construction_core.action_payment_request_user_payment_apply"
    MENU_XMLID = "smart_construction_core.menu_sc_user_payment_apply_acceptance"
    COMPLETION_EVENTS = (
        "PAYMENT_REQUEST_SUBMIT_INTENT",
        "PAYMENT_REQUEST_APPROVE_INTENT",
        "PAYMENT_REQUEST_REJECT_INTENT",
        "PAYMENT_REQUEST_DONE_INTENT",
    )
    SECTION_LABELS = {
        "todo": "待我处理",
        "initiated": "我发起的",
        "completed": "最近完成",
    }

    def __init__(self, env, *, params=None, context=None):
        self.env = env
        self.params = params or {}
        self.context = context or {}
        self.PaymentRequest = env[self.MODEL]
        self._action_handler = PaymentRequestAvailableActionsHandler(env, payload={})
        self._action_specs = list(self._action_handler._ACTION_SPECS)
        self._group_xmlids = self._action_handler._current_user_group_xmlids()
        self._state_labels = dict(self.PaymentRequest._fields["state"].selection or [])

    def _active_company_id(self):
        raw = self.params.get("company_id") or self.context.get("company_id")
        try:
            company_id = int(raw or 0)
        except (TypeError, ValueError):
            company_id = 0
        allowed_ids = set(self.env.user.company_ids.ids)
        if company_id and company_id in allowed_ids:
            return company_id
        # A missing explicit scope is intentionally the current company only;
        # an invalid scope can never broaden the query to all allowed companies.
        return int(self.env.company.id)

    def _has_workspace_capability(self):
        return bool(
            self.env.user.has_group("smart_construction_core.group_sc_cap_finance_read")
            or self.env.user.has_group("smart_construction_core.group_sc_cap_finance_user")
            or self.env.user.has_group("smart_construction_core.group_sc_cap_finance_manager")
        )

    def _company_domain(self):
        return [("company_id", "=", self._active_company_id())]

    def _project_domain(self):
        raw = self.params.get("project_id") or self.context.get("current_project_id")
        try:
            project_id = int(raw or 0)
        except (TypeError, ValueError):
            project_id = 0
        return [("project_id", "=", project_id)] if project_id else []

    def _search(self, domain, *, limit=80):
        if not self.PaymentRequest.check_access_rights("read", raise_exception=False):
            return self.PaymentRequest.browse()
        return self.PaymentRequest.search(
            list(domain or []) + self._company_domain() + self._project_domain(),
            order="write_date desc, id desc",
            limit=limit,
        )

    def _allowed_actions(self, record):
        rows = []
        for spec in self._action_specs:
            action = self._action_handler._action_entry(
                record,
                spec,
                user_group_xmlids=self._group_xmlids,
            )
            if action.get("allowed") and action.get("actor_matches_required_role"):
                rows.append(
                    {
                        "key": str(action.get("key") or ""),
                        "label": str(action.get("label") or ""),
                        "intent": str(action.get("execute_intent") or ""),
                        "params": dict(action.get("execute_params") or {}),
                        "requires_reason": bool(action.get("requires_reason")),
                        "reason_label": "拒绝原因" if action.get("requires_reason") else "",
                        "reason_help": "请说明拒绝原因，提交后会写入正式审批记录。" if action.get("requires_reason") else "",
                        "next_state": str(action.get("next_state_hint") or ""),
                        "presentation": dict(action.get("presentation") or {}),
                    }
                )
        return rows

    @staticmethod
    def _ref(value):
        if not value:
            return None
        return {"id": int(value.id), "label": str(value.display_name or "")}

    def _target(self, record):
        action = self.env.ref(self.ACTION_XMLID, raise_if_not_found=False)
        menu = self.env.ref(self.MENU_XMLID, raise_if_not_found=False)
        action_id = int(action.id) if action else 0
        menu_id = int(menu.id) if menu else 0
        query = []
        if action_id:
            query.append("action_id=%s" % action_id)
        if menu_id:
            query.append("menu_id=%s" % menu_id)
        suffix = ("?" + "&".join(query)) if query else ""
        return {
            "kind": "record",
            "model": self.MODEL,
            "record_id": int(record.id),
            "action_xmlid": self.ACTION_XMLID,
            "menu_xmlid": self.MENU_XMLID,
            "route": "/r/%s/%s%s" % (self.MODEL, record.id, suffix),
        }

    def _list_target(self):
        action = self.env.ref(self.ACTION_XMLID, raise_if_not_found=False)
        menu = self.env.ref(self.MENU_XMLID, raise_if_not_found=False)
        action_id = int(action.id) if action else 0
        menu_id = int(menu.id) if menu else 0
        if not action_id:
            return None
        return {
            "key": "payment_request_list",
            "label": "付款申请",
            "detail": "查看全部付款申请",
            "route": "/a/%s?action_id=%s%s" % (
                action_id,
                action_id,
                ("&menu_id=%s" % menu_id) if menu_id else "",
            ),
        }

    def _presentation(self, *, include_quick_links):
        quick_link = self._list_target() if include_quick_links else None
        return {
            "description": "只展示当前账号和当前业务范围内可处理的事项。",
            "search_label": "查找工作事项",
            "search_placeholder": "输入业务编号或关键信息",
            "default_sort": "updated_desc",
            "sort_options": [
                {"key": "updated_desc", "label": "最近更新", "kind": "text_desc"},
                {"key": "amount_desc", "label": "金额从高到低", "kind": "number_desc"},
                {"key": "amount_asc", "label": "金额从低到高", "kind": "number_asc"},
            ],
            "quick_links": [quick_link] if quick_link else [],
        }

    def _item(self, record, *, section, actions=None, completed_event=None):
        currency = record.currency_id
        project = record.project_id
        company = record.company_id
        partner = record.partner_id
        initiator = record.create_uid
        amount = record.amount
        money = {
            "value": amount if amount is not None else None,
            "currency": str(currency.name or "") if currency else "",
            "currency_symbol": str(currency.symbol or "") if currency else "",
            "digits": int((currency.decimal_places if currency else 2) or 2),
        }
        facts = [
            {"key": "project", "label": "项目", "value": str(project.display_name or "") if project else "未关联"},
            {"key": "company", "label": "公司", "value": str(company.display_name or "") if company else "未关联"},
            {"key": "partner", "label": "往来方", "value": str(partner.display_name or "") if partner else "未填写"},
            {"key": "amount", "label": "金额", "display_role": "money", "money": money},
            {"key": "initiator", "label": "发起人", "value": str(initiator.display_name or "") if initiator else "未知"},
            {"key": "initiated_at", "label": "发起时间", "display_role": "datetime", "value": str(record.create_date or "")},
        ]
        search_text = " ".join(
            filter(
                None,
                [
                    str(record.display_name or record.name or ""),
                    "付款申请",
                    str(self._state_labels.get(record.state) or record.state or ""),
                    *(str(row.get("value") or "") for row in facts),
                ],
            )
        )
        return {
            "key": "payment.request:%s" % record.id,
            "section": section,
            "business_type": "付款申请",
            "record": {"label": str(record.display_name or record.name or "付款申请")},
            "state": {
                "key": str(record.state or ""),
                "label": str(self._state_labels.get(record.state) or record.state or "未知状态"),
            },
            "project": self._ref(project),
            "company": self._ref(company),
            "partner": self._ref(partner),
            "amount": money,
            "initiator": self._ref(initiator),
            "initiated_at": str(record.create_date or ""),
            "updated_at": str(record.write_date or ""),
            "facts": facts,
            "search_text": search_text,
            "sort_values": {
                "updated_desc": str(record.write_date or record.create_date or ""),
                "amount_desc": amount if amount is not None else 0,
                "amount_asc": amount if amount is not None else 0,
            },
            "actions": list(actions or []),
            "completed_event": dict(completed_event or {}),
            "target": self._target(record),
            "source_authority": "payment.request + payment.request.available_actions",
        }

    def _todo(self):
        rows = []
        candidates = self._search([("type", "=", "pay"), ("state", "in", ["draft", "submit", "approved"])])
        for record in candidates:
            actions = self._allowed_actions(record)
            if actions:
                rows.append(self._item(record, section="todo", actions=actions))
        return rows

    def _initiated(self):
        records = self._search(
            [("type", "=", "pay"), ("create_uid", "=", self.env.user.id), ("state", "!=", "cancel")]
        )
        return [self._item(record, section="initiated", actions=self._allowed_actions(record)) for record in records]

    def _completed(self):
        Audit = self.env.get("sc.audit.log")
        if not Audit or not Audit.check_access_rights("read", raise_exception=False):
            return [], "AUDIT_READ_NOT_AVAILABLE"
        try:
            audits = Audit.search(
                [
                    ("model", "=", self.MODEL),
                    ("event_code", "in", list(self.COMPLETION_EVENTS)),
                    ("actor_uid", "=", self.env.user.id),
                    ("company_id", "=", self._active_company_id()),
                ],
                order="ts desc, id desc",
                limit=40,
            )
        except AccessError:
            return [], "AUDIT_READ_DENIED"
        seen = set()
        rows = []
        for audit in audits:
            if audit.res_id in seen:
                continue
            record = self.PaymentRequest.browse(audit.res_id).exists()
            if not record:
                continue
            try:
                record.check_access_rule("read")
            except AccessError:
                continue
            seen.add(audit.res_id)
            rows.append(
                self._item(
                    record,
                    section="completed",
                    actions=self._allowed_actions(record),
                    completed_event={
                        "code": str(audit.event_code or ""),
                        "label": str(audit.action or "已处理"),
                        "at": str(audit.ts or ""),
                    },
                )
            )
        return rows, ""

    def build(self):
        if not self._has_workspace_capability():
            sections = [
                {"key": "todo", "label": self.SECTION_LABELS["todo"], "count": 0, "items": []},
                {"key": "initiated", "label": self.SECTION_LABELS["initiated"], "count": 0, "items": []},
            ]
            return {
                "version": self.VERSION,
                "query_scope": {
                    "user_id": int(self.env.user.id),
                    "company_ids": [self._active_company_id()],
                    "project_id": int((self._project_domain()[0][2] if self._project_domain() else 0)),
                },
                "sections": sections,
                "counts": {row["key"]: 0 for row in sections},
                "total": 0,
                "completed_unavailable_reason": "FINANCE_CAPABILITY_NOT_AVAILABLE",
                "presentation": self._presentation(include_quick_links=False),
                "source_authority": "finance capability boundary + current-user ACL/rules",
            }
        todo = self._todo()
        initiated = self._initiated()
        completed, completed_unavailable_reason = self._completed()
        section_specs = [
            ("todo", self.SECTION_LABELS["todo"], todo),
            ("initiated", self.SECTION_LABELS["initiated"], initiated),
        ]
        if not completed_unavailable_reason:
            section_specs.append(("completed", self.SECTION_LABELS["completed"], completed))
        sections = [
            {"key": key, "label": label, "count": len(rows), "items": rows}
            for key, label, rows in section_specs
        ]
        return {
            "version": self.VERSION,
            "query_scope": {
                "user_id": int(self.env.user.id),
                "company_ids": [self._active_company_id()],
                "project_id": int((self._project_domain()[0][2] if self._project_domain() else 0)),
            },
            "sections": sections,
            "counts": {row["key"]: int(row["count"]) for row in sections},
            "total": sum(int(row["count"]) for row in sections),
            "completed_unavailable_reason": completed_unavailable_reason,
            "presentation": self._presentation(include_quick_links=True),
            "source_authority": "current-user ACL/rules + canonical payment action contract",
        }
