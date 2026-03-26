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

from odoo.addons.smart_construction_core.services.evidence_chain_service import EvidenceChainService

OUT_JSON = Path("/mnt/artifacts/backend/evidence_chain_project_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/evidence_chain_project_guard.md")

PROJECT_NAMES = [
    "展厅-智慧园区运营中心",
    "展厅-装配式住宅试点",
    "展厅-产线升级改造工程",
]

Project = env["project.project"].sudo()
service = EvidenceChainService(env)
report = {"status": "PASS", "projects": {}, "errors": []}

for name in PROJECT_NAMES:
    project = Project.search([("name", "=", name)], limit=1)
    if not project:
        report["errors"].append(f"missing project: {name}")
        continue
    chain = service.build_project_chain(project.id)
    summary = chain.get("summary") or {}
    refs = chain.get("evidence_refs") or []
    row = {
        "project_id": int(project.id),
        "summary": summary,
        "evidence_ref_count": len(refs),
    }
    report["projects"][name] = row
    if int(summary.get("evidence_count") or 0) <= 0:
        report["errors"].append(f"{name}: evidence_count <= 0")
    if not refs:
        report["errors"].append(f"{name}: evidence_refs empty")

if report["errors"]:
    report["status"] = "FAIL"

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUT_MD.write_text(
    "# Evidence Chain Project Guard\n\n"
    f"- status: `{report['status']}`\n"
    + "\n".join(
        f"- {name}: evidence_count={int((row.get('summary') or {}).get('evidence_count') or 0)} refs={row['evidence_ref_count']}"
        for name, row in report["projects"].items()
    )
    + ("\n- errors:\n" + "\n".join(f"  - {line}" for line in report["errors"]) if report["errors"] else "\n"),
    encoding="utf-8",
)

if report["errors"]:
    print("[evidence_chain_project_guard] FAIL")
    for line in report["errors"]:
        print(f" - {line}")
    raise SystemExit(1)

print("[evidence_chain_project_guard] PASS")
PY
