#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_JSON = ROOT / "artifacts" / "contract_governance_coverage.json"
ARTIFACT_MD = ROOT / "artifacts" / "contract_governance_coverage.md"

TARGETS = {
    "system_init": ROOT / "addons/smart_core/handlers/system_init.py",
    "ui_contract": ROOT / "addons/smart_core/handlers/ui_contract.py",
    "contract_service": ROOT / "addons/smart_core/app_config_engine/services/contract_service.py",
}

RULES = {
    "system_init": [
        r"resolve_contract_mode",
        r"apply_contract_governance",
    ],
    "ui_contract": [
        r"resolve_contract_mode",
        r"apply_contract_governance",
    ],
    "contract_service": [
        r"resolve_contract_mode",
        r"apply_contract_governance",
    ],
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)

    files_report = {}
    failures = []

    for name, path in TARGETS.items():
        exists = path.is_file()
        entry = {
            "path": path.relative_to(ROOT).as_posix(),
            "exists": exists,
            "rules": [],
            "covered": False,
        }
        if not exists:
            failures.append(f"{name}: file missing")
            files_report[name] = entry
            continue

        text = _read(path)
        all_ok = True
        for pattern in RULES.get(name, []):
            ok = re.search(pattern, text) is not None
            entry["rules"].append({"pattern": pattern, "ok": ok})
            if not ok:
                failures.append(f"{name}: missing {pattern}")
                all_ok = False
        entry["covered"] = all_ok
        files_report[name] = entry

    covered = sum(1 for v in files_report.values() if v.get("covered"))
    total = len(files_report)
    summary = {
        "ok": len(failures) == 0,
        "coverage_ratio": f"{covered}/{total}",
        "files": files_report,
        "failures": failures,
    }

    ARTIFACT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Contract Governance Coverage",
        "",
        f"- status: {'PASS' if summary['ok'] else 'FAIL'}",
        f"- coverage_ratio: {summary['coverage_ratio']}",
        "",
        "## Files",
        "",
    ]
    for name, info in files_report.items():
        lines.append(f"- {name}: {'covered' if info.get('covered') else 'missing'} ({info.get('path')})")
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend([f"- {item}" for item in failures])
    ARTIFACT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(ARTIFACT_JSON))
    print(str(ARTIFACT_MD))
    if failures:
        print("[contract_governance_coverage] FAIL")
        return 1
    print("[contract_governance_coverage] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
