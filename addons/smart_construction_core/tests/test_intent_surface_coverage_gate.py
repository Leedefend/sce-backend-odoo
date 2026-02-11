# -*- coding: utf-8 -*-
"""Gate-level checks for high-value intent surface coverage signals."""

from __future__ import annotations

from pathlib import Path
import re

from odoo.tests.common import TransactionCase, tagged


REQUIRED_HIGH_VALUE_INTENTS = [
    "system.init",
    "api.data",
    "api.data.batch",
    "execute_button",
    "ui.contract",
    "chatter.post",
    "chatter.timeline",
    "load_contract",
    "load_view",
    "my.work.summary",
    "my.work.complete_batch",
    "usage.report",
]


def _addons_root() -> Path:
    # Runtime path in container: /mnt/extra-addons/smart_construction_core/tests/...
    # Host path also matches this 2-level parent shape.
    return Path(__file__).resolve().parents[2]


def _collect_declared_intents(addons_root: Path) -> set[str]:
    out: set[str] = set()
    for rel_dir in ("smart_core/handlers", "smart_construction_core/handlers"):
        abs_dir = addons_root / rel_dir
        if not abs_dir.exists():
            continue
        for py in abs_dir.glob("*.py"):
            text = py.read_text(encoding="utf-8")
            for match in re.finditer(r'INTENT_TYPE\s*=\s*"([^"]+)"', text):
                out.add(match.group(1).strip())
    return out


def _collect_tests_blob(addons_root: Path) -> str:
    blobs: list[str] = []
    for rel_dir in ("smart_core/tests", "smart_construction_core/tests"):
        abs_dir = addons_root / rel_dir
        if not abs_dir.exists():
            continue
        for py in abs_dir.rglob("test_*.py"):
            blobs.append(py.read_text(encoding="utf-8"))
    return "\n".join(blobs)


def _required_test_ref_intents() -> list[str]:
    # Keep in sync with scripts/verify/baselines/business_increment_readiness_policy.json.
    return list(REQUIRED_HIGH_VALUE_INTENTS)


@tagged("post_install", "-at_install", "sc_gate", "intent_surface_coverage_gate")
class TestIntentSurfaceCoverageGate(TransactionCase):
    def test_high_value_intents_are_declared(self):
        addons_root = _addons_root()
        declared = _collect_declared_intents(addons_root)
        missing = sorted(set(REQUIRED_HIGH_VALUE_INTENTS) - declared)
        self.assertFalse(missing, f"missing high-value intent declarations: {missing}")

    def test_required_test_ref_intents_are_present_in_tests(self):
        required = _required_test_ref_intents()
        tests_blob = _collect_tests_blob(_addons_root())
        missing = sorted([intent for intent in required if intent not in tests_blob])
        self.assertFalse(missing, f"required_test_ref_intents missing in test corpus: {missing}")
