# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any, Dict

from odoo.exceptions import AccessError, UserError

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.services.project_creation_service import ProjectCreationService


class ProjectInitiationEnterHandler(BaseIntentHandler):
    """Product scene entry intent: create minimal project initiation record."""

    INTENT_TYPE = "project.initiation.enter"
    DESCRIPTION = "创建项目立项记录并返回后续契约入口"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]

    _ALLOWED_FIELDS = {
        "name",
        "description",
        "date_start",
        "date_end",
        "partner_id",
        "manager_id",
        "user_id",
    }

    @staticmethod
    def _build_lifecycle_hints(reason_code: str) -> Dict[str, Any]:
        code = str(reason_code or "")
        if code == "PERMISSION_DENIED":
            return {
                "stage": "project_create_denied",
                "first_action": "request_access",
                "primary_action_label": "申请权限",
                "suggested_action_intent": "project.initiation.enter",
                "suggested_action_title": "申请项目创建权限",
                "reason_code": code,
            }
        if code == "BUSINESS_RULE_FAILED":
            return {
                "stage": "project_create_validation_failed",
                "first_action": "fix_project_input",
                "primary_action_label": "修正项目信息",
                "suggested_action_intent": "project.initiation.enter",
                "suggested_action_title": "修正后重试创建",
                "reason_code": code,
            }
        return {
            "stage": "project_create_input_missing",
            "first_action": "fill_required_fields",
            "primary_action_label": "补全必填信息",
            "suggested_action_intent": "project.initiation.enter",
            "suggested_action_title": "补全后重试创建",
            "reason_code": code or "MISSING_PARAMS",
        }

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params: Dict[str, Any] = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}

        name = str(params.get("name") or "").strip()
        if not name:
            reason_code = "MISSING_PARAMS"
            return {
                "ok": False,
                "error": {
                    "code": reason_code,
                    "message": "缺少必填字段：name",
                    "suggested_action": "fix_input",
                },
                "data": {
                    "lifecycle_hints": self._build_lifecycle_hints(reason_code),
                    "suggested_action_payload": {
                        "intent": "project.initiation.enter",
                        "reason_code": reason_code,
                        "params": {
                            "reason_code": reason_code,
                        },
                    },
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": str((self.context or {}).get("trace_id") or ""),
                },
            }

        create_vals = {key: params.get(key) for key in self._ALLOWED_FIELDS if key in params}
        create_vals["name"] = name

        model = self.env["project.project"]
        try:
            model.check_access_rights("create")
            creation_service = ProjectCreationService(self.env)
            normalized_vals = creation_service.normalize_create_vals(create_vals)
            project = model.create(normalized_vals)
            bootstrap_summary = creation_service.post_create_bootstrap(project)
        except AccessError:
            reason_code = "PERMISSION_DENIED"
            return {
                "ok": False,
                "error": {
                    "code": reason_code,
                    "message": "当前账号无项目立项创建权限",
                    "suggested_action": "request_access",
                },
                "data": {
                    "lifecycle_hints": self._build_lifecycle_hints(reason_code),
                    "suggested_action_payload": {
                        "intent": "project.initiation.enter",
                        "reason_code": reason_code,
                        "params": {
                            "reason_code": reason_code,
                        },
                    },
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": str((self.context or {}).get("trace_id") or ""),
                },
            }
        except UserError as exc:
            reason_code = "BUSINESS_RULE_FAILED"
            return {
                "ok": False,
                "error": {
                    "code": reason_code,
                    "message": str(exc) or "项目立项业务校验失败",
                    "suggested_action": "fix_input",
                },
                "data": {
                    "lifecycle_hints": self._build_lifecycle_hints(reason_code),
                    "suggested_action_payload": {
                        "intent": "project.initiation.enter",
                        "reason_code": reason_code,
                        "params": {
                            "reason_code": reason_code,
                        },
                    },
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "elapsed_ms": int((time.time() - ts0) * 1000),
                    "trace_id": str((self.context or {}).get("trace_id") or ""),
                },
            }

        menu_xmlid = "smart_construction_core.menu_sc_project_dashboard"
        menu = self.env.ref(menu_xmlid, raise_if_not_found=False)
        contract_params = {
            "op": "menu",
            "menu_id": int(menu.id) if menu else 0,
            "menu_xmlid": menu_xmlid,
            "project_id": int(project.id),
            "scene_key": "project.dashboard",
        }
        if int(contract_params.get("menu_id") or 0) <= 0:
            contract_params = {
                "op": "model",
                "model": "project.project",
                "project_id": int(project.id),
                "scene_key": "project.dashboard",
            }

        data = {
            "state": "ready",
            "record": {
                "model": "project.project",
                "id": int(project.id),
                "name": str(project.name or ""),
            },
            "suggested_action": "open_project_dashboard",
            "suggested_action_payload": {
                "intent": "project.dashboard.enter",
                "reason_code": "PROJECT_INITIATION_CREATED",
                "params": {
                    "project_id": int(project.id),
                    "reason_code": "PROJECT_INITIATION_CREATED",
                },
            },
            "lifecycle_hints": {
                "stage": "project_created",
                "project_id": int(project.id),
                "scene_key": "project.dashboard",
                "reason_code": "PROJECT_INITIATION_CREATED",
                "primary_action_label": "打开项目驾驶舱",
                "next_step_label": "进入项目管理首页",
                "suggested_action_intent": "project.dashboard.enter",
            },
            "contract_ref": {
                "intent": "ui.contract",
                "params": dict(contract_params),
            },
            "bootstrap_summary": dict(bootstrap_summary or {}),
        }

        return {
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "trace_id": str((self.context or {}).get("trace_id") or ""),
            },
        }
