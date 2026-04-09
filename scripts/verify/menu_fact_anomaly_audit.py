#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


def _load_menu_fact_service_class():
    service_path = ROOT_DIR / "addons" / "smart_core" / "delivery" / "menu_fact_service.py"
    spec = importlib.util.spec_from_file_location("menu_fact_service_local", service_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"unable to load menu_fact_service module: {service_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.MenuFactService


def run_audit(snapshot_path: Path, output_path: Path) -> dict:
    menu_fact_service_class = _load_menu_fact_service_class()
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    flat = payload.get("flat") if isinstance(payload.get("flat"), list) else []
    auditor = menu_fact_service_class(env=None)
    report = auditor.audit_menu_facts(flat)
    out = {
        "meta": {
            "source_snapshot": str(snapshot_path),
            "menu_total": report.get("summary", {}).get("menu_total", 0),
        },
        "summary": report.get("summary", {}),
        "anomalies": report.get("anomalies", {}),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit menu fact snapshot anomalies.")
    parser.add_argument(
        "--snapshot",
        default="artifacts/menu/menu_fact_snapshot_v1.json",
        help="menu fact snapshot path",
    )
    parser.add_argument(
        "--output",
        default="artifacts/menu/menu_fact_anomalies_v1.json",
        help="anomaly output path",
    )
    args = parser.parse_args()
    out = run_audit(Path(args.snapshot), Path(args.output))
    summary = out.get("summary", {})
    print(
        "[menu.fact.anomaly_audit] PASS "
        f"menu_total={summary.get('menu_total', 0)} "
        f"anomaly_menu_count={summary.get('anomaly_menu_count', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
