#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_render_profile_interaction_regression_v1.json"


def _run(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    return {
        "code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def run_audit() -> dict:
    backend_cmd = ["python3", "scripts/verify/form_render_profiles_audit.py", "--json"]
    frontend_cmd = ["python3", "scripts/verify/form_render_profile_frontend_consumer_audit.py", "--json"]

    backend_run = _run(backend_cmd)
    frontend_run = _run(frontend_cmd)

    backend_artifact = _read_json(ROOT / "artifacts" / "contract" / "form_render_profiles_v1.json")
    frontend_artifact = _read_json(ROOT / "artifacts" / "contract" / "form_render_profile_frontend_consumer_v1.json")

    backend_summary = backend_artifact.get("summary") if isinstance(backend_artifact.get("summary"), dict) else {}
    frontend_summary = frontend_artifact.get("summary") if isinstance(frontend_artifact.get("summary"), dict) else {}

    backend_pass = backend_run["code"] == 0 and str(backend_summary.get("status") or "") == "PASS"
    frontend_pass = frontend_run["code"] == 0 and str(frontend_summary.get("status") or "") == "PASS"

    pairwise = backend_artifact.get("pairwise_diffs") if isinstance(backend_artifact.get("pairwise_diffs"), dict) else {}
    rights_changed_pairs = [
        key for key, row in pairwise.items()
        if isinstance(row, dict) and bool(row.get("rights_changed"))
    ]

    status = "PASS" if backend_pass and frontend_pass and len(rights_changed_pairs) >= 2 else "BLOCKED"

    payload = {
        "version": "v1",
        "audit": "form_render_profile_interaction_regression",
        "summary": {
            "status": status,
            "backend_pass": backend_pass,
            "frontend_pass": frontend_pass,
            "rights_changed_pairs": rights_changed_pairs,
        },
        "backend": {
            "command": " ".join(backend_cmd),
            "exit_code": backend_run["code"],
            "summary": backend_summary,
        },
        "frontend": {
            "command": " ".join(frontend_cmd),
            "exit_code": frontend_run["code"],
            "summary": frontend_summary,
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit create/edit/readonly interaction regression.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    payload = run_audit()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        summary = payload.get("summary") or {}
        print(
            "status={status} backend_pass={backend} frontend_pass={frontend} rights_pairs={pairs}".format(
                status=summary.get("status"),
                backend=summary.get("backend_pass"),
                frontend=summary.get("frontend_pass"),
                pairs=len(summary.get("rights_changed_pairs") or []),
            )
        )
    if args.strict and (payload.get("summary") or {}).get("status") != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
