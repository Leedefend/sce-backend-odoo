#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_JSON = ROOT / "docs" / "product" / "product_delivery_contract_v1.json"
REPORT_JSON = ROOT / "artifacts" / "backend" / "product_delivery_package_manifest.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "product_delivery_package_manifest.md"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _norm(v: object) -> str:
    return str(v or "").strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            b = fh.read(8192)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    contract = _load(CONTRACT_JSON)
    if not contract:
        errors.append("missing product delivery contract")

    reports = contract.get("required_reports") if isinstance(contract.get("required_reports"), list) else []
    docs = contract.get("required_docs") if isinstance(contract.get("required_docs"), list) else []

    files = []
    for row in [*reports, *docs]:
        if not isinstance(row, dict):
            continue
        item_id = _norm(row.get("id"))
        rel_path = _norm(row.get("path"))
        p = ROOT / rel_path
        exists = p.is_file()
        entry = {
            "id": item_id,
            "path": rel_path,
            "exists": exists,
            "size_bytes": p.stat().st_size if exists else 0,
            "sha256": _sha256(p) if exists else "",
        }
        files.append(entry)
        if not exists:
            errors.append(f"missing_required_file={rel_path}")

    existing_mtimes = [((ROOT / row["path"]).stat().st_mtime) for row in files if row["exists"]]
    generated_ts = max(existing_mtimes) if existing_mtimes else 0
    generated_at = (
        datetime.fromtimestamp(generated_ts).isoformat(timespec="seconds")
        if generated_ts > 0
        else "unknown"
    )
    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "contract_version": _norm(contract.get("version") or "unknown"),
            "file_count": len(files),
            "missing_count": len([x for x in files if not x["exists"]]),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "generated_at": generated_at,
        "files": files,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Product Delivery Package Manifest",
        "",
        f"- generated_at: {generated_at}",
        f"- contract_version: {payload['summary']['contract_version']}",
        f"- file_count: {payload['summary']['file_count']}",
        f"- missing_count: {payload['summary']['missing_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        "",
        "| id | path | exists | size_bytes | sha256_16 |",
        "|---|---|---|---:|---|",
    ]
    for row in files:
        lines.append(
            f"| {row['id']} | {row['path']} | {'yes' if row['exists'] else 'no'} | "
            f"{row['size_bytes']} | {(row['sha256'][:16] if row['sha256'] else '-')} |"
        )
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[product_delivery_package_manifest] FAIL")
        return 2
    print("[product_delivery_package_manifest] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
