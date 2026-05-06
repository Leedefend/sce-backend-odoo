# -*- coding: utf-8 -*-
import time

from ..core.base_handler import BaseIntentHandler
from ..utils.extension_hooks import call_extension_hook_first


def _service(env, user):
    service_cls = call_extension_hook_first(env, "smart_core_scene_package_service_class", env)
    if service_cls is None:
        raise RuntimeError("scene package service provider is not configured")
    return service_cls(env, user)


class ScenePackagesInstalledHandler(BaseIntentHandler):
    INTENT_TYPE = "scene.packages.installed"
    DESCRIPTION = "Installed scene package registry"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = ["smart_core.group_smart_core_scene_admin"]
    SOURCE_KIND = "scene_package_registry_projection"
    SOURCE_AUTHORITIES = ("sc.scene.package", "sc.scene", "ir.module.module")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls):
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        result = _service(self.env, self.env.user).list_packages()
        return {
            "status": "success",
            "ok": True,
            "data": {
                "packages": result.get("items") if isinstance(result, dict) else [],
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "source_kind": self.SOURCE_KIND,
                "source_authorities": list(self.SOURCE_AUTHORITIES),
                "source_authority": self.source_authority_contract(),
            },
        }
