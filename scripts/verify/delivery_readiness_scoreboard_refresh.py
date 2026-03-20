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
SUMMARY_PATH = ROOT / "artifacts" / "backend" / "delivery_readiness_ci_summary.json"
SUMMARY_MD_PATH = ROOT / "artifacts" / "backend" / "delivery_readiness_ci_summary.md"

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


def _to_summary_payload(state: dict) -> dict:
    profiles = state.get("profiles") if isinstance(state.get("profiles"), dict) else {}

    def _profile(name: str) -> dict:
        row = profiles.get(name) if isinstance(profiles.get(name), dict) else {}
        status = str(row.get("status") or "UNKNOWN").upper()
        return {
            "status": status,
            "ok": status == "PASS",
            "last_run_at_utc": str(row.get("last_run_at_utc") or "").strip(),
            "command": str(row.get("command") or PROFILE_COMMANDS[name]).strip(),
        }

    return {
        "generated_at_utc": _utc_now(),
        "scoreboard": {
            "path": str(SCOREBOARD_PATH.relative_to(ROOT)),
            "branch": _git(["git", "branch", "--show-current"]) or "unknown",
            "commit_ref": _git(["git", "rev-parse", "--short", "HEAD"]) or "unknown",
        },
        "profiles": {
            "strict": _profile("strict"),
            "restricted": _profile("restricted"),
        },
    }


def _to_summary_markdown(payload: dict) -> str:
    scoreboard = payload.get("scoreboard") if isinstance(payload.get("scoreboard"), dict) else {}
    profiles = payload.get("profiles") if isinstance(payload.get("profiles"), dict) else {}
    strict = profiles.get("strict") if isinstance(profiles.get("strict"), dict) else {}
    restricted = profiles.get("restricted") if isinstance(profiles.get("restricted"), dict) else {}

    lines = [
        "# Delivery Readiness CI Summary",
        "",
        f"- generated_at_utc: {payload.get('generated_at_utc', '')}",
        f"- branch: {scoreboard.get('branch', '')}",
        f"- commit_ref: {scoreboard.get('commit_ref', '')}",
        f"- scoreboard: {scoreboard.get('path', '')}",
        "",
        "## Profiles",
        "",
        "| profile | status | ok | last_run_at_utc | command |",
        "|---|---|---|---|---|",
        "| strict | {status} | {ok} | {last} | `{cmd}` |".format(
            status=strict.get("status", ""),
            ok=str(strict.get("ok", "")),
            last=str(strict.get("last_run_at_utc", "")),
            cmd=str(strict.get("command", "")),
        ),
        "| restricted | {status} | {ok} | {last} | `{cmd}` |".format(
            status=restricted.get("status", ""),
            ok=str(restricted.get("ok", "")),
            last=str(restricted.get("last_run_at_utc", "")),
            cmd=str(restricted.get("command", "")),
        ),
    ]
    return "\n".join(lines) + "\n"


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


def _normalize_evidence_table(lines: list[str]) -> list[str]:
    start = -1
    end = -1
    for index, line in enumerate(lines):
        if line.strip() == "## System-Bound Evidence Summary":
            start = index
            break
    if start < 0:
        return lines
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    if end < 0:
        end = len(lines)

    section = lines[start:end]
    normalized: list[str] = []
    previous_was_table_row = False
    for line in section:
        is_table_row = line.startswith("|")
        if not line.strip() and previous_was_table_row:
            continue
        normalized.append(line)
        previous_was_table_row = is_table_row

    return lines[:start] + normalized + lines[end:]


def _upsert_release_gap_profile_posture(lines: list[str], strict_label: str, restricted_label: str) -> list[str]:
    section_header = "## Release Blocking Gaps (Current)"
    start = -1
    end = -1
    for index, line in enumerate(lines):
        if line.strip() == section_header:
            start = index
            break
    if start < 0:
        return lines
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    if end < 0:
        end = len(lines)

    posture_line = (
        f"5. CI profile posture: strict={strict_label}, restricted={restricted_label}; "
        "release execution should use strict in live-enabled runners and restricted only for network-restricted evidence runs."
    )

    if strict_label.startswith("FAIL"):
        posture_line += " Recovery: `CI_SCENE_DELIVERY_PROFILE=restricted make ci.scene.delivery.readiness`."

    for index in range(start + 1, end):
        if lines[index].startswith("5. CI profile posture:"):
            lines[index] = posture_line
            return lines

    insert_at = end
    if insert_at > start + 1 and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    lines.insert(insert_at, posture_line)
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
    summary_payload = _to_summary_payload(state)
    _dump_json(SUMMARY_PATH, summary_payload)
    SUMMARY_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_MD_PATH.write_text(_to_summary_markdown(summary_payload), encoding="utf-8")

    if not SCOREBOARD_PATH.is_file():
        raise SystemExit(f"missing scoreboard: {SCOREBOARD_PATH}")

    lines = SCOREBOARD_PATH.read_text(encoding="utf-8").splitlines()
    lines = _replace_snapshot(lines)
    strict_label = _status_label(state["profiles"]["strict"])
    restricted_label = _status_label(state["profiles"]["restricted"])

    lines = _upsert_evidence_row(
        lines,
        "CI strict profile readiness",
        strict_label,
        PROFILE_COMMANDS["strict"],
    )
    lines = _upsert_evidence_row(
        lines,
        "CI restricted profile readiness",
        restricted_label,
        PROFILE_COMMANDS["restricted"],
    )
    lines = _normalize_evidence_table(lines)
    lines = _upsert_release_gap_profile_posture(lines, strict_label, restricted_label)
    SCOREBOARD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(SCOREBOARD_PATH)
    print(STATE_PATH)
    print(SUMMARY_PATH)
    print(SUMMARY_MD_PATH)
    print("[delivery_readiness_scoreboard_refresh] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
