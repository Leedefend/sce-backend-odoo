#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import industry_module_product_boundary_guard as guard


class IndustryModuleProductBoundaryGuardTests(unittest.TestCase):
    def _module_root(self, source: str, *, manifest: str = "{}") -> tuple[tempfile.TemporaryDirectory, Path]:
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        module = root / "addons" / "smart_construction_core"
        (module / "models").mkdir(parents=True)
        (module / "__manifest__.py").write_text(manifest, encoding="utf-8")
        (module / "models" / "sample.py").write_text(source, encoding="utf-8")
        return tmp, root / "addons"

    def test_runtime_bare_pass_boundary_rejects_runtime_pass(self):
        tmp, addons = self._module_root(
            "def sample():\n"
            "    try:\n"
            "        return 1\n"
            "    except Exception:\n"
            "        pass\n"
        )
        with tmp, patch.object(guard, "ROOT", addons.parent), patch.object(guard, "ADDONS", addons):
            errors = guard.verify_runtime_bare_pass_boundary()
        self.assertEqual(len(errors), 1)
        self.assertIn("bare pass", errors[0])
        self.assertIn("models/sample.py:5", errors[0])

    def test_runtime_abstract_boundary_rejects_bare_not_implemented(self):
        tmp, addons = self._module_root(
            "class Sample:\n"
            "    def run(self):\n"
            "        raise NotImplementedError\n"
        )
        with tmp, patch.object(guard, "ROOT", addons.parent), patch.object(guard, "ADDONS", addons):
            errors = guard.verify_runtime_abstract_method_boundary()
        self.assertEqual(len(errors), 1)
        self.assertIn("NotImplementedError", errors[0])
        self.assertIn("models/sample.py", errors[0])

    def test_manifest_shape_rejects_demo_key(self):
        tmp, addons = self._module_root("VALUE = 1\n", manifest="{'data': [], 'demo': []}")
        with (
            tmp,
            patch.object(guard, "ROOT", addons.parent),
            patch.object(guard, "ADDONS", addons),
            patch.object(guard, "INDUSTRY_MODULES", ("smart_construction_core",)),
            patch.object(guard, "ALLOWED_UNDECLARED_XML", {}),
        ):
            errors = guard.verify_manifest_shape()
        self.assertEqual(errors, ["smart_construction_core: production manifest must not declare demo data entries"])


if __name__ == "__main__":
    unittest.main()
