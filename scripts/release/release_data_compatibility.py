"""Read-only Odoo-shell compatibility audit. Never calls create/write/unlink/sudo."""
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

report_path = Path(os.environ.get("RELEASE_REPORT_PATH", "/tmp/release-data-compatibility.json"))
model_names = [
    "res.company", "res.users", "project.project", "construction.contract",
    "sc.settlement.order", "payment.request", "sc.payment.execution",
    "payment.ledger", "res.partner", "res.currency", "ir.attachment",
]
modules = ["smart_core", "smart_construction_core", "smart_construction_bundle", "smart_construction_demo"]
module_rows = env["ir.module.module"].search_read([("name", "in", modules)], ["name", "state", "installed_version"])
module_map = {row["name"]: {"state": row["state"], "version": row.get("installed_version") or ""} for row in module_rows}

findings = []
counts = {}
for name in model_names:
    if name not in env:
        findings.append({"severity": "BLOCKER", "code": "missing_model", "reference": name})
        continue
    counts[name] = env[name].search_count([])

bad_states = {name: data["state"] for name, data in module_map.items() if data["state"] in {"to install", "to upgrade", "to remove"}}
if bad_states:
    findings.append({"severity": "BLOCKER", "code": "pending_module_state", "reference": sorted(bad_states)})
if module_map.get("smart_construction_demo", {}).get("state") == "installed":
    findings.append({"severity": "BLOCKER", "code": "demo_module_installed", "reference": "smart_construction_demo"})

users = env["res.users"].search_read([], ["active", "company_id", "company_ids", "login"])
invalid_company_users = sum(1 for user in users if not user.get("company_id"))
if invalid_company_users:
    findings.append({"severity": "BLOCKER", "code": "user_without_company", "count": invalid_company_users})
demo_logins = {"demo_role_finance", "demo_role_project_a_member", "demo_role_pm", "demo_role_owner", "demo_role_executive"}
present_demo = sorted(demo_logins.intersection({u.get("login") for u in users}))
if present_demo:
    findings.append({"severity": "BLOCKER", "code": "demo_accounts_present", "count": len(present_demo)})

relation_specs = [
    ("construction.contract", "project_id"),
    ("sc.settlement.order", "contract_id"),
    ("payment.request", "settlement_id"),
    ("sc.payment.execution", "payment_request_id"),
]
for model, field in relation_specs:
    if model in env and field in env[model]._fields:
        missing = env[model].search_count([(field, "=", False)])
        if missing:
            findings.append({"severity": "WARN", "code": "missing_relation", "reference": f"{model}.{field}", "count": missing})

for model in ("construction.contract", "sc.settlement.order", "payment.request", "sc.payment.execution", "payment.ledger"):
    if model not in env:
        continue
    fields = env[model]._fields
    currency_field = next((f for f in ("currency_id", "company_currency_id") if f in fields), None)
    if currency_field:
        missing = env[model].search_count([(currency_field, "=", False)])
        if missing:
            findings.append({"severity": "WARN", "code": "missing_currency", "reference": f"{model}.{currency_field}", "count": missing})

filestore_root = Path(env["ir.attachment"]._filestore())
stored = env["ir.attachment"].search_read([("store_fname", "!=", False)], ["store_fname"], limit=5000)
missing_files = sum(1 for row in stored if not (filestore_root / row["store_fname"]).is_file())
if missing_files:
    findings.append({"severity": "BLOCKER", "code": "missing_filestore_object", "count": missing_files, "sample_limited": len(stored) == 5000})

severity = Counter(item["severity"] for item in findings)
report = {
    "schema_version": 1,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "database": env.cr.dbname,
    "mode": "read_only",
    "source_class": os.environ.get("RELEASE_DATA_SOURCE_CLASS", "production_shaped_sample"),
    "module_states": module_map,
    "counts": counts,
    "filestore": {"checked_objects": len(stored), "missing_objects": missing_files},
    "findings": findings,
    "summary": dict(severity),
    "pass": severity.get("BLOCKER", 0) == 0,
}
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("RELEASE_DATA_COMPATIBILITY=" + json.dumps({"pass": report["pass"], "counts": counts, "summary": report["summary"]}, ensure_ascii=False))
if not report["pass"]:
    raise SystemExit(1)
