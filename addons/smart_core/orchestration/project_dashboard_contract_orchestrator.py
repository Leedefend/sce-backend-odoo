# -*- coding: utf-8 -*-
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from odoo.addons.smart_construction_core.services.project_dashboard_service import (
    ProjectDashboardService,
)


_SCENE_CONTENT_MODULE = None
_KERNEL_MODULE = None
_SCENE_ENGINE_MODULE = None


def _load_scene_content_module():
    global _SCENE_CONTENT_MODULE
    if _SCENE_CONTENT_MODULE is not None:
        return _SCENE_CONTENT_MODULE
    content_path = None
    try:
        registry_path = Path(__file__).resolve().parents[2] / "smart_scene" / "core" / "scene_provider_registry.py"
        locator_spec = spec_from_file_location("smart_scene_provider_registry_project_dashboard", registry_path)
        if locator_spec is not None and locator_spec.loader is not None:
            locator_module = module_from_spec(locator_spec)
            locator_spec.loader.exec_module(locator_module)
            resolver = getattr(locator_module, "resolve_scene_provider_path", None)
            if callable(resolver):
                content_path = resolver("project.dashboard", Path(__file__))
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


def _load_scene_engine_module():
    global _SCENE_ENGINE_MODULE
    if _SCENE_ENGINE_MODULE is not None:
        return _SCENE_ENGINE_MODULE
    engine_path = Path(__file__).resolve().parents[2] / "smart_scene" / "core" / "scene_engine.py"
    try:
        spec = spec_from_file_location("smart_scene_core_scene_engine", engine_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("spec unavailable")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        _SCENE_ENGINE_MODULE = module
        return module
    except Exception:
        _SCENE_ENGINE_MODULE = False
        return None


class ProjectDashboardContractOrchestrator:
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
        self._service = ProjectDashboardService(env)
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

    def build_contract(self, project_id=None, context=None):
        ctx = dict(context or {})
        project, project_resolution = self._service.resolve_project_with_diagnostics(project_id)
        project_payload = self._service.project_payload(project)
        zones = self._build_zones(project=project, context=ctx)
        scene = self._scene_content.get("scene") if isinstance(self._scene_content.get("scene"), dict) else {}
        page = self._scene_content.get("page") if isinstance(self._scene_content.get("page"), dict) else {}
        diagnostics = {
            "project_resolution": project_resolution,
        }
        scene_engine = _load_scene_engine_module()
        engine_fn = getattr(scene_engine, "build_scene_contract_from_specs", None) if scene_engine else None
        if callable(engine_fn):
            contract = engine_fn(
                scene_hint=scene,
                page_hint=page,
                zone_specs=self._scene_content.get("zone_blocks") if isinstance(self._scene_content.get("zone_blocks"), list) else [],
                built_zones=zones,
                record={"project": project_payload},
                diagnostics=diagnostics,
            )
            contract["route_context"] = self._route_context(project)
            contract["project"] = project_payload
            return contract

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
            "diagnostics": diagnostics,
            "zones": zones,
        }

    def build_dashboard_contract_v1(self, raw_data, *, project_id=0):
        payload = raw_data if isinstance(raw_data, dict) else {}
        zones = payload.get("zones") if isinstance(payload.get("zones"), dict) else {}
        summary_block = self._extract_zone_block(zones, "metrics", "header", "dashboard_summary")
        progress_block = self._extract_zone_block(zones, "progress", "dashboard_progress")
        next_actions_block = self._extract_zone_block(zones, "risk", "dashboard_risk")

        if not summary_block:
            summary_block = {
                "key": "block.project.dashboard.summary.placeholder",
                "state": "empty",
                "data": {"summary": {}},
            }
        if not progress_block:
            progress_block = {
                "key": "block.project.dashboard.progress.placeholder",
                "state": "empty",
                "data": {"progress": {}},
            }
        if not next_actions_block:
            next_actions_block = {
                "key": "block.project.dashboard.next_actions.placeholder",
                "state": "empty",
                "data": {
                    "actions": [
                        {
                            "key": "open_workspace_overview",
                            "label": "返回工作区",
                            "intent": "ui.contract",
                        }
                    ]
                },
            }

        return {
            "kind": "project_dashboard_contract_v1",
            "scene_key": "project.dashboard",
            "project_context": {"project_id": int(project_id or 0)},
            "blocks": [
                {"key": "summary", "block": summary_block},
                {"key": "progress", "block": progress_block},
                {"key": "next_actions", "block": next_actions_block},
            ],
        }

    def _build_zones(self, project, context):
        zone_specs = self._scene_content.get("zone_blocks") if isinstance(self._scene_content.get("zone_blocks"), list) else []
        kernel = _load_orchestration_kernel_module()
        fn = getattr(kernel, "build_single_block_zones", None) if kernel else None
        if callable(fn):
            try:
                payload = fn(zone_specs, self._service._builder_map, project, context, self._service.error_block)
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
            builder = self._service._builder_map.get(block_key)
            block = builder.build(project=project, context=context) if builder else self._service.error_block(block_key, "BLOCK_BUILDER_NOT_FOUND")
            zones[key] = {
                "zone_key": str(spec.get("zone_key") or ("zone.%s" % key)),
                "title": str(spec.get("title") or key),
                "zone_type": str(spec.get("zone_type") or "secondary"),
                "display_mode": str(spec.get("display_mode") or "stack"),
                "blocks": [block],
            }
        return zones

    @staticmethod
    def _extract_zone_block(zones, *keys):
        if not isinstance(zones, dict):
            return {}
        for key in keys:
            zone = zones.get(key) if isinstance(zones.get(key), dict) else {}
            blocks = zone.get("blocks") if isinstance(zone.get("blocks"), list) else []
            if blocks and isinstance(blocks[0], dict):
                return blocks[0]
        return {}

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
