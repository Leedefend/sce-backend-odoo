#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard against direct base.group_system ACL binding on SC business models."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_JSON = ROOT / "artifacts" / "backend" / "system_group_business_acl_guard.json"
ARTIFACT_MD = ROOT / "docs" / "ops" / "audit" / "system_group_business_acl_guard.md"

# Technical/system models allowed to bind base.group_system directly.
DEFAULT_ALLOWLIST = {
    "model_sc_audit_log",
    "model_sc_signup_throttle",
    "smart_construction_custom.model_sc_security_policy",
    "model_sc_norm_specialty",
    "model_sc_norm_chapter",
    "model_sc_norm_item",
}


def _load_allowlist() -> set[str]:
    allow = set(DEFAULT_ALLOWLIST)
    extra = str(os.getenv("SYSTEM_GROUP_ACL_ALLOWLIST") or "").strip()
    for item in extra.split(","):
        val = item.strip()
        if val:
            allow.add(val)
    return allow


def _iter_acl_csv_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.glob("addons/*/security/ir.model.access.csv"):
        if path.is_file():
            files.append(path)
    return sorted(files)


def _is_sc_business_model_ref(model_ref: str) -> bool:
    value = model_ref.strip()
    return value.startswith("model_sc_")


def main() -> int:
    allowlist = _load_allowlist()
    violations: list[dict] = []
    scanned_rows = 0
    scanned_files = _iter_acl_csv_files()

    for csv_path in scanned_files:
        with csv_path.open("r", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            for row in reader:
                if not row or row[0].strip().startswith("#"):
                    continue
                if len(row) < 4:
                    continue
                if row[0].strip() == "id":
                    continue
                scanned_rows += 1
                access_id = row[0].strip()
                model_ref = row[2].strip()
                group_ref = row[3].strip()
                if group_ref != "base.group_system":
                    continue
                if not _is_sc_business_model_ref(model_ref):
                    continue
                if model_ref in allowlist:
                    continue
                violations.append(
                    {
                        "file": str(csv_path.relative_to(ROOT).as_posix()),
                        "access_id": access_id,
                        "model_ref": model_ref,
                        "group_ref": group_ref,
                    }
                )

    payload = {
        "ok": len(violations) == 0,
        "summary": {
            "scanned_file_count": len(scanned_files),
            "scanned_row_count": scanned_rows,
            "violation_count": len(violations),
        },
        "allowlist": sorted(allowlist),
        "violations": violations,
    }
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# System Group Business ACL Guard",
        "",
        f"- status: {'PASS' if payload['ok'] else 'FAIL'}",
        f"- scanned_file_count: {payload['summary']['scanned_file_count']}",
        f"- scanned_row_count: {payload['summary']['scanned_row_count']}",
        f"- violation_count: {payload['summary']['violation_count']}",
        "",
        "## Rule",
        "",
        "- Forbid direct `base.group_system` ACL on `model_sc_*` business models.",
        "- Use SC capability groups as ACL bindings, then map system role via implied groups.",
    ]
    if violations:
        lines.extend(["", "## Violations", ""])
        for item in violations[:200]:
            lines.append(
                f"- {item['file']} :: {item['access_id']} :: {item['model_ref']} -> {item['group_ref']}"
            )
    ARTIFACT_MD.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(ARTIFACT_JSON))
    print(str(ARTIFACT_MD))
    if violations:
        print("[system_group_business_acl_guard] FAIL")
        return 1
    print("[system_group_business_acl_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
