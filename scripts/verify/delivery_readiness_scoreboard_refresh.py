#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCOREBOARD_PATH = ROOT / "docs" / "product" / "delivery" / "v1" / "delivery_readiness_scoreboard_v1.md"
STATE_PATH = ROOT / "artifacts" / "backend" / "delivery_ci_profile_status.json"
SUMMARY_PATH = ROOT / "artifacts" / "backend" / "delivery_readiness_ci_summary.json"
SUMMARY_MD_PATH = ROOT / "artifacts" / "backend" / "delivery_readiness_ci_summary.md"
MAINLINE_SUMMARY_PATH = ROOT / "artifacts" / "backend" / "delivery_mainline_run_summary.json"
ACTION_CLOSURE_REPORT_PATH = ROOT / "artifacts" / "backend" / "product_delivery_action_closure_report.json"

PROFILE_COMMANDS = {
    "strict": "CI_SCENE_DELIVERY_PROFILE=strict make ci.scene.delivery.readiness",
    "restricted": "CI_SCENE_DELIVERY_PROFILE=restricted make ci.scene.delivery.readiness",
}

OVERALL_OK_POLICIES = {
    "mainline_or_restricted",
    "strict_only",
    "restricted_only",
    "mainline_only",
    "strict_and_mainline",
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

    mainline_summary = _load_json(MAINLINE_SUMMARY_PATH)
    mainline = {
        "present": bool(mainline_summary),
        "path": str(MAINLINE_SUMMARY_PATH.relative_to(ROOT)),
    }
    if mainline_summary:
        mainline.update(
            {
                "ok": bool(mainline_summary.get("ok")),
                "profile": str(mainline_summary.get("profile") or "").strip(),
                "generated_at_utc": str(mainline_summary.get("generated_at_utc") or "").strip(),
                "commit_ref": str(mainline_summary.get("commit_ref") or "").strip(),
                "steps": mainline_summary.get("steps") if isinstance(mainline_summary.get("steps"), dict) else {},
            }
        )

    payload = {
        "generated_at_utc": _utc_now(),
        "scoreboard": {
            "path": str(SCOREBOARD_PATH.relative_to(ROOT)),
            "branch": _git(["git", "branch", "--show-current"]) or "unknown",
            "commit_ref": _git(["git", "rev-parse", "--short", "HEAD"]) or "unknown",
        },
        "mainline": mainline,
        "profiles": {
            "strict": _profile("strict"),
            "restricted": _profile("restricted"),
        },
    }
    payload["overall"] = _compute_overall(payload)
    return payload


def _compute_overall(payload: dict) -> dict:
    profiles = payload.get("profiles") if isinstance(payload.get("profiles"), dict) else {}
    strict_ok = bool((profiles.get("strict") or {}).get("ok"))
    restricted_ok = bool((profiles.get("restricted") or {}).get("ok"))
    mainline = payload.get("mainline") if isinstance(payload.get("mainline"), dict) else {}
    mainline_ok = bool(mainline.get("ok")) if bool(mainline.get("present")) else False

    policy = str(os.getenv("DELIVERY_READINESS_OVERALL_POLICY") or "mainline_or_restricted").strip()
    if policy not in OVERALL_OK_POLICIES:
        policy = "mainline_or_restricted"

    if policy == "strict_only":
        ok = strict_ok
    elif policy == "restricted_only":
        ok = restricted_ok
    elif policy == "mainline_only":
        ok = mainline_ok
    elif policy == "strict_and_mainline":
        ok = strict_ok and mainline_ok
    else:
        ok = mainline_ok or restricted_ok

    return {
        "ok": ok,
        "policy": policy,
        "signals": {
            "strict_ok": strict_ok,
            "restricted_ok": restricted_ok,
            "mainline_ok": mainline_ok,
        },
    }


def _to_summary_markdown(payload: dict) -> str:
    scoreboard = payload.get("scoreboard") if isinstance(payload.get("scoreboard"), dict) else {}
    profiles = payload.get("profiles") if isinstance(payload.get("profiles"), dict) else {}
    strict = profiles.get("strict") if isinstance(profiles.get("strict"), dict) else {}
    restricted = profiles.get("restricted") if isinstance(profiles.get("restricted"), dict) else {}
    mainline = payload.get("mainline") if isinstance(payload.get("mainline"), dict) else {}
    overall = payload.get("overall") if isinstance(payload.get("overall"), dict) else {}

    lines = [
        "# Delivery Readiness CI Summary",
        "",
        f"- generated_at_utc: {payload.get('generated_at_utc', '')}",
        f"- branch: {scoreboard.get('branch', '')}",
        f"- commit_ref: {scoreboard.get('commit_ref', '')}",
        f"- scoreboard: {scoreboard.get('path', '')}",
        f"- mainline_summary: {mainline.get('path', '')}",
        f"- overall_ok: {overall.get('ok', '')}",
        f"- overall_policy: {overall.get('policy', '')}",
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

    if mainline.get("present"):
        steps = mainline.get("steps") if isinstance(mainline.get("steps"), dict) else {}
        lines.extend(
            [
                "",
                "## Mainline",
                "",
                f"- ok: {mainline.get('ok')}",
                f"- profile: {mainline.get('profile', '')}",
                f"- generated_at_utc: {mainline.get('generated_at_utc', '')}",
                f"- commit_ref: {mainline.get('commit_ref', '')}",
                "",
                "| step | status |",
                "|---|---|",
                f"| frontend_gate | {steps.get('frontend_gate', '')} |",
                f"| scene_delivery_readiness | {steps.get('scene_delivery_readiness', '')} |",
                f"| action_closure_smoke | {steps.get('action_closure_smoke', '')} |",
                f"| governance_truth | {steps.get('governance_truth', '')} |",
            ]
        )
    else:
        lines.extend(["", "## Mainline", "", "- unavailable"]) 
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


def _bool_status_label(value: bool) -> str:
    return "PASS" if bool(value) else "FAIL"


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
    mainline = summary_payload.get("mainline") if isinstance(summary_payload.get("mainline"), dict) else {}
    mainline_present = bool(mainline.get("present"))
    mainline_ok = bool(mainline.get("ok")) if mainline_present else False
    mainline_label = _bool_status_label(mainline_ok) if mainline_present else "UNKNOWN"

    action_closure_payload = _load_json(ACTION_CLOSURE_REPORT_PATH)
    action_closure_present = bool(action_closure_payload)
    action_closure_ok = bool(action_closure_payload.get("ok")) if action_closure_present else False
    action_closure_label = _bool_status_label(action_closure_ok) if action_closure_present else "UNKNOWN"

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
    lines = _upsert_evidence_row(
        lines,
        "Mainline one-command summary",
        mainline_label,
        str(MAINLINE_SUMMARY_PATH.relative_to(ROOT)),
    )
    lines = _upsert_evidence_row(
        lines,
        "Product delivery action closure smoke",
        action_closure_label,
        str(ACTION_CLOSURE_REPORT_PATH.relative_to(ROOT)),
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
