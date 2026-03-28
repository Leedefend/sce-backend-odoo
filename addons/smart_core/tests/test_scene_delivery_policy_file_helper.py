# -*- coding: utf-8 -*-
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_delivery_policy_file_helper.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("scene_delivery_policy_file_helper_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
load_surface_policy_payload_from_file = TARGET.load_surface_policy_payload_from_file
resolve_default_surface_from_file = TARGET.resolve_default_surface_from_file
resolve_policy_file_path = TARGET.resolve_policy_file_path
surface_policy_default_file = TARGET.surface_policy_default_file


class TestSceneDeliveryPolicyFileHelper(unittest.TestCase):
    def test_surface_policy_default_file_prefers_hook_value(self):
        hook = lambda env, name, *_: "docs/custom/policy.json" if name == "smart_core_surface_policy_file_default" else None
        self.assertEqual(
            surface_policy_default_file(None, hook=hook, default_file="docs/default.json"),
            "docs/custom/policy.json",
        )

    def test_resolve_policy_file_path_and_payload_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rel = "policy.json"
            path = Path(tmpdir) / rel
            path.write_text('{"default_surface":"showcase"}', encoding="utf-8")
            previous = os.environ.get("SCENE_DELIVERY_POLICY_FILE")
            os.environ["SCENE_DELIVERY_POLICY_FILE"] = str(path)
            try:
                cache = {"path": "", "mtime": -1.0, "payload": {}}
                resolved = resolve_policy_file_path(None, default_file_resolver=lambda env: rel)
                self.assertEqual(resolved, str(path))
                payload = load_surface_policy_payload_from_file(None, cache=cache, default_file_resolver=lambda env: rel)
                self.assertEqual(payload.get("default_surface"), "showcase")
                payload2 = load_surface_policy_payload_from_file(None, cache=cache, default_file_resolver=lambda env: rel)
                self.assertEqual(payload2.get("default_surface"), "showcase")
            finally:
                if previous is None:
                    os.environ.pop("SCENE_DELIVERY_POLICY_FILE", None)
                else:
                    os.environ["SCENE_DELIVERY_POLICY_FILE"] = previous

    def test_resolve_default_surface_from_file(self):
        payload_loader = lambda env: {"default_surface": " Showcase "}
        normalize = lambda value: str(value or "").strip().lower() or "default"
        self.assertEqual(
            resolve_default_surface_from_file(None, payload_loader=payload_loader, normalize_surface=normalize),
            "showcase",
        )


if __name__ == "__main__":
    unittest.main()
