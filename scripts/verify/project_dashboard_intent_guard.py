#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDLER = ROOT / "addons" / "smart_construction_core" / "handlers" / "project_dashboard.py"
ORCHESTRATOR = ROOT / "addons" / "smart_core" / "orchestration" / "project_dashboard_contract_orchestrator.py"


def _must(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def main():
    text = HANDLER.read_text(encoding="utf-8")
    orchestrator_text = ORCHESTRATOR.read_text(encoding="utf-8")
    required_fragments = [
        'INTENT_TYPE = "project.dashboard"',
        '(params or {}).get("project_id")',
        'payload.get("project_id")',
        '(ctx or {}).get("project_id")',
        'model == "project.project"',
        '(ctx or {}).get("record_id")',
        '"contract_version": "v1"',
        '"trace_id": trace_id',
        '"intent": self.INTENT_TYPE',
        "ProjectDashboardContractOrchestrator",
        "orchestrator.build_contract(project_id=project_id, context=ctx)",
    ]
    for frag in required_fragments:
        _must(frag in text, f"handler missing fragment: {frag}")
    for frag in (
        "class ProjectDashboardContractOrchestrator:",
        "def build_contract(self, project_id=None, context=None):",
        '"scene": {',
        '"route_context": self._route_context(project)',
    ):
        _must(frag in orchestrator_text, f"orchestrator missing fragment: {frag}")
    print("[verify.project.dashboard.intent] PASS")


if __name__ == "__main__":
    main()
