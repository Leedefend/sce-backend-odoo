# -*- coding: utf-8 -*-
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from odoo import fields

from .project_dashboard_builders import BUILDERS


_SCENE_CONTENT_MODULE = None
_KERNEL_MODULE = None


def _load_scene_content_module():
    global _SCENE_CONTENT_MODULE
    if _SCENE_CONTENT_MODULE is not None:
        return _SCENE_CONTENT_MODULE
    content_path = None
    try:
        locator_path = Path(__file__).resolve().parents[2] / "smart_scene" / "core" / "provider_locator.py"
        locator_spec = spec_from_file_location("smart_scene_provider_locator_project_dashboard", locator_path)
        if locator_spec is not None and locator_spec.loader is not None:
            locator_module = module_from_spec(locator_spec)
            locator_spec.loader.exec_module(locator_module)
            resolver = getattr(locator_module, "resolve_project_dashboard_scene_content_path", None)
            if callable(resolver):
                content_path = resolver(Path(__file__))
    except Exception:
        content_path = None
    if content_path is None:
        _SCENE_CONTENT_MODULE = False
        return None
    try:
        spec = spec_from_file_location("smart_construction_project_dashboard_scene_content", content_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("spec unavailable")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        _SCENE_CONTENT_MODULE = module
        return module
    except Exception:
        _SCENE_CONTENT_MODULE = False
        return None


def _load_orchestration_kernel_module():
    global _KERNEL_MODULE
    if _KERNEL_MODULE is not None:
        return _KERNEL_MODULE
    kernel_path = Path(__file__).resolve().parents[2] / "smart_scene" / "core" / "dashboard_orchestration_kernel.py"
    try:
        spec = spec_from_file_location("smart_scene_dashboard_orchestration_kernel", kernel_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("spec unavailable")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        _KERNEL_MODULE = module
        return module
    except Exception:
        _KERNEL_MODULE = False
        return None


class ProjectDashboardService:
    """Assemble project.dashboard contract using block builders."""

    ZONE_BLOCKS = (
        ("header", "项目头部信息", "hero", "stack", "block.project.header"),
        ("metrics", "关键指标", "primary", "grid", "block.project.metrics"),
        ("progress", "项目进度", "primary", "stack", "block.project.progress"),
        ("contract", "合同执行", "secondary", "stack", "block.project.contract"),
        ("cost", "成本控制", "secondary", "stack", "block.project.cost"),
        ("finance", "资金情况", "secondary", "stack", "block.project.finance"),
        ("risk", "风险提醒", "supporting", "stack", "block.project.risk"),
    )

    def __init__(self, env):
        self.env = env
        self._builders = [builder_cls(env) for builder_cls in BUILDERS]
        self._builder_map = {builder.block_key: builder for builder in self._builders}
        self._scene_content = self._scene_content_payload()

    def _scene_content_payload(self):
        module = _load_scene_content_module()
        fn = getattr(module, "build_project_dashboard_scene_content", None) if module else None
        if callable(fn):
            try:
                payload = fn()
                if isinstance(payload, dict) and payload:
                    return payload
            except Exception:
                pass
        return {
            "scene": {"key": "project.management", "page": "project.management.dashboard"},
            "page": {"key": "project.management.dashboard", "title": "项目驾驶舱", "route": "/s/project.management"},
            "zone_blocks": [
                {"key": key, "title": title, "zone_type": zone_type, "display_mode": display_mode, "block_key": block_key}
                for key, title, zone_type, display_mode, block_key in self.ZONE_BLOCKS
            ],
        }

    def build(self, project_id=None, context=None):
        ctx = dict(context or {})
        project, project_resolution = self._resolve_project_with_diagnostics(project_id)
        project_payload = self._project_payload(project)
        zones = self._build_zones(project=project, context=ctx)
        scene = self._scene_content.get("scene") if isinstance(self._scene_content.get("scene"), dict) else {}
        page = self._scene_content.get("page") if isinstance(self._scene_content.get("page"), dict) else {}
        return {
            "scene": {
                "key": str(scene.get("key") or "project.management"),
                "page": str(scene.get("page") or "project.management.dashboard"),
            },
            "page": {
                "key": str(page.get("key") or "project.management.dashboard"),
                "title": str(page.get("title") or "项目驾驶舱"),
                "route": str(page.get("route") or "/s/project.management"),
            },
            "route_context": self._route_context(project),
            "project": project_payload,
            "diagnostics": {
                "project_resolution": project_resolution,
            },
            "zones": zones,
        }

    def _build_zones(self, project, context):
        zone_specs = self._scene_content.get("zone_blocks") if isinstance(self._scene_content.get("zone_blocks"), list) else []
        kernel = _load_orchestration_kernel_module()
        fn = getattr(kernel, "build_single_block_zones", None) if kernel else None
        if callable(fn):
            try:
                payload = fn(zone_specs, self._builder_map, project, context, self._error_block)
                if isinstance(payload, dict) and payload:
                    return payload
            except Exception:
                pass
        zones = {}
        for spec in zone_specs:
            if not isinstance(spec, dict):
                continue
            key = str(spec.get("key") or "").strip()
            if not key:
                continue
            block_key = str(spec.get("block_key") or "").strip()
            builder = self._builder_map.get(block_key)
            block = builder.build(project=project, context=context) if builder else self._error_block(block_key, "BLOCK_BUILDER_NOT_FOUND")
            zones[key] = {
                "zone_key": str(spec.get("zone_key") or ("zone.%s" % key)),
                "title": str(spec.get("title") or key),
                "zone_type": str(spec.get("zone_type") or "secondary"),
                "display_mode": str(spec.get("display_mode") or "stack"),
                "blocks": [block],
            }
        return zones

    def _model(self, model_name):
        try:
            return self.env[model_name]
        except Exception:
            return None

    def _project_domain_for_user(self):
        model = self._model("project.project")
        if model is None:
            return []
        f = getattr(model, "_fields", {})
        uid = int(self.env.user.id)
        ors = []
        for field in ("manager_id", "owner_id", "user_id"):
            if field in f:
                ors.append((field, "=", uid))
        for field in ("user_ids", "member_ids", "member_user_ids"):
            if field in f:
                ors.append((field, "in", [uid]))
        if not ors:
            return []
        if len(ors) == 1:
            return [ors[0]]
        return (["|"] * (len(ors) - 1)) + ors

    def _resolve_project(self, project_id):
        project, _diag = self._resolve_project_with_diagnostics(project_id)
        return project

    def _resolve_project_with_diagnostics(self, project_id):
        model_in_env = False
        model_error = ""
        try:
            model_in_env = "project.project" in self.env
        except Exception as exc:
            model_error = str(exc)
        Project = None
        try:
            Project = self.env["project.project"]
        except Exception as exc:
            model_error = str(exc)
        if Project is None:
            return None, {
                "requested_project_id": int(project_id or 0),
                "resolved_project_id": 0,
                "resolution_path": "model_missing",
                "reason": "project.project model not available",
                "model_in_env": model_in_env,
                "model_error": model_error,
            }
        requested_project_id = 0
        try:
            requested_project_id = int(project_id or 0)
        except Exception:
            requested_project_id = 0
        diagnostics = {
            "requested_project_id": requested_project_id,
            "resolved_project_id": 0,
            "resolution_path": "",
            "reason": "",
            "candidate_counts": {},
        }
        if project_id:
            try:
                record = Project.browse(int(project_id)).exists()
                if record:
                    diagnostics.update(
                        {
                            "resolved_project_id": int(record.id),
                            "resolution_path": "explicit_project_id",
                            "reason": "matched explicit project_id",
                        }
                    )
                    return record, diagnostics
                diagnostics["reason"] = "explicit project_id not found or inaccessible"
            except Exception:
                diagnostics["reason"] = "explicit project_id browse failed"
        domain = self._project_domain_for_user()
        diagnostics["user_domain"] = domain
        try:
            if domain:
                diagnostics["candidate_counts"]["user_domain"] = int(Project.search_count(domain))
            else:
                diagnostics["candidate_counts"]["user_domain"] = 0
            record = Project.search(domain, order="write_date desc,id desc", limit=1)
            if record:
                diagnostics.update(
                    {
                        "resolved_project_id": int(record.id),
                        "resolution_path": "user_domain",
                        "reason": "matched project by user ownership/member domain",
                    }
                )
                return record, diagnostics
        except Exception:
            diagnostics["candidate_counts"]["user_domain"] = -1
            diagnostics["reason"] = "user_domain search failed"
        try:
            diagnostics["candidate_counts"]["global"] = int(Project.search_count([]))
            record = Project.search([], order="write_date desc,id desc", limit=1)
            if record:
                diagnostics.update(
                    {
                        "resolved_project_id": int(record.id),
                        "resolution_path": "global_search",
                        "reason": "matched latest project in global search",
                    }
                )
                return record, diagnostics
        except Exception:
            diagnostics["candidate_counts"]["global"] = -1
            diagnostics["reason"] = "global search failed"
        try:
            rows = Project.search_read(
                [("active", "=", True)],
                fields=["id", "name", "write_date"],
                limit=1,
                order="write_date desc,id desc",
            )
            diagnostics["candidate_counts"]["active_search_read"] = int(len(rows or []))
            if rows and rows[0].get("id"):
                record = Project.browse(int(rows[0]["id"])).exists()
                if record:
                    diagnostics.update(
                        {
                            "resolved_project_id": int(record.id),
                            "resolution_path": "active_search_read",
                            "reason": "matched latest active project by search_read fallback",
                        }
                    )
                    return record, diagnostics
        except Exception:
            diagnostics["candidate_counts"]["active_search_read"] = -1
            diagnostics["reason"] = "active search_read fallback failed"
        diagnostics.update(
            {
                "resolved_project_id": 0,
                "resolution_path": diagnostics.get("resolution_path") or "no_match",
                "reason": diagnostics.get("reason") or "no project resolved",
            }
        )
        return None, diagnostics

    def _project_payload(self, project):
        if not project:
            return {
                "id": 0,
                "name": "",
                "project_code": "",
                "partner_name": "",
                "manager_name": "",
                "stage_name": "",
                "state": "empty",
                "date": str(fields.Date.today()),
            }
        return {
            "id": int(project.id),
            "name": str(getattr(project, "name", "") or ""),
            "project_code": str(getattr(project, "project_code", "") or ""),
            "partner_name": str(getattr(getattr(project, "partner_id", None), "display_name", "") or ""),
            "manager_name": str(getattr(getattr(project, "user_id", None), "display_name", "") or ""),
            "stage_name": str(getattr(getattr(project, "stage_id", None), "display_name", "") or ""),
            "state": "ready",
            "date": str(fields.Date.today()),
        }

    @staticmethod
    def _route_context(project):
        route = "/s/project.management"
        query_key = "project_id"
        out = {
            "primary_protocol": "/s/project.management?project_id=<id>",
            "query_key": query_key,
            "scene_route": route,
            "project_route_template": "/s/project.management?project_id={project_id}",
            "project_route": route,
        }
        if project:
            out["project_route"] = "/s/project.management?project_id=%s" % int(project.id)
        return out

    @staticmethod
    def _error_block(block_key, code):
        return {
            "block_key": block_key,
            "block_type": "unknown",
            "title": block_key,
            "state": "error",
            "visibility": {"allowed": True, "reason_code": "OK", "reason": ""},
            "data": {},
            "error": {"code": code, "message": code},
        }
