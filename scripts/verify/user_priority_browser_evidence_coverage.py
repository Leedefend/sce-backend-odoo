#!/usr/bin/env python3
"""Check browser evidence coverage for user-prioritized legacy entries."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PLAN_SCRIPT = ROOT / "scripts/migration/business_user_priority_menu_plan_write.py"
EVIDENCE_DIR = Path(os.getenv("USER_PRIORITY_BROWSER_EVIDENCE_DIR", ROOT / "artifacts/function-usability-proof/current"))
REPORT_JSON = Path(
    os.getenv(
        "USER_PRIORITY_BROWSER_EVIDENCE_REPORT",
        ROOT / "artifacts/function-usability-proof/current/user_priority_browser_evidence_coverage.json",
    )
)
REPORT_MD = REPORT_JSON.with_suffix(".md")


CODE_RE = re.compile(r"(?<![A-Za-z0-9])P?([1-9][0-9]0?)(?![0-9])", re.IGNORECASE)


def load_expected_entries() -> list[dict[str, Any]]:
    source = PLAN_SCRIPT.read_text(encoding="utf-8")
    prefix = source.split("\nensure_allowed_db()", 1)[0]
    namespace: dict[str, Any] = {"__file__": str(PLAN_SCRIPT)}
    exec(compile(prefix, str(PLAN_SCRIPT), "exec"), namespace)
    entries = namespace.get("ENTRIES")
    if not isinstance(entries, list):
        raise RuntimeError("business user priority plan ENTRIES not found")
    return entries


def normalize_code(value: object) -> str | None:
    text = str(value or "")
    match = CODE_RE.search(text)
    if not match:
        return None
    return f"P{int(match.group(1)):03d}"


def truthy_status(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("ok") is True or payload.get("pass") is True:
        return True
    if str(payload.get("status") or "").upper() == "PASS":
        return True
    checks = payload.get("checks")
    if isinstance(checks, dict) and checks and all(value is True for value in checks.values()):
        return True
    return False


def has_legacy_passing_checks(payload: Any) -> bool:
    if isinstance(payload, list):
        return any(has_legacy_passing_checks(item) for item in payload)
    if not isinstance(payload, dict):
        return False
    if truthy_status(payload):
        return True
    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        return False
    bool_items = {key: value for key, value in payload.items() if isinstance(value, bool)}
    positive = any(
        value is True
        and (
            key.startswith("has")
            or key.endswith("_ok")
            or key in {"createVisible", "titlePresent", "loadingDone", "enteredCreate", "fieldVisible", "labelVisible"}
        )
        for key, value in bool_items.items()
    )
    negative_clean = all(
        value is False
        for key, value in bool_items.items()
        if "Error" in key or "Invalid" in key or key in {"hasError", "hasErrorText"}
    )
    if positive and negative_clean:
        return True
    return any(has_legacy_passing_checks(value) for value in payload.values())


def collect_codes_from_node(node: Any, inherited_ok: bool = False) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    if isinstance(node, dict):
        node_ok = inherited_ok or truthy_status(node)
        code = (
            normalize_code(node.get("code"))
            or normalize_code(node.get("key"))
            or normalize_code(node.get("entry"))
            or normalize_code(node.get("name"))
            or normalize_code(node.get("label"))
        )
        if code and node_ok:
            found.setdefault(code, set()).add("json")
        for value in node.values():
            for child_code, kinds in collect_codes_from_node(value, node_ok).items():
                found.setdefault(child_code, set()).update(kinds)
    elif isinstance(node, list):
        for item in node:
            for child_code, kinds in collect_codes_from_node(item, inherited_ok).items():
                found.setdefault(child_code, set()).update(kinds)
    return found


def collect_evidence() -> dict[str, list[dict[str, str]]]:
    evidence: dict[str, list[dict[str, str]]] = {}
    if not EVIDENCE_DIR.is_dir():
        return evidence
    for path in sorted(EVIDENCE_DIR.glob("user_priority_entry*")):
        if not path.is_file():
            continue
        filename_code_matches = [f"P{int(match):03d}" for match in CODE_RE.findall(path.name)]
        codes: dict[str, set[str]] = {}
        if path.suffix.lower() == ".json":
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                payload = {}
            file_ok = has_legacy_passing_checks(payload)
            codes = collect_codes_from_node(payload, file_ok)
            if file_ok:
                for code in filename_code_matches:
                    codes.setdefault(code, set()).add("json")
        elif path.suffix.lower() == ".png":
            for code in filename_code_matches:
                codes.setdefault(code, set()).add("screenshot")
        for code, kinds in codes.items():
            evidence.setdefault(code, []).append({"path": str(path.relative_to(ROOT)), "kind": "+".join(sorted(kinds))})
    return evidence


def write_report(payload: dict[str, Any]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# User Priority Browser Evidence Coverage",
        "",
        f"Status: {payload['status']}",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(payload["summary"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Entries",
        "",
        "| code | legacy entry | json evidence | screenshot evidence | status |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {code} | {legacy_menu_group}/{legacy_menu_name} | {json_count} | {screenshot_count} | {status} |".format(**row)
        )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    expected_entries = load_expected_entries()
    evidence = collect_evidence()
    rows: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for entry in expected_entries:
        code = f"P{int(entry['priority_sequence']):03d}"
        items = evidence.get(code, [])
        json_count = sum(1 for item in items if "json" in item["kind"])
        screenshot_count = sum(1 for item in items if "screenshot" in item["kind"])
        ok = json_count > 0
        row = {
            "code": code,
            "legacy_menu_group": entry["legacy_menu_group"],
            "legacy_menu_name": entry["legacy_menu_name"],
            "json_count": json_count,
            "screenshot_count": screenshot_count,
            "evidence": items[:8],
            "status": "PASS" if ok else "MISSING_JSON_EVIDENCE",
        }
        rows.append(row)
        if not ok:
            missing.append(row)
    payload = {
        "status": "PASS" if not missing else "FAIL",
        "mode": "user_priority_browser_evidence_coverage",
        "evidence_dir": str(EVIDENCE_DIR.relative_to(ROOT) if EVIDENCE_DIR.is_relative_to(ROOT) else EVIDENCE_DIR),
        "summary": {
            "expected_count": len(expected_entries),
            "covered_count": len(expected_entries) - len(missing),
            "missing_count": len(missing),
            "screenshot_supported_count": sum(1 for row in rows if row["screenshot_count"] > 0),
        },
        "missing": missing,
        "rows": rows,
    }
    write_report(payload)
    print("USER_PRIORITY_BROWSER_EVIDENCE_COVERAGE=" + json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    if missing:
        print("MISSING_USER_PRIORITY_BROWSER_EVIDENCE=" + json.dumps([row["code"] for row in missing], ensure_ascii=False))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
