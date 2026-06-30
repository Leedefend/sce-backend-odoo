#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts" / "codex"
REPORT_PATH = ROOT / "artifacts" / "backend" / "payment_request_approval_chain_summary.json"

SMOKE_SOURCES = {
    "finance_action_smoke": ARTIFACT_ROOT / "payment-request-approval-smoke",
    "finance_executive_handoff_smoke": ARTIFACT_ROOT / "payment-request-approval-handoff-smoke",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _latest_summary(root: Path) -> Path | None:
    if not root.is_dir():
        return None
    candidates = sorted(path for path in root.glob("*/summary.json") if path.is_file())
    return candidates[-1] if candidates else None


def _step_ok(step: object) -> bool:
    if not isinstance(step, dict):
        return False
    return bool(step.get("ok"))


def _summarize_component(name: str, root: Path) -> dict:
    summary_path = _latest_summary(root)
    if summary_path is None:
        return {
            "present": False,
            "ok": False,
            "path": "",
            "step_count": 0,
            "failed_steps": [],
        }

    payload = _load_json(summary_path)
    steps = payload.get("steps") if isinstance(payload.get("steps"), list) else []
    failed_steps = [
        str((step or {}).get("step") or "<unknown>")
        for step in steps
        if not _step_ok(step)
    ]
    return {
        "present": True,
        "ok": bool(steps) and not failed_steps,
        "path": str(summary_path.relative_to(ROOT)),
        "payment_request_id": payload.get("payment_request_id"),
        "auto_created": bool(payload.get("auto_created")),
        "step_count": len(steps),
        "failed_steps": failed_steps,
        "selected_action": payload.get("selected_action") or payload.get("executive_selected_action") or "",
        "followup_selected_action": payload.get("followup_selected_action") or "",
        "followup_skip_reason": payload.get("followup_skip_reason") or "",
    }


def main() -> int:
    components = {
        name: _summarize_component(name, root)
        for name, root in SMOKE_SOURCES.items()
    }
    present_count = sum(1 for item in components.values() if item.get("present"))
    ok = bool(components) and all(bool(item.get("ok")) for item in components.values())
    payload = {
        "generated_at_utc": _utc_now(),
        "ok": ok,
        "summary": {
            "component_count": len(components),
            "present_count": present_count,
            "missing_count": len(components) - present_count,
            "failed_count": sum(1 for item in components.values() if item.get("present") and not item.get("ok")),
        },
        "components": components,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(REPORT_PATH)
    print("[payment_request_approval_chain_summary] PASS" if ok else "[payment_request_approval_chain_summary] INCOMPLETE")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
