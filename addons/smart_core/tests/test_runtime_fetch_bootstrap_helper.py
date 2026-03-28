# -*- coding: utf-8 -*-
import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "runtime_fetch_bootstrap_helper.py"


def _load_target_module():
    sys.modules.setdefault("odoo", SimpleNamespace())
    spec = importlib.util.spec_from_file_location("runtime_fetch_bootstrap_helper_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
build_runtime_fetch_bootstrap_surface = TARGET.build_runtime_fetch_bootstrap_surface


class _FakeSurfaceContext:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class _FakeSurfaceBuilder:
    last_surface_ctx = None

    @classmethod
    def apply(cls, *, surface_ctx):
        cls.last_surface_ctx = surface_ctx
        surfaced = dict(surface_ctx.kwargs.get("data") or {})
        surfaced["surface_applied"] = True
        return surfaced, {"diagnostics": "ok"}


class TestRuntimeFetchBootstrapHelper(unittest.TestCase):
    def test_bootstrap_surface_applies_extensions_before_surface(self):
        calls = []
        data = {"base": True}
        components = {"capability_surface_engine": "capability-engine"}

        def run_extension_hooks_fn(env, hook_name, payload, *args):
            calls.append(("hook", hook_name))
            payload["hook_applied"] = True

        def merge_extension_facts_fn(payload):
            calls.append(("merge", payload.get("hook_applied")))
            payload["merged"] = True

        surfaced = build_runtime_fetch_bootstrap_surface(
            data=data,
            env="env",
            user="user",
            contract_mode="runtime",
            components=components,
            identity_resolver="resolver",
            user_groups_xmlids=["base.group_user"],
            build_capability_groups_fn="cap-group-fn",
            apply_contract_governance_fn="governance-fn",
            scene_diagnostics_builder="diag-builder",
            run_extension_hooks_fn=run_extension_hooks_fn,
            merge_extension_facts_fn=merge_extension_facts_fn,
            surface_context_cls=_FakeSurfaceContext,
            surface_builder=_FakeSurfaceBuilder,
        )

        self.assertEqual(calls, [("hook", "smart_core_extend_system_init"), ("merge", True)])
        self.assertTrue(surfaced.get("hook_applied"))
        self.assertTrue(surfaced.get("merged"))
        self.assertTrue(surfaced.get("surface_applied"))

    def test_bootstrap_surface_passes_runtime_context_into_surface_context(self):
        data = {"base": True}
        components = {"capability_surface_engine": "capability-engine"}

        surfaced = build_runtime_fetch_bootstrap_surface(
            data=data,
            env="env",
            user="user",
            contract_mode="compact",
            components=components,
            identity_resolver="resolver",
            user_groups_xmlids=["group.a"],
            build_capability_groups_fn="cap-group-fn",
            apply_contract_governance_fn="governance-fn",
            scene_diagnostics_builder="diag-builder",
            run_extension_hooks_fn=lambda *args, **kwargs: None,
            merge_extension_facts_fn=lambda payload: payload.update({"merged": True}),
            surface_context_cls=_FakeSurfaceContext,
            surface_builder=_FakeSurfaceBuilder,
        )

        ctx = _FakeSurfaceBuilder.last_surface_ctx
        self.assertEqual(ctx.kwargs.get("contract_mode"), "compact")
        self.assertEqual(ctx.kwargs.get("capability_surface_engine"), "capability-engine")
        self.assertEqual(ctx.kwargs.get("identity_resolver"), "resolver")
        self.assertEqual(ctx.kwargs.get("user_groups_xmlids"), ["group.a"])
        self.assertEqual(ctx.kwargs.get("nav_tree"), [])
        self.assertTrue(surfaced.get("merged"))


if __name__ == "__main__":
    unittest.main()
