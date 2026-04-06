# -*- coding: utf-8 -*-
import time

from odoo.addons.smart_construction_scene.services.scene_package_service import ScenePackageService

from ..core.base_handler import BaseIntentHandler


def _service(env, user):
    return ScenePackageService(env, user)


class ScenePackagesInstalledHandler(BaseIntentHandler):
    INTENT_TYPE = "scene.packages.installed"
    DESCRIPTION = "Installed scene package registry"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = ["smart_core.group_smart_core_scene_admin"]

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
            },
        }
