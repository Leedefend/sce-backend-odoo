#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDLER = ROOT / "addons" / "smart_construction_core" / "handlers" / "project_dashboard.py"


def _must(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def main() -> None:
    text = HANDLER.read_text(encoding="utf-8")
    _must("def _resolve_project_id(" in text, "handler _resolve_project_id not found")

    order_tokens = [
        '(params or {}).get("project_id")',
        'payload.get("project_id")',
        '(ctx or {}).get("project_id")',
    ]
    pos = []
    for token in order_tokens:
        idx = text.find(token)
        _must(idx >= 0, f"missing project_id candidate: {token}")
        pos.append(idx)
    _must(pos[0] < pos[1] < pos[2], "project_id candidate order must be params -> payload -> ctx")

    _must('if model == "project.project":' in text, "missing project model guard")
    _must('candidates.append((ctx or {}).get("record_id"))' in text, "missing record_id fallback append")

    print("[verify.project.dashboard.project_id_order] PASS")


if __name__ == "__main__":
    main()
