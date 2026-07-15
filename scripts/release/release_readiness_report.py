#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
import platform
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/release/frontend-pilot-readiness"


def command(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def read_json(name: str) -> dict | None:
    path = OUT / name
    return json.loads(path.read_text()) if path.exists() else None


def manifest_versions() -> dict[str, str]:
    result = {}
    for name in ("smart_core", "smart_construction_core", "smart_construction_custom", "smart_construction_demo"):
        data = ast.literal_eval((ROOT / "addons" / name / "__manifest__.py").read_text())
        result[name] = str(data.get("version", "unknown"))
    return result


def version(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, cwd=ROOT, text=True, stderr=subprocess.STDOUT).splitlines()[0].strip()
    except Exception:
        return "unavailable"


OUT.mkdir(parents=True, exist_ok=True)
compat = read_json("data-compatibility.json")
restore = read_json("restore.json")
rollback = read_json("rollback.json")
acceptance = read_json("production-acceptance.json")
backup = read_json("backup/manifest.json")
historical_copy_available = bool(compat and compat.get("source_class") in {"sanitized_history_copy", "authorized_production_backup_copy"})
blockers = []
for name, value in (("data_compatibility", compat), ("backup", backup), ("restore", restore), ("rollback", rollback), ("production_acceptance", acceptance)):
    if value is None or value.get("pass", True) is False:
        blockers.append(name)

conditions = []
if not historical_copy_available:
    conditions.append({"code":"HISTORICAL_COPY_REQUIRED","owner":"Delivery owner + DBA","deadline":"2026-07-22","launch_blocker":True,"requirement":"Obtain an authorized sanitized history copy and pass make verify.release.data_compatibility."})
conditions.extend([
    {"code":"HTTPS_DOMAIN_REQUIRED","owner":"Infrastructure owner","deadline":"before pilot activation","launch_blocker":True,"requirement":"Configure real domain, TLS termination, trusted proxy and validate secure cookies/security headers."},
    {"code":"PRODUCTION_SCALE_RTO_REQUIRED","owner":"DBA/SRE","deadline":"before pilot activation","launch_blocker":True,"requirement":"Validate restore timing at representative production data volume; rehearsal timing is not a production RTO claim."},
    {"code":"MONITORING_INTEGRATION_REQUIRED","owner":"SRE","deadline":"before pilot activation","launch_blocker":True,"requirement":"Connect the documented checks and alerts to the selected monitoring platform and assign on-call ownership."},
])
decision = "NO_GO" if blockers else ("CONDITIONAL_GO" if conditions else "GO")
build_hash_path = OUT / "frontend-candidate-build.sha256"
acceptance_hash_path = OUT / "frontend-build.sha256"
payload = {
    "schema_version": 1,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "decision": decision,
    "release_candidate": {
        "git_sha": command("git", "rev-parse", "HEAD"),
        "branch": command("git", "branch", "--show-current"),
        "module_versions": manifest_versions(),
        "frontend_build_sha256": build_hash_path.read_text().strip() if build_hash_path.exists() else None,
        "acceptance_build_sha256": acceptance_hash_path.read_text().strip() if acceptance_hash_path.exists() else None,
        "versions": {"python": platform.python_version(), "node": version(["node", "--version"]), "pnpm": version([str(ROOT / "scripts/dev/pnpm_exec.sh"), "--version"]), "postgres_image": "postgres:15", "odoo": "17"},
        "authoritative_navigation_leaf_count": 70,
        "journey_range": "J02-J11",
    },
    "evidence": {"compatibility": compat, "backup": backup, "restore": restore, "rollback": rollback, "production_acceptance": acceptance},
    "blockers": blockers,
    "conditions": conditions,
}
(OUT / "report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
print(f"[release.readiness] {decision} report={OUT / 'report.json'}")
if decision == "NO_GO":
    raise SystemExit(1)
