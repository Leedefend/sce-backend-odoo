# -*- coding: utf-8 -*-
import json
import time

from ..core.base_handler import BaseIntentHandler
from ..utils.extension_hooks import call_extension_hook_first

ALLOWED_SCENE_CHANNELS = {"stable", "beta", "dev"}


def _trace_id_from_context(ctx) -> str:
    try:
        return str((ctx or {}).get("trace_id") or "")
    except Exception:
        return ""


def _service(env, user):
    service_cls = call_extension_hook_first(env, "smart_core_scene_package_service_class", env)
    if service_cls is None:
        raise RuntimeError("scene package service provider is not configured")
    return service_cls(env, user)


class _BaseScenePackageHandler(BaseIntentHandler):
    REQUIRED_GROUPS = ["smart_core.group_smart_core_scene_admin"]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "scene_delivery_governance"
    SOURCE_AUTHORITIES = ("sc.scene", "sc.capability", "ir.ui.menu", "ir.actions", "res.groups")
    NO_BUSINESS_FACT_AUTHORITY = True

    def _params(self, payload):
        params = (payload or {}).get("params") if isinstance(payload, dict) else payload
        if isinstance(params, dict):
            return params
        if isinstance(payload, dict):
            return payload
        return {}

    def _err(self, code, message):
        return {
            "ok": False,
            "error": {"code": code, "message": message},
            "code": code,
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract()},
        }

    def _text_param(self, params, key, *, default=""):
        raw = params.get(key, default)
        if raw is None or raw == "":
            return default, None
        if isinstance(raw, bool) or not isinstance(raw, (str, int, float)):
            return "", self._err(400, f"{key} 无效")
        text = str(raw).strip()
        return text or default, None

    def _package_json_param(self, params):
        package_json = params.get("package")
        if package_json is None:
            package_json = params.get("package_json")
        if isinstance(package_json, str):
            try:
                package_json = json.loads(package_json)
            except Exception:
                return None, self._err(400, "package_json 无效")
        if not isinstance(package_json, dict):
            return None, self._err(400, "package_json 无效")
        return package_json, None

    def _response(self, ts0, data):
        return {
            "status": "success",
            "ok": True,
            "data": data,
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "source_authority": self._source_authority_contract(),
            },
        }

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "delivery_only": True,
            "no_business_fact_authority": self.NO_BUSINESS_FACT_AUTHORITY,
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
        package_name, package_name_error = self._text_param(params, "package_name")
        if package_name_error:
            return package_name_error
        package_version, package_version_error = self._text_param(params, "package_version")
        if package_version_error:
            return package_version_error
        scene_channel, scene_channel_error = self._text_param(params, "scene_channel", default="stable")
        if scene_channel_error:
            return scene_channel_error
        scene_channel = scene_channel.lower()
        if scene_channel not in ALLOWED_SCENE_CHANNELS:
            return self._err(400, "scene_channel 无效")
        reason, reason_error = self._text_param(params, "reason", default="scene package export")
        if reason_error:
            return reason_error
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
        package_json, package_error = self._package_json_param(params)
        if package_error:
            return package_error
        result = _service(self.env, self.env.user).dry_run_import(package_json)
        return self._response(ts0, result)


class ScenePackageImportHandler(_BaseScenePackageHandler):
    INTENT_TYPE = "scene.package.import"
    DESCRIPTION = "Import scene package"
    VERSION = "1.0.0"

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = self._params(payload)
        package_json, package_error = self._package_json_param(params)
        if package_error:
            return package_error
        strategy, strategy_error = self._text_param(params, "strategy", default="skip_existing")
        if strategy_error:
            return strategy_error
        strategy = strategy.lower()
        reason, reason_error = self._text_param(params, "reason")
        if reason_error:
            return reason_error
        result = _service(self.env, self.env.user).import_package(
            package_json=package_json,
            strategy=strategy,
            reason=reason,
            trace_id=_trace_id_from_context(self.context),
        )
        return self._response(ts0, result)
