#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCOREBOARD_PATH = ROOT / "docs" / "product" / "delivery" / "v1" / "delivery_readiness_scoreboard_v1.md"
STATE_PATH = ROOT / "artifacts" / "backend" / "delivery_ci_profile_status.json"

PROFILE_COMMANDS = {
    "strict": "CI_SCENE_DELIVERY_PROFILE=strict make ci.scene.delivery.readiness",
    "restricted": "CI_SCENE_DELIVERY_PROFILE=restricted make ci.scene.delivery.readiness",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _git(cmd: list[str]) -> str:
    result = subprocess.run(cmd, cwd=str(ROOT), check=False, capture_output=True, text=True)
    return (result.stdout or "").strip()


def _replace_snapshot(lines: list[str]) -> list[str]:
    now = _utc_now()
    branch = _git(["git", "branch", "--show-current"]) or "unknown"
    commit_ref = _git(["git", "rev-parse", "--short", "HEAD"]) or "unknown"

    def _replace(prefix: str, value: str) -> None:
        for index, line in enumerate(lines):
            if line.startswith(prefix):
                lines[index] = f"{prefix}{value}"
                return

    _replace("- generated_at_utc: ", now)
    _replace("- branch: `", f"{branch}`")
    _replace("- commit_ref: `", f"{commit_ref}`")
    return lines


def _upsert_evidence_row(lines: list[str], evidence: str, status: str, source: str) -> list[str]:
    row = f"| {evidence} | {status} | `{source}` |"
    for index, line in enumerate(lines):
        if line.startswith(f"| {evidence} |"):
            lines[index] = row
            return lines

    insert_at = -1
    for index, line in enumerate(lines):
        if line.startswith("## 9-Module Readiness Board"):
            insert_at = index
            break
    if insert_at < 0:
        lines.append(row)
    else:
        lines.insert(insert_at, row)
    return lines


def _status_label(state: dict) -> str:
    value = str(state.get("status") or "UNKNOWN").upper()
    if value not in {"PASS", "FAIL", "UNKNOWN"}:
        value = "UNKNOWN"
    ts = str(state.get("last_run_at_utc") or "").strip()
    return f"{value} ({ts})" if ts else value


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh delivery readiness scoreboard snapshot and CI profile status rows")
    parser.add_argument("--profile", choices=["strict", "restricted"], help="CI profile to update")
    parser.add_argument("--status", choices=["PASS", "FAIL"], help="Profile status to persist")
    args = parser.parse_args()

    if bool(args.profile) != bool(args.status):
        raise SystemExit("--profile and --status must be provided together")

    state = _load_json(STATE_PATH)
    profiles = state.get("profiles") if isinstance(state.get("profiles"), dict) else {}
    state = {"profiles": profiles}
    for key in ("strict", "restricted"):
        if key not in state["profiles"] or not isinstance(state["profiles"][key], dict):
            state["profiles"][key] = {
                "status": "UNKNOWN",
                "last_run_at_utc": "",
                "command": PROFILE_COMMANDS[key],
            }

    if args.profile and args.status:
        state["profiles"][args.profile]["status"] = args.status
        state["profiles"][args.profile]["last_run_at_utc"] = _utc_now()
        state["profiles"][args.profile]["command"] = PROFILE_COMMANDS[args.profile]

    _dump_json(STATE_PATH, state)

    if not SCOREBOARD_PATH.is_file():
        raise SystemExit(f"missing scoreboard: {SCOREBOARD_PATH}")

    lines = SCOREBOARD_PATH.read_text(encoding="utf-8").splitlines()
    lines = _replace_snapshot(lines)
    lines = _upsert_evidence_row(
        lines,
        "CI strict profile readiness",
        _status_label(state["profiles"]["strict"]),
        PROFILE_COMMANDS["strict"],
    )
    lines = _upsert_evidence_row(
        lines,
        "CI restricted profile readiness",
        _status_label(state["profiles"]["restricted"]),
        PROFILE_COMMANDS["restricted"],
    )
    SCOREBOARD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(SCOREBOARD_PATH)
    print(STATE_PATH)
    print("[delivery_readiness_scoreboard_refresh] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

