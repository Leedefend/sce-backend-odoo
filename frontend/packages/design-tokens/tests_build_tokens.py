from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_tokens import resolve_refs, validate_flat_tokens  # type: ignore


class BuildTokensTests(unittest.TestCase):
    def test_resolve_base_reference(self):
        tokens = {
            "base.color.blue_500": "#2563eb",
            "semantic.surface.interactive": "{color.blue_500}",
        }
        out = resolve_refs(tokens, strict=True)
        self.assertEqual(out["semantic.surface.interactive"], "#2563eb")

    def test_whole_ref_preserves_number_type(self):
        tokens = {
            "base.space.lg": 16,
            "component.button.padding_x": "{space.lg}",
        }
        out = resolve_refs(tokens, strict=True)
        self.assertEqual(out["component.button.padding_x"], 16)
        self.assertIsInstance(out["component.button.padding_x"], int)

    def test_circular_reference_raises(self):
        tokens = {
            "base.a": "{base.b}",
            "base.b": "{base.a}",
        }
        with self.assertRaises(ValueError):
            resolve_refs(tokens, strict=True)

    def test_validate_required_keys(self):
        with self.assertRaises(ValueError):
            validate_flat_tokens({"semantic.surface.page": "#fff"})


if __name__ == "__main__":
    unittest.main()
