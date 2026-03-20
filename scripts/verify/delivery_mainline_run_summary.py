#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "backend" / "delivery_mainline_run_summary.json"
REPORT_MD = ROOT / "artifacts" / "backend" / "delivery_mainline_run_summary.md"

ALLOWED = {"PASS", "FAIL", "SKIP"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git(cmd: list[str]) -> str:
    result = subprocess.run(cmd, cwd=str(ROOT), check=False, capture_output=True, text=True)
    return (result.stdout or "").strip()


def _norm_status(value: str) -> str:
    status = str(value or "").strip().upper()
    return status if status in ALLOWED else "FAIL"


def main() -> int:
    parser = argparse.ArgumentParser(description="Write delivery mainline run summary artifact")
    parser.add_argument("--profile", default="restricted")
    parser.add_argument("--frontend", required=True)
    parser.add_argument("--scene", required=True)
    parser.add_argument("--action-closure", required=True)
    parser.add_argument("--governance", required=True)
    args = parser.parse_args()

    frontend = _norm_status(args.frontend)
    scene = _norm_status(args.scene)
    action_closure = _norm_status(args.action_closure)
    governance = _norm_status(args.governance)
    ok = frontend == "PASS" and scene == "PASS" and action_closure == "PASS" and governance == "PASS"

    payload = {
        "generated_at_utc": _utc_now(),
        "branch": _git(["git", "branch", "--show-current"]) or "unknown",
        "commit_ref": _git(["git", "rev-parse", "--short", "HEAD"]) or "unknown",
        "profile": str(args.profile or "restricted").strip(),
        "ok": ok,
        "steps": {
            "frontend_gate": frontend,
            "scene_delivery_readiness": scene,
            "action_closure_smoke": action_closure,
            "governance_truth": governance,
        },
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Delivery Mainline Run Summary",
        "",
        f"- generated_at_utc: {payload['generated_at_utc']}",
        f"- branch: {payload['branch']}",
        f"- commit_ref: {payload['commit_ref']}",
        f"- profile: {payload['profile']}",
        f"- ok: {payload['ok']}",
        "",
        "| step | status |",
        "|---|---|",
        f"| frontend_gate | {frontend} |",
        f"| scene_delivery_readiness | {scene} |",
        f"| action_closure_smoke | {action_closure} |",
        f"| governance_truth | {governance} |",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(REPORT_JSON)
    print(REPORT_MD)
    print("[delivery_mainline_run_summary] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
