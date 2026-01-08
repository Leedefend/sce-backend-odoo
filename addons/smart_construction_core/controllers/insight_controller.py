# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from odoo import http
from odoo.http import request

from ..services.insight.project_insight_service import ProjectInsightService


class InsightController(http.Controller):

    @http.route("/api/insight", type="http", auth="user", methods=["GET"], csrf=False)
    def get_insight(self, **params):
        """
        GET /api/insight?model=project.project&id=123&scene=project.entry

        Returns:
          { "ok": true, "data": { ...BusinessInsight... } }
        """
        model = params.get("model", "project.project")
        scene = params.get("scene", "project.entry")
        rid = params.get("id")

        try:
            rid_int = int(rid) if rid is not None else 0
        except Exception:
            return self._json({"ok": False, "error": {"code": "BAD_REQUEST", "message": "Invalid id"}}, status=400)

        if not model or rid_int <= 0:
            return self._json({"ok": False, "error": {"code": "BAD_REQUEST", "message": "model and id required"}}, status=400)

        # Use normal env (no sudo) to enforce ACL/record rules
        env = request.env
        rec = env[model].browse(rid_int).exists()
        if not rec:
            return self._json({"ok": False, "error": {"code": "NOT_FOUND", "message": "Record not found"}}, status=404)

        # Explicit access checks (belt + suspenders)
        try:
            rec.check_access_rights("read")
            rec.check_access_rule("read")
        except Exception:
            return self._json({"ok": False, "error": {"code": "FORBIDDEN", "message": "Access denied"}}, status=403)

        # Only support project.project for now (MVP)
        if model != "project.project":
            return self._json(
                {"ok": False, "error": {"code": "NOT_SUPPORTED", "message": "Only project.project supported currently"}},
                status=400,
            )

        service = ProjectInsightService(env)
        data = service.get_insight(rec, scene=scene)

        return self._json({"ok": True, "data": data}, status=200)

    def _json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False)
        headers = [("Content-Type", "application/json; charset=utf-8")]
        return request.make_response(body, headers=headers, status=status)
