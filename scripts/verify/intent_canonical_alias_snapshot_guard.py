#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INTENT_CATALOG = ROOT / "docs" / "contract" / "exports" / "intent_catalog.json"
BASELINE = ROOT / "scripts" / "verify" / "baselines" / "intent_canonical_alias_snapshot.json"
ARTIFACT = ROOT / "artifacts" / "backend" / "intent_canonical_alias_snapshot.json"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _snapshot() -> dict[str, Any]:
    catalog = _load_json(INTENT_CATALOG)
    intents = catalog.get("intents") if isinstance(catalog.get("intents"), list) else []

    rows: list[dict[str, Any]] = []
    for item in intents:
        if not isinstance(item, dict):
            continue
        canonical = str(item.get("intent") or "").strip()
        if not canonical:
            continue
        rows.append({"name": canonical, "status": "canonical", "canonical": canonical})
        for alias in item.get("aliases") if isinstance(item.get("aliases"), list) else []:
            alias_name = str(alias or "").strip()
            if alias_name and alias_name != canonical:
                rows.append({"name": alias_name, "status": "alias", "canonical": canonical})

    rows.sort(key=lambda row: (str(row.get("name") or ""), str(row.get("status") or "")))
    return {
        "source": "docs.contract.exports.intent_catalog",
        "canonical_count": len([r for r in rows if r.get("status") == "canonical"]),
        "alias_count": len([r for r in rows if r.get("status") == "alias"]),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Intent canonical/alias snapshot drift guard")
    parser.add_argument("--update-baseline", action="store_true", help="Overwrite baseline with current snapshot")
    args = parser.parse_args()

    current = _snapshot()
    _save_json(ARTIFACT, current)

    if args.update_baseline:
        _save_json(BASELINE, current)
        print("[intent_canonical_alias_snapshot_guard] UPDATED")
        print(f"baseline={BASELINE.relative_to(ROOT).as_posix()}")
        return 0

    baseline = _load_json(BASELINE)
    if not baseline:
        print("[intent_canonical_alias_snapshot_guard] FAIL")
        print(f"missing_or_invalid_baseline={BASELINE.relative_to(ROOT).as_posix()}")
        return 2

    if baseline != current:
        print("[intent_canonical_alias_snapshot_guard] FAIL")
        print("baseline and current snapshot mismatch")
        print(f"artifact={ARTIFACT.relative_to(ROOT).as_posix()}")
        return 2

    print("[intent_canonical_alias_snapshot_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

