#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORE_EXTENSION = ROOT / "addons" / "smart_construction_core" / "core_extension.py"
HANDLER = ROOT / "addons" / "smart_construction_core" / "handlers" / "project_dashboard.py"
ORCHESTRATOR = ROOT / "addons" / "smart_core" / "orchestration" / "project_dashboard_contract_orchestrator.py"


def _must(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def _check_core_extension() -> None:
    text = CORE_EXTENSION.read_text(encoding="utf-8")
    required = [
        "from odoo.addons.smart_construction_core.handlers.project_dashboard import (",
        "ProjectDashboardHandler",
        'registry["project.dashboard"] = ProjectDashboardHandler',
    ]
    for frag in required:
        _must(frag in text, f"core_extension missing fragment: {frag}")


def _check_handler() -> None:
    text = HANDLER.read_text(encoding="utf-8")
    required = [
        'INTENT_TYPE = "project.dashboard"',
        'DESCRIPTION = "Project management dashboard contract"',
        "ProjectDashboardContractOrchestrator(self.env)",
        "data = orchestrator.build_contract(project_id=project_id, context=ctx)",
        '"intent": self.INTENT_TYPE',
        '"contract_version": "v1"',
    ]
    for frag in required:
        _must(frag in text, f"handler missing fragment: {frag}")


def _check_orchestrator() -> None:
    text = ORCHESTRATOR.read_text(encoding="utf-8")
    required = [
        "ZONE_BLOCKS = (",
        "def build_contract(self, project_id=None, context=None):",
        '"scene": {',
        '"key": "project.management"',
        '"page": "project.management.dashboard"',
        '"route_context": self._route_context(project)',
        '"zones": zones',
    ]
    for frag in required:
        _must(frag in text, f"service missing fragment: {frag}")


def main() -> None:
    _check_core_extension()
    _check_handler()
    _check_orchestrator()
    print("[verify.project.dashboard.runtime_chain] PASS")


if __name__ == "__main__":
    main()
