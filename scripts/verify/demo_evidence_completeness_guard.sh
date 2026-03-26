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

from odoo.addons.smart_construction_demo.tools.scenario_loader import SCENARIO_PROFILES
from odoo.addons.smart_construction_core.services.evidence_chain_service import EvidenceChainService
from odoo.addons.smart_construction_core.services.project_risk_alert_service import ProjectRiskAlertService

OUT_JSON = Path("/mnt/artifacts/backend/demo_evidence_completeness_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/demo_evidence_completeness_guard.md")

Project = env["project.project"].sudo()
chain_service = EvidenceChainService(env)
risk_service = ProjectRiskAlertService(env)

report = {"status": "PASS", "scenarios": {}, "errors": []}

for scenario_key, spec in SCENARIO_PROFILES.items():
    project_name = str(spec.get("showcase_project") or "")
    expected_risk = str(spec.get("expected_risk") or "")
    project = Project.search([("name", "=", project_name)], limit=1)
    if not project:
        report["errors"].append(f"{scenario_key}: missing showcase project {project_name}")
        continue
    chain = chain_service.build_project_chain(project.id)
    risks = risk_service.build(project)
    risk_codes = [str(item.get("code") or "") for item in risks if isinstance(item, dict)]
    summary = chain.get("summary") or {}
    row = {
        "project_id": int(project.id),
        "project_name": project_name,
        "evidence_count": int(summary.get("evidence_count") or 0),
        "risk_codes": risk_codes,
    }
    report["scenarios"][scenario_key] = row
    if row["evidence_count"] <= 0:
        report["errors"].append(f"{scenario_key}: evidence_count <= 0")
    if expected_risk and expected_risk not in risk_codes:
        report["errors"].append(f"{scenario_key}: expected risk missing -> {expected_risk}")

if report["errors"]:
    report["status"] = "FAIL"

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUT_MD.write_text(
    "# Demo Evidence Completeness Guard\n\n"
    f"- status: `{report['status']}`\n"
    + "\n".join(
        f"- {key}: project={row['project_name']} evidence_count={row['evidence_count']} risks={','.join(row['risk_codes'])}"
        for key, row in report["scenarios"].items()
    )
    + ("\n- errors:\n" + "\n".join(f"  - {line}" for line in report["errors"]) if report["errors"] else "\n"),
    encoding="utf-8",
)

if report["errors"]:
    print("[demo_evidence_completeness_guard] FAIL")
    for line in report["errors"]:
        print(f" - {line}")
    raise SystemExit(1)

print("[demo_evidence_completeness_guard] PASS")
PY
