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

OUT_JSON = Path("/mnt/artifacts/backend/settlement_evidence_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/settlement_evidence_guard.md")

PROJECT_NAMES = [
    "展厅-智慧园区运营中心",
    "展厅-装配式住宅试点",
    "展厅-产线升级改造工程",
]

Project = env["project.project"].sudo()
Settlement = env["sc.settlement.order"].sudo()
Evidence = env["sc.business.evidence"].sudo()

report = {"status": "PASS", "projects": {}, "missing_projects": [], "errors": []}

for name in PROJECT_NAMES:
    project = Project.search([("name", "=", name)], limit=1)
    if not project:
        report["missing_projects"].append(name)
        continue
    settlements = Settlement.search([("project_id", "=", project.id), ("state", "=", "done")])
    evidences = Evidence.search(
        [
            ("business_model", "=", "project.project"),
            ("business_id", "=", project.id),
            ("evidence_type", "=", "settlement"),
        ]
    )
    evidence_sources = {(item.source_model, int(item.source_id or 0)) for item in evidences}
    missing = [item.id for item in settlements if ("sc.settlement.order", item.id) not in evidence_sources]
    report["projects"][name] = {
        "project_id": int(project.id),
        "settlement_done_count": len(settlements),
        "settlement_evidence_count": len(evidences),
        "missing_settlement_ids": missing,
    }
    if missing:
        report["errors"].append(f"{name}: missing settlement evidence for ids {missing}")

if report["errors"]:
    report["status"] = "FAIL"
elif report["missing_projects"]:
    report["status"] = "SKIP_ENV"

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUT_MD.write_text(
    "# Settlement Evidence Guard\n\n"
    f"- status: `{report['status']}`\n"
    + "\n".join(
        f"- {name}: done_settlements={row['settlement_done_count']} evidences={row['settlement_evidence_count']}"
        for name, row in report["projects"].items()
    )
    + ("\n- missing demo projects:\n" + "\n".join(f"  - {line}" for line in report["missing_projects"]) if report["missing_projects"] else "")
    + ("\n- errors:\n" + "\n".join(f"  - {line}" for line in report["errors"]) if report["errors"] else "\n"),
    encoding="utf-8",
)

if report["errors"]:
    print("[settlement_evidence_guard] FAIL")
    for line in report["errors"]:
        print(f" - {line}")
    raise SystemExit(1)

if report["status"] == "SKIP_ENV":
    print("[settlement_evidence_guard] SKIP_ENV")
    for line in report["missing_projects"]:
        print(f" - missing demo project: {line}")
    raise SystemExit(0)

print("[settlement_evidence_guard] PASS")
PY
