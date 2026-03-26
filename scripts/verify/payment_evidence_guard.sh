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

OUT_JSON = Path("/mnt/artifacts/backend/payment_evidence_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/payment_evidence_guard.md")

PROJECT_NAMES = [
    "展厅-智慧园区运营中心",
    "展厅-装配式住宅试点",
    "展厅-产线升级改造工程",
]

Project = env["project.project"].sudo()
PaymentRequest = env["payment.request"].sudo()
Evidence = env["sc.business.evidence"].sudo()

report = {"status": "PASS", "projects": {}, "errors": []}

for name in PROJECT_NAMES:
    project = Project.search([("name", "=", name)], limit=1)
    if not project:
        report["errors"].append(f"missing project: {name}")
        continue

    requests = PaymentRequest.search([("project_id", "=", project.id), ("type", "=", "pay")])
    evidences = Evidence.search(
        [
            ("business_model", "=", "project.project"),
            ("business_id", "=", project.id),
            ("evidence_type", "=", "payment"),
        ]
    )
    evidence_by_source = {(item.source_model, int(item.source_id or 0)): item for item in evidences}
    missing = []
    invalid = []

    for request in requests:
        evidence = evidence_by_source.get(("payment.request", request.id))
        if not evidence:
            missing.append(request.name)
            continue
        if float(evidence.amount or 0.0) != float(request.amount or 0.0):
            invalid.append(f"{request.name}: amount mismatch")

    row = {
        "project_id": int(project.id),
        "payment_request_count": len(requests),
        "payment_evidence_count": len(evidences),
        "missing_sources": missing,
        "invalid_sources": invalid,
    }
    report["projects"][name] = row
    if missing:
        report["errors"].append(f"{name}: missing payment evidence for {', '.join(missing)}")
    if invalid:
        report["errors"].extend(f"{name}: {item}" for item in invalid)

if report["errors"]:
    report["status"] = "FAIL"

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUT_MD.write_text(
    "# Payment Evidence Guard\n\n"
    f"- status: `{report['status']}`\n"
    + "\n".join(
        f"- {name}: requests={row['payment_request_count']} evidences={row['payment_evidence_count']}"
        for name, row in report["projects"].items()
    )
    + ("\n- errors:\n" + "\n".join(f"  - {line}" for line in report["errors"]) if report["errors"] else "\n"),
    encoding="utf-8",
)

if report["errors"]:
    print("[payment_evidence_guard] FAIL")
    for line in report["errors"]:
        print(f" - {line}")
    raise SystemExit(1)

print("[payment_evidence_guard] PASS")
PY
