#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "artifacts" / "v2" / "v2_focus_intent_compare_snapshot_v1.json"


def run_audit() -> Dict[str, object]:
    errors: List[str] = []
    if not SNAPSHOT.exists():
        return {"gate_version": "v1", "gate_profile": "full", "status": "FAIL", "errors": ["missing_snapshot"]}

    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    required = list(snap.get("required_compare_fields") or [])

    sys.path.insert(0, str(ROOT / "addons" / "smart_core"))
    from core.intent_shadow_compare_executor import run_shadow_compare  # type: ignore
    from v2.dispatcher import dispatch_intent  # type: ignore

    compare = run_shadow_compare(
        intent="meta.describe_model",
        route_mode="v2_shadow",
        params={"model": "res.partner"},
        context={"trace_id": "compare-meta-describe-1674", "user_id": 1, "company_id": 1},
        v1_result={"ok": True, "data": {"model": "res.partner"}, "meta": {"intent": "meta.describe_model"}},
        v2_runner=lambda i, p, c: dispatch_intent(intent=i, payload=p, context=c),
    )

    for key in required:
        if key not in compare:
            errors.append(f"missing_compare_field:{key}")
    if str(compare.get("intent") or "") != "meta.describe_model":
        errors.append("intent_mismatch")
    if str(compare.get("v2_status") or "") != "ok":
        errors.append("v2_status_not_ok")

    return {"gate_version": "v1", "gate_profile": "full", "status": "PASS" if not errors else "FAIL", "errors": errors, "compare": compare}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_audit()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
