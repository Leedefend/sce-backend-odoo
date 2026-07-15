import json
import os
from datetime import datetime, timezone
from pathlib import Path

models = ["res.company", "res.users", "project.project", "construction.contract", "sc.settlement.order", "payment.request", "sc.payment.execution", "payment.ledger", "ir.attachment"]
modules = env["ir.module.module"].search_read([("name", "like", "smart_%")], ["name", "state", "installed_version"])
root = Path(env["ir.attachment"]._filestore())
files = [p for p in root.rglob("*") if p.is_file()] if root.exists() else []
payload = {
    "schema_version": 1,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "database": env.cr.dbname,
    "counts": {name: env[name].search_count([]) if name in env else None for name in models},
    "modules": sorted(({"name": m["name"], "state": m["state"], "version": m.get("installed_version") or ""} for m in modules), key=lambda x: x["name"]),
    "filestore": {"file_count": len(files), "bytes": sum(p.stat().st_size for p in files)},
}
path = Path(os.environ["RELEASE_FINGERPRINT_PATH"])
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("RELEASE_FINGERPRINT=" + json.dumps({"database": payload["database"], "counts": payload["counts"], "filestore": payload["filestore"]}))
