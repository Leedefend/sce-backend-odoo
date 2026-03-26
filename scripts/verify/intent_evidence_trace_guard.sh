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
from odoo.addons.smart_construction_core.handlers.business_evidence_trace import BusinessEvidenceTraceHandler

OUT_JSON = Path("/mnt/artifacts/backend/intent_evidence_trace_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/intent_evidence_trace_guard.md")

project = env["project.project"].sudo().search([("name", "=", "展厅-产线升级改造工程")], limit=1)
report = {"status": "PASS", "errors": [], "project_id": int(project.id or 0)}

if not project:
    report["status"] = "FAIL"
    report["errors"].append("missing target project: 展厅-产线升级改造工程")
else:
    su_env = api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))
    handler = BusinessEvidenceTraceHandler(
        env,
        su_env=su_env,
        context={"trace_id": "guard-evidence-trace"},
        payload={"params": {"business_model": "project.project", "business_id": int(project.id)}},
    )
    result = handler.run()
    data = result.get("data") or {}
    summary = data.get("summary") or {}
    chain = data.get("evidence_chain") or {}
    if not result.get("ok"):
        report["status"] = "FAIL"
        report["errors"].append("handler returned ok=false")
    if int(summary.get("evidence_count") or 0) <= 0:
        report["status"] = "FAIL"
        report["errors"].append("summary.evidence_count <= 0")
    if not any(chain.get(key) for key in ("payment", "cost", "settlement")):
        report["status"] = "FAIL"
        report["errors"].append("evidence_chain missing payment/cost/settlement groups")
    report["summary"] = summary
    report["evidence_refs"] = data.get("evidence_refs") or []

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUT_MD.write_text(
    "# Intent Evidence Trace Guard\n\n"
    f"- status: `{report['status']}`\n"
    f"- project_id: `{report.get('project_id')}`\n"
    f"- evidence_count: `{int((report.get('summary') or {}).get('evidence_count') or 0)}`\n"
    f"- evidence_refs: `{len(report.get('evidence_refs') or [])}`\n"
    + ("\n- errors:\n" + "\n".join(f"  - {line}" for line in report["errors"]) if report["errors"] else "\n"),
    encoding="utf-8",
)

if report["errors"]:
    print("[intent_evidence_trace_guard] FAIL")
    for line in report["errors"]:
        print(f" - {line}")
    raise SystemExit(1)

print("[intent_evidence_trace_guard] PASS")
PY
