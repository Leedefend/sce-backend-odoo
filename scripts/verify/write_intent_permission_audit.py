#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDLER_DIRS = [
    ROOT / "addons" / "smart_core" / "handlers",
    ROOT / "addons" / "smart_construction_core" / "handlers",
]
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "write_intent_permission_audit.md"

TARGET_WRITE_INTENTS = [
    {"label": "execute_button", "candidates": ["execute_button"]},
    {"label": "api.data(write)", "candidates": ["api.data.create", "api.data.unlink", "api.data.batch"]},
    {"label": "api.data.batch", "candidates": ["api.data.batch"]},
    {"label": "file.upload", "candidates": ["file.upload"]},
    {"label": "report.export", "candidates": ["report.export", "usage.export.csv"]},
    {"label": "job.cancel", "candidates": ["job.cancel"]},
]


@dataclass
class IntentLocation:
    intent: str
    file_path: Path
    class_name: str
    required_groups: list[str]
    source: str


def _literal(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _collect_intent_locations() -> dict[str, IntentLocation]:
    out: dict[str, IntentLocation] = {}
    for handler_dir in HANDLER_DIRS:
        if not handler_dir.is_dir():
            continue
        for path in sorted(handler_dir.glob("*.py")):
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(path))
            for node in tree.body:
                if not isinstance(node, ast.ClassDef):
                    continue
                intent = ""
                required_groups: list[str] = []
                for stmt in node.body:
                    if not isinstance(stmt, ast.Assign):
                        continue
                    for target in stmt.targets:
                        if not isinstance(target, ast.Name):
                            continue
                        name = target.id
                        value = _literal(stmt.value)
                        if name == "INTENT_TYPE" and isinstance(value, str):
                            intent = value.strip()
                        elif name == "REQUIRED_GROUPS" and isinstance(value, list):
                            required_groups = [str(x).strip() for x in value if str(x).strip()]
                if intent:
                    out[intent] = IntentLocation(
                        intent=intent,
                        file_path=path,
                        class_name=node.name,
                        required_groups=required_groups,
                        source=str(path.relative_to(ROOT)),
                    )
    return out


def _line_hits(text: str, token: str) -> list[int]:
    rows = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if token in line:
            rows.append(idx)
    return rows


def _audit_one(intent: str, loc: IntentLocation | None) -> dict:
    if loc is None:
        return {
            "intent": intent,
            "exists": False,
            "source": "",
            "required_groups": [],
            "has_acl_guard": False,
            "has_permission_check_intent": False,
            "sudo_lines": [],
            "unguarded_sudo_lines": [],
            "risk_level": "high",
            "notes": ["intent not found in handlers"],
        }
    text = loc.file_path.read_text(encoding="utf-8")
    acl_tokens = ["check_access_rights(", "check_access_rule(", "has_group("]
    acl_hits = [tok for tok in acl_tokens if tok in text]
    has_acl_guard = bool(acl_hits)
    has_permission_check_intent = "permission.check" in text
    sudo_lines = _line_hits(text, ".sudo(")
    unguarded_sudo_lines = sudo_lines if sudo_lines and not has_acl_guard else []

    risk_level = "low"
    notes: list[str] = []
    if not has_acl_guard:
        risk_level = "high"
        notes.append("missing ACL guard call (check_access_rights/check_access_rule/has_group)")
    if sudo_lines and not has_acl_guard:
        risk_level = "high"
        notes.append("sudo usage without explicit ACL guard in file")
    if not loc.required_groups:
        if risk_level == "low":
            risk_level = "medium"
        notes.append("REQUIRED_GROUPS not explicitly defined")
    if has_permission_check_intent:
        notes.append("contains permission.check usage")
    if not notes:
        notes.append("permission posture looks acceptable")
    return {
        "intent": intent,
        "exists": True,
        "source": loc.source,
        "required_groups": loc.required_groups,
        "has_acl_guard": has_acl_guard,
        "has_permission_check_intent": has_permission_check_intent,
        "sudo_lines": sudo_lines,
        "unguarded_sudo_lines": unguarded_sudo_lines,
        "risk_level": risk_level,
        "notes": notes,
    }


def _merge_risk(rows: list[dict]) -> str:
    order = {"low": 0, "medium": 1, "high": 2}
    level = "low"
    for row in rows:
        if order.get(row.get("risk_level", "low"), 0) > order.get(level, 0):
            level = row["risk_level"]
    return level


def _audit_family(label: str, candidates: list[str], intents: dict[str, IntentLocation]) -> dict:
    checks = [_audit_one(intent, intents.get(intent)) for intent in candidates]
    existing = [x for x in checks if x.get("exists")]
    required_groups = sorted({grp for row in existing for grp in row.get("required_groups", [])})
    has_acl_guard = any(bool(row.get("has_acl_guard")) for row in existing)
    sudo_lines = sum(len(row.get("sudo_lines", [])) for row in existing)
    unguarded_sudo_lines = sum(len(row.get("unguarded_sudo_lines", [])) for row in existing)
    notes: list[str] = []
    for row in checks:
        name = row.get("intent", "")
        for note in row.get("notes", []):
            notes.append(f"{name}: {note}")
    if not existing:
        return {
            "intent": label,
            "exists": False,
            "source": "",
            "required_groups": [],
            "has_acl_guard": False,
            "has_permission_check_intent": False,
            "sudo_lines": [],
            "unguarded_sudo_lines": [],
            "risk_level": "high",
            "notes": notes or ["intent family not found in handlers"],
            "matched_intents": [],
        }
    risk = _merge_risk(existing)
    sources = sorted({row.get("source", "") for row in existing if row.get("source")})
    return {
        "intent": label,
        "exists": True,
        "source": ", ".join(sources),
        "required_groups": required_groups,
        "has_acl_guard": has_acl_guard,
        "has_permission_check_intent": any(bool(x.get("has_permission_check_intent")) for x in existing),
        "sudo_lines": [0] * sudo_lines,
        "unguarded_sudo_lines": [0] * unguarded_sudo_lines,
        "risk_level": risk,
        "notes": notes,
        "matched_intents": [x.get("intent") for x in checks],
    }


def _render(rows: list[dict]) -> str:
    high = [x for x in rows if x["risk_level"] == "high"]
    medium = [x for x in rows if x["risk_level"] == "medium"]
    lines = [
        "# Write Intent Permission Audit",
        "",
        f"- intents_scanned: {len(rows)}",
        f"- high_risk_count: {len(high)}",
        f"- medium_risk_count: {len(medium)}",
        "",
        "| intent | exists | required_groups | acl_guard | sudo_calls | unguarded_sudo | risk | source |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {intent} | {exists} | {groups} | {acl} | {sudo} | {unguarded} | {risk} | {src} |".format(
                intent=row["intent"],
                exists="Y" if row["exists"] else "N",
                groups=len(row["required_groups"]),
                acl="Y" if row["has_acl_guard"] else "N",
                sudo=len(row["sudo_lines"]),
                unguarded=len(row["unguarded_sudo_lines"]),
                risk=row["risk_level"],
                src=row["source"] or "-",
            )
        )
        matched = row.get("matched_intents") or []
        if matched:
            lines.append(f"- matched: `{', '.join(matched)}`")
        for note in row["notes"]:
            lines.append(f"- note: `{row['intent']}` {note}")
    return "\n".join(lines) + "\n"


def main() -> int:
    intents = _collect_intent_locations()
    rows = [_audit_family(item["label"], item["candidates"], intents) for item in TARGET_WRITE_INTENTS]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(_render(rows), encoding="utf-8")
    print(str(REPORT_MD))
    print("[write_intent_permission_audit] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
