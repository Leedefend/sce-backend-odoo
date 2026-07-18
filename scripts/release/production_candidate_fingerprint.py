"""Read-only, redacted release fingerprint for an Odoo database."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


MODELS = {
    "companies": "res.company",
    "users": "res.users",
    "partners": "res.partner",
    "projects": "project.project",
    "contracts": "construction.contract",
    "settlements": "sc.settlement.order",
    "payment_requests": "payment.request",
    "payment_executions": "sc.payment.execution",
    "ledgers": "payment.ledger",
    "attachments": "ir.attachment",
    "config_contracts": "ui.business.config.contract",
    "config_versions": "ui.business.config.contract.version",
    "low_code_change_sets": "ui.business.config.change.set",
}
AMOUNTS = {
    "construction.contract": ("amount_total", "amount", "contract_amount"),
    "sc.settlement.order": ("amount_total", "settlement_amount", "amount"),
    "payment.request": ("amount", "amount_total"),
    "sc.payment.execution": ("amount", "actual_amount", "paid_amount"),
    "payment.ledger": ("amount", "amount_total"),
}
RELATIONS = {
    "construction.contract": ("project_id",),
    "sc.settlement.order": ("contract_id", "project_id"),
    "payment.request": ("settlement_id", "contract_id", "project_id", "partner_id"),
    "sc.payment.execution": ("payment_request_id",),
    "payment.ledger": ("payment_request_id",),
}


def count(model_name):
    return env[model_name].sudo().search_count([]) if model_name in env else None


def amount_summary(model_name):
    if model_name not in env:
        return None
    model = env[model_name].sudo()
    field = next((name for name in AMOUNTS[model_name] if name in model._fields), None)
    if not field:
        return {"field": None, "sum": "0.00"}
    rows = model.read_group([], [f"{field}:sum"], [])
    value = rows[0].get(field, 0.0) if rows else 0.0
    return {"field": field, "sum": f"{float(value or 0.0):.2f}"}


def relation_summary(model_name):
    if model_name not in env:
        return None
    model = env[model_name].sudo()
    return {
        field: model.search_count([(field, "=", False)])
        for field in RELATIONS[model_name]
        if field in model._fields
    }


def structural_digest():
    digest = hashlib.sha256()
    for label, model_name in MODELS.items():
        if model_name not in env:
            digest.update(f"{label}:missing\n".encode())
            continue
        model = env[model_name].sudo()
        relation_fields = [name for name in RELATIONS.get(model_name, ()) if name in model._fields]
        fields = ["id", *relation_fields]
        for row in model.search_read([], fields, order="id"):
            values = [str(row["id"])]
            for field in relation_fields:
                value = row.get(field)
                values.append(str(value[0] if isinstance(value, (list, tuple)) and value else 0))
            digest.update((model_name + ":" + ":".join(values) + "\n").encode())
    return digest.hexdigest()


filestore_root = Path(env["ir.attachment"]._filestore())
filestore_digest = hashlib.sha256()
filestore_files = []
if filestore_root.exists():
    filestore_files = sorted(path for path in filestore_root.rglob("*") if path.is_file())
    for path in filestore_files:
        relative = path.relative_to(filestore_root).as_posix()
        filestore_digest.update(relative.encode() + b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                filestore_digest.update(chunk)

modules = env["ir.module.module"].sudo().search_read(
    [("name", "like", "smart_%")], ["name", "state", "installed_version"], order="name"
)
pending = [row["name"] for row in modules if row["state"] in {"to install", "to upgrade", "to remove"}]
payload = {
    "schema_version": 1,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "database": env.cr.dbname,
    "mode": "read_only_redacted",
    "counts": {label: count(model) for label, model in MODELS.items()},
    "amounts": {model: amount_summary(model) for model in AMOUNTS},
    "missing_relations": {model: relation_summary(model) for model in RELATIONS},
    "structural_digest": structural_digest(),
    "filestore": {
        "file_count": len(filestore_files),
        "bytes": sum(path.stat().st_size for path in filestore_files),
        "sha256": filestore_digest.hexdigest(),
    },
    "modules": modules,
    "pending_modules": pending,
    "demo_module_state": next((row["state"] for row in modules if row["name"] == "smart_construction_demo"), "uninstalled"),
    "sensitive_values_included": False,
}
canonical = dict(payload)
canonical.pop("generated_at", None)
canonical.pop("database", None)
payload["fingerprint_sha256"] = hashlib.sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
path = Path(os.environ.get("CANDIDATE_FINGERPRINT_PATH", "/tmp/production-candidate-fingerprint.json"))
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
print("CANDIDATE_FINGERPRINT=" + json.dumps({"database": payload["database"], "fingerprint": payload["fingerprint_sha256"], "counts": payload["counts"]}))
