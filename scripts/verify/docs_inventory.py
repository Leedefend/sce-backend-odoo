#!/usr/bin/env python3
"""Build docs markdown inventory for governance."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = ROOT / "docs"
OUT_JSON = ROOT / "artifacts/docs/docs_inventory.json"


def classify(rel_path: str) -> str:
    parts = rel_path.split("/")
    if len(parts) < 2:
        return "root"
    section = parts[1]
    if section in {"contract", "ops", "audit", "p0", "p1", "p2", "p3", "release", "runbooks", "specs"}:
        return section
    return "other"


def main() -> int:
    files = sorted(p for p in DOCS_ROOT.rglob("*.md") if p.is_file())
    entries = []
    by_category = Counter()

    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        cat = classify(rel)
        by_category[cat] += 1
        entries.append(
            {
                "path": rel,
                "category": cat,
                "size_bytes": path.stat().st_size,
            }
        )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(ROOT),
        "summary": {
            "docs_markdown_count": len(entries),
            "by_category": dict(sorted(by_category.items())),
        },
        "documents": entries,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(OUT_JSON))
    print(f"docs_markdown_count={len(entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
