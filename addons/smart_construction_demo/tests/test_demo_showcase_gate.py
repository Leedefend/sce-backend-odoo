# -*- coding: utf-8 -*-
import os
import re

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_gate", "demo_gate")
class TestDemoShowcaseGate(TransactionCase):
    """Prevent demo filters from leaking into core business entries."""

    def test_no_demo_showcase_filters_in_core(self):
        demo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        addons_root = os.path.abspath(os.path.join(demo_root, os.pardir))
        module_root = os.path.join(addons_root, "smart_construction_core")
        allow_path = os.path.join("models", "core", "project_core.py")
        allow_pattern = re.compile(r"\bsc_demo_showcase_ready\s*=\s*fields\.Boolean\b")

        hits = []
        for root, _, files in os.walk(module_root):
            if "__pycache__" in root:
                continue
            for name in files:
                if not (name.endswith(".py") or name.endswith(".xml")):
                    continue
                path = os.path.join(root, name)
                with open(path, "r", encoding="utf-8") as handle:
                    content = handle.read()
                if "sc_demo_showcase_ready" not in content:
                    continue
                rel_path = os.path.relpath(path, module_root)
                if rel_path.startswith("tests" + os.sep):
                    continue
                for idx, line in enumerate(content.splitlines(), start=1):
                    if "sc_demo_showcase_ready" not in line:
                        continue
                    if rel_path.endswith(allow_path) and allow_pattern.search(line):
                        continue
                    hits.append(f"{rel_path}:{idx}")

        self.assertFalse(
            hits,
            "禁止 core 模块硬编码 demo 过滤（sc_demo_showcase_ready），命中：%s"
            % ", ".join(hits),
        )
