#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

source "$ROOT_DIR/scripts/common/env.sh"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
source "$ROOT_DIR/scripts/_lib/common.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME required}"

compose ${COMPOSE_FILES} exec -T odoo sh -lc "odoo shell -d '${DB_NAME}' -c '${ODOO_CONF}'" <<'PY'
import json
from pathlib import Path

from odoo import api, SUPERUSER_ID
from odoo.addons.smart_construction_core.handlers.project_dashboard_enter import ProjectDashboardEnterHandler

OUT_JSON = Path("/mnt/artifacts/backend/project_dashboard_evidence_contract_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/project_dashboard_evidence_contract_guard.md")

project = env["project.project"].sudo().search([("name", "=", "展厅-产线升级改造工程")], limit=1)
report = {"status": "PASS", "errors": []}

if not project:
    report["status"] = "FAIL"
    report["errors"].append("missing target project: 展厅-产线升级改造工程")
else:
    su_env = api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))
    handler = ProjectDashboardEnterHandler(
        env,
        su_env=su_env,
        context={"trace_id": "guard-dashboard-evidence"},
        payload={"params": {"project_id": int(project.id)}},
    )
    result = handler.run()
    data = result.get("data") or {}
    facts = data.get("facts") or {}
    refs = data.get("evidence_refs") or []
    completion = data.get("completion") or {}
    if not result.get("ok"):
        report["status"] = "FAIL"
        report["errors"].append("project.dashboard.enter returned ok=false")
    if not isinstance(facts, dict) or int(facts.get("evidence_count") or 0) <= 0:
        report["status"] = "FAIL"
        report["errors"].append("facts.evidence_count <= 0")
    if not refs:
        report["status"] = "FAIL"
        report["errors"].append("evidence_refs empty")
    if not isinstance(completion, dict) or int(completion.get("percent") or 0) <= 0:
        report["status"] = "FAIL"
        report["errors"].append("completion.percent <= 0")
    report["project_id"] = int(project.id)
    report["facts"] = facts
    report["evidence_refs"] = refs
    report["completion"] = completion

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUT_MD.write_text(
    "# Project Dashboard Evidence Contract Guard\n\n"
    f"- status: `{report['status']}`\n"
    f"- project_id: `{report.get('project_id', 0)}`\n"
    f"- evidence_count: `{int((report.get('facts') or {}).get('evidence_count') or 0)}`\n"
    f"- evidence_refs: `{len(report.get('evidence_refs') or [])}`\n"
    f"- completion_percent: `{int((report.get('completion') or {}).get('percent') or 0)}`\n"
    + ("\n- errors:\n" + "\n".join(f"  - {line}" for line in report["errors"]) if report["errors"] else "\n"),
    encoding="utf-8",
)

if report["errors"]:
    print("[project_dashboard_evidence_contract_guard] FAIL")
    for line in report["errors"]:
        print(f" - {line}")
    raise SystemExit(1)

print("[project_dashboard_evidence_contract_guard] PASS")
PY
