#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "backend_contract_closure_mainline_summary.json"


def _norm(status: str) -> str:
    text = str(status or "").strip().upper()
    if text in {"PASS", "FAIL", "SKIP"}:
        return text
    return "FAIL"


def main() -> int:
    parser = argparse.ArgumentParser(description="Write backend contract closure mainline summary artifact")
    parser.add_argument("--structure", default="PASS")
    parser.add_argument("--snapshot", default="PASS")
    parser.add_argument("--alias", default="PASS")
    args = parser.parse_args()

    structure = _norm(args.structure)
    snapshot = _norm(args.snapshot)
    alias = _norm(args.alias)
    overall_ok = structure == "PASS" and snapshot == "PASS" and alias == "PASS"

    payload = {
        "ok": overall_ok,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "closure_structure_guard": structure,
            "closure_snapshot_guard": snapshot,
            "intent_alias_snapshot_guard": alias,
        },
        "overall": {
            "status": "PASS" if overall_ok else "FAIL",
            "policy": "backend_contract_closure_mainline_v1",
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[backend_contract_closure_mainline_summary] wrote {OUT_JSON.relative_to(ROOT).as_posix()}")
    print(f"[backend_contract_closure_mainline_summary] overall={payload['overall']['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

