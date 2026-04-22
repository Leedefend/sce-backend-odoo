# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


SMART_CORE_DIR = Path(__file__).resolve().parents[1]


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


sys.modules.setdefault("odoo", types.ModuleType("odoo"))
sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
smart_core_pkg.__path__ = [str(SMART_CORE_DIR)]
governance_pkg = sys.modules.setdefault("odoo.addons.smart_core.governance", types.ModuleType("odoo.addons.smart_core.governance"))
governance_pkg.__path__ = [str(SMART_CORE_DIR / "governance")]
utils_pkg = sys.modules.setdefault("odoo.addons.smart_core.utils", types.ModuleType("odoo.addons.smart_core.utils"))
utils_pkg.__path__ = [str(SMART_CORE_DIR / "utils")]

reason_codes = types.ModuleType("odoo.addons.smart_core.utils.reason_codes")
reason_codes.REASON_OK = "OK"
reason_codes.REASON_PERMISSION_DENIED = "PERMISSION_DENIED"
reason_codes.failure_meta_for_reason = lambda code: {"reason_code": code}
sys.modules["odoo.addons.smart_core.utils.reason_codes"] = reason_codes

drift_engine = types.ModuleType("odoo.addons.smart_core.governance.scene_drift_engine")


def _append_resolve_error(resolve_errors, **kwargs):
    if isinstance(resolve_errors, list):
        resolve_errors.append(kwargs)


drift_engine.append_resolve_error = _append_resolve_error
sys.modules["odoo.addons.smart_core.governance.scene_drift_engine"] = drift_engine

target = _load_module(
    "odoo.addons.smart_core.governance.scene_normalizer",
    SMART_CORE_DIR / "governance" / "scene_normalizer.py",
)


class _RefRecord:
    def __init__(self, record_id: int):
        self.id = record_id


class _StubEnv:
    def __init__(self, refs: dict[str, int]):
        self._refs = refs

    def ref(self, xmlid: str, raise_if_not_found: bool = False):
        record_id = self._refs.get(xmlid)
        if record_id is None:
            return None
        return _RefRecord(record_id)


class TestSceneNormalizerEntryTarget(unittest.TestCase):
    def test_resolve_targets_adds_scene_entry_target(self):
        normalizer = target.SceneNormalizer()
        scenes = [
            {
                "code": "projects.list",
                "target": {
                    "model": "project.project",
                    "record_id": 42,
                    "action_xmlid": "smart_construction_core.action_sc_project_list",
                    "menu_xmlid": "smart_construction_core.menu_sc_root",
                },
            }
        ]
        diagnostics = {
            "normalize_warnings": [],
            "resolve_errors": [],
        }
        env = _StubEnv(
            {
                "smart_construction_core.action_sc_project_list": 502,
                "smart_construction_core.menu_sc_root": 202,
            }
        )

        normalizer.resolve_targets(env, scenes, [], diagnostics)

        target_payload = (scenes[0] or {}).get("target") or {}
        self.assertEqual((target_payload.get("entry_target") or {}).get("type"), "scene")
        self.assertEqual((target_payload.get("entry_target") or {}).get("scene_key"), "projects.list")
        self.assertEqual((((target_payload.get("entry_target") or {}).get("compatibility_refs") or {}).get("action_id")), 502)
        self.assertEqual((((target_payload.get("entry_target") or {}).get("compatibility_refs") or {}).get("menu_id")), 202)
        self.assertEqual((((target_payload.get("entry_target") or {}).get("record_entry") or {}).get("model")), "project.project")
        self.assertEqual((((target_payload.get("entry_target") or {}).get("record_entry") or {}).get("record_id")), 42)
        self.assertEqual((((target_payload.get("entry_target") or {}).get("record_entry") or {}).get("action_id")), 502)
        self.assertEqual((((target_payload.get("entry_target") or {}).get("record_entry") or {}).get("menu_id")), 202)


if __name__ == "__main__":
    unittest.main()
