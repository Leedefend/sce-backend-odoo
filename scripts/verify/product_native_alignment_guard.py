#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "product_native_alignment_guard.json"
DOCS_REQUIRED = [
    ROOT / "docs" / "ops" / "product_native_alignment_business_mapping_v1.md",
    ROOT / "docs" / "ops" / "product_scene_orchestration_native_template_v1.md",
    ROOT / "docs" / "ops" / "product_native_alignment_gate_rules_v1.md",
]
PATH_PATTERNS = [
    re.compile(r"^addons/smart_construction_core/(handlers|services)/project_(payment|contract|cost)"),
    re.compile(r"^scripts/verify/product_project_(payment|contract|cost)"),
]
TOKEN_PATTERNS = [
    re.compile(r"project\.(payment|contract|cost)\."),
]
SCAN_ROOTS = (
    "addons/",
    "frontend/",
    "scripts/",
    "Makefile",
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _git_status_paths() -> list[str]:
    proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    out: list[str] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        if path:
            out.append(path)
    return out


def _scan_text(path: str, text: str) -> list[dict]:
    findings: list[dict] = []
    for pattern in TOKEN_PATTERNS:
        for match in pattern.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            findings.append(
                {
                    "rule": "shadow_intent_family_forbidden",
                    "severity": "high",
                    "path": path,
                    "line": line_no,
                    "message": f"found forbidden shadow intent family token `{match.group(0)}`",
                }
            )
            break
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-findings", action="store_true")
    args = parser.parse_args()

    report = {
        "status": "PASS",
        "summary": {},
        "findings": [],
        "required_docs": [],
    }

    for doc in DOCS_REQUIRED:
        report["required_docs"].append({"path": str(doc.relative_to(ROOT)), "exists": doc.exists()})

    missing_docs = [row["path"] for row in report["required_docs"] if not row["exists"]]
    if missing_docs:
        report["findings"].append(
            {
                "rule": "native_alignment_docs_required",
                "severity": "high",
                "path": ",".join(missing_docs),
                "message": "required native alignment documents are missing",
            }
        )

    try:
        changed_paths = _git_status_paths()
    except Exception as exc:
        report["status"] = "FAIL"
        report["findings"].append(
            {
                "rule": "git_status_unavailable",
                "severity": "high",
                "message": str(exc),
            }
        )
        _write_json(OUT_JSON, report)
        print("[product_native_alignment_guard] FAIL")
        return 1

    for rel in changed_paths:
        if not rel.startswith(SCAN_ROOTS):
            continue
        matched = any(pattern.search(rel) for pattern in PATH_PATTERNS)
        path = ROOT / rel
        if matched:
            report["findings"].append(
                {
                    "rule": "shadow_scene_file_forbidden",
                    "severity": "high",
                    "path": rel,
                    "message": "changed file matches forbidden project-domain shadow scene path",
                }
            )
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
            report["findings"].extend(_scan_text(rel, text))

    report["summary"] = {
        "changed_path_count": len(changed_paths),
        "finding_count": len(report["findings"]),
        "blocked": bool(report["findings"]),
    }
    if report["findings"]:
        report["status"] = "BLOCKED"

    _write_json(OUT_JSON, report)
    if report["findings"] and not args.allow_findings:
        print("[product_native_alignment_guard] BLOCKED")
        for item in report["findings"][:12]:
            path = item.get("path") or "-"
            line = item.get("line")
            line_text = f":{line}" if line else ""
            print(f" - {path}{line_text} {item.get('rule')}: {item.get('message')}")
        return 1

    print("[product_native_alignment_guard] PASS" if not report["findings"] else "[product_native_alignment_guard] PASS_WITH_FINDINGS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
