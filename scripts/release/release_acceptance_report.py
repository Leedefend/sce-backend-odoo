#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path

paths = {
    "fixture": Path("artifacts/playwright/frontend-productization-fixture/report.json"),
    "navigation": Path("artifacts/playwright/frontend-navigation-access/report.json"),
    "financial": Path("artifacts/frontend-financial-workspace/report.json"),
    "work": Path("artifacts/frontend-my-work-approval/report.json"),
    "hardening": Path("artifacts/frontend-delivery-hardening/report.json"),
}
if any(not path.exists() for path in paths.values()):
    raise SystemExit("release acceptance evidence is incomplete")
evidence = {name: json.loads(path.read_text()) for name, path in paths.items()}
checks = [
    evidence["fixture"].get("pass") is True,
    all(evidence["fixture"].get("journeys", {}).get(f"J0{i}", {}).get("status") == "PASS" for i in (2, 3)),
    evidence["navigation"].get("final_authoritative_leaf_count") == 70,
    evidence["navigation"].get("reachable") == 70,
    evidence["navigation"].get("forbidden") == 0,
    evidence["financial"].get("pass") is True,
    all(evidence["financial"].get(key, {}).get("status") == "PASS" for key in ("j04", "j05", "j06")),
    evidence["work"].get("pass") is True,
    all(evidence["work"].get(key, {}).get("status") == "PASS" for key in ("j07", "j08")),
    evidence["hardening"].get("pass") is True,
    all(evidence["hardening"].get("journeys", {}).get(f"J{i:02d}") == "PASS" for i in range(9, 12)),
    all(not evidence["hardening"].get("runtime", {}).get(key) for key in ("console", "pageerror", "unhandled", "http")),
]
if not all(checks):
    raise SystemExit("release acceptance evidence contains a failed gate")
build_hash = Path("artifacts/release/frontend-pilot-readiness/frontend-build.sha256").read_text().strip()
out = Path("artifacts/release/frontend-pilot-readiness/production-acceptance.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "runtime": "production_static_build",
    "database": "sc_frontend_acceptance",
    "demo_fixture": True,
    "frontend_build_sha256": build_hash,
    "navigation": {"reachable": 70, "total": 70},
    "journeys": {f"J{i:02d}": "PASS" for i in range(2, 12)},
    "console_pageerror_unhandled_unexpected_http": 0,
    "pass": True,
}, indent=2) + "\n")
print(f"[release.production.acceptance] PASS build={build_hash} J02-J11 70/70")
