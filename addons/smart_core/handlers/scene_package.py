# -*- coding: utf-8 -*-
import json
import time

from ..core.base_handler import BaseIntentHandler


def _trace_id_from_context(ctx) -> str:
    try:
        return str((ctx or {}).get("trace_id") or "")
    except Exception:
        return ""


def _service(env, user):
    from odoo.addons.smart_construction_scene.services.scene_package_service import ScenePackageService
    return ScenePackageService(env, user)


class _BaseScenePackageHandler(BaseIntentHandler):
    REQUIRED_GROUPS = ["smart_construction_core.group_sc_cap_config_admin"]

    def _params(self, payload):
        params = (payload or {}).get("params") if isinstance(payload, dict) else payload
        if isinstance(params, dict):
            return params
        if isinstance(payload, dict):
            return payload
        return {}

    def _response(self, ts0, data):
        return {
            "status": "success",
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
            },
        }


class ScenePackageListHandler(_BaseScenePackageHandler):
    INTENT_TYPE = "scene.package.list"
    DESCRIPTION = "List installed scene packages"
    VERSION = "1.0.0"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        result = _service(self.env, self.env.user).list_packages()
        return self._response(ts0, result)


class ScenePackageExportHandler(_BaseScenePackageHandler):
    INTENT_TYPE = "scene.package.export"
    DESCRIPTION = "Export a scene package"
    VERSION = "1.0.0"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        package_name = str(params.get("package_name") or "").strip()
        package_version = str(params.get("package_version") or "").strip()
        scene_channel = str(params.get("scene_channel") or "stable").strip().lower()
        reason = str(params.get("reason") or "scene package export").strip() or "scene package export"
        result = _service(self.env, self.env.user).export_package(
            package_name=package_name,
            package_version=package_version,
            scene_channel=scene_channel,
            reason=reason,
            trace_id=_trace_id_from_context(self.context),
        )
        return self._response(ts0, result)


class ScenePackageDryRunImportHandler(_BaseScenePackageHandler):
    INTENT_TYPE = "scene.package.dry_run_import"
    DESCRIPTION = "Dry-run scene package import"
    VERSION = "1.0.0"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        package_json = params.get("package")
        if package_json is None:
            package_json = params.get("package_json")
        if isinstance(package_json, str):
            try:
                package_json = json.loads(package_json)
            except Exception as exc:
                raise ValueError("package_json invalid") from exc
        result = _service(self.env, self.env.user).dry_run_import(package_json)
        return self._response(ts0, result)


class ScenePackageImportHandler(_BaseScenePackageHandler):
    INTENT_TYPE = "scene.package.import"
    DESCRIPTION = "Import scene package"
    VERSION = "1.0.0"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        package_json = params.get("package")
        if package_json is None:
            package_json = params.get("package_json")
        if isinstance(package_json, str):
            try:
                package_json = json.loads(package_json)
            except Exception as exc:
                raise ValueError("package_json invalid") from exc
        strategy = str(params.get("strategy") or "skip_existing").strip().lower()
        reason = str(params.get("reason") or "").strip()
        result = _service(self.env, self.env.user).import_package(
            package_json=package_json,
            strategy=strategy,
            reason=reason,
            trace_id=_trace_id_from_context(self.context),
        )
        return self._response(ts0, result)
