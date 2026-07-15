#!/usr/bin/env python3
from pathlib import Path
import re

root = Path(__file__).resolve().parents[2]
required = [
    "make/release.mk", "docker-compose.release-rehearsal.yml",
    "config/release/odoo.release-rehearsal.conf.template",
    "scripts/release/rehearsal_guard.py", "scripts/release/release_data_compatibility.py",
    "scripts/release/rehearsal_backup_restore.sh", "scripts/release/release_readiness_report.py",
    "docs/release/frontend_pilot_release_candidate_v1.md", "docs/release/frontend_pilot_runbook_v1.md",
    "docs/release/frontend_backup_restore_drill_v1.md", "docs/release/frontend_rollback_runbook_v1.md",
    "docs/release/frontend_monitoring_baseline_v1.md", "docs/release/frontend_data_compatibility_v1.md",
    "docs/release/frontend_pilot_signoff_v1.md",
]
missing = [path for path in required if not (root / path).is_file()]
if missing:
    raise SystemExit(f"missing release tooling: {missing}")
compose = (root / "docker-compose.release-rehearsal.yml").read_text()
config = (root / "config/release/odoo.release-rehearsal.conf.template").read_text()
guard = (root / "scripts/release/rehearsal_guard.py").read_text()
assert "sc_frontend_acceptance" in guard and "sc_demo" in guard and "postgres" in guard
assert "SC_ALLOW_DEMO_DATA" in guard and "release_rehearsal" in guard
assert re.search(r"list_db\s*=\s*False", config)
assert re.search(r"without_demo\s*=\s*True", config)
assert "18087:8069" in compose and "18086:80" in compose
print("[verify.release.tooling] PASS")
