#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INTENT_ENRICHED_JSON = ROOT / "docs" / "contract" / "exports" / "intent_catalog_enriched.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "intent_layered_catalog.md"


def _safe_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _as_rows(payload: dict) -> list[dict]:
    rows = payload.get("intents")
    if not isinstance(rows, list):
        return []
    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        intent = str(row.get("intent_type") or "").strip()
        if not intent:
            continue
        layer = str(row.get("layer") or "domain").strip().lower()
        if layer not in {"core", "domain", "governance"}:
            layer = "domain"
        out.append(
            {
                "intent": intent,
                "layer": layer,
                "is_write": bool(row.get("is_write") or row.get("is_write_operation")),
                "required_groups": [
                    str(item).strip()
                    for item in (row.get("required_groups") or [])
                    if str(item).strip()
                ],
                "source": str(row.get("source") or ""),
            }
        )
    return out


def main() -> int:
    payload = _safe_json(INTENT_ENRICHED_JSON)
    rows = _as_rows(payload)
    grouped = {"core": [], "domain": [], "governance": []}
    for row in rows:
        grouped[row["layer"]].append(row)

    summary = {
        "intent_count": len(rows),
        "core_count": len(grouped["core"]),
        "domain_count": len(grouped["domain"]),
        "governance_count": len(grouped["governance"]),
        "write_count": sum(1 for row in rows if row["is_write"]),
    }

    lines = [
        "# Intent Layered Catalog",
        "",
        f"- intent_count: {summary['intent_count']}",
        f"- core_count: {summary['core_count']}",
        f"- domain_count: {summary['domain_count']}",
        f"- governance_count: {summary['governance_count']}",
        f"- write_count: {summary['write_count']}",
        "",
        "| intent | layer | is_write | required_groups | source |",
        "|---|---|---:|---:|---|",
    ]
    for row in sorted(rows, key=lambda item: (item["layer"], item["intent"])):
        lines.append(
            "| {intent} | {layer} | {is_write} | {groups} | {source} |".format(
                intent=row["intent"],
                layer=row["layer"],
                is_write="Y" if row["is_write"] else "N",
                groups=len(row["required_groups"]),
                source=row["source"] or "-",
            )
        )

    for layer in ("core", "domain", "governance"):
        lines.extend(["", f"## {layer.title()} Layer", ""])
        bucket = sorted(grouped[layer], key=lambda item: item["intent"])
        if not bucket:
            lines.append("- none")
            continue
        for row in bucket:
            lines.append(f"- `{row['intent']}`")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(REPORT_MD))
    print("[intent_layered_catalog_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
