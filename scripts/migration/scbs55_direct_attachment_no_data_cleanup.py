# -*- coding: utf-8 -*-
"""Hide direct-acceptance attachment buttons whose old-system BillId has no files.

Run inside Odoo shell. Set APPLY=1 to update records; otherwise it only reports.
The raw_payload keeps the original old-system value for audit traceability.
"""

import json
import os
from pathlib import Path


def _artifact_root():
    candidates = [
        Path("/mnt/artifacts/migration"),
        Path("artifacts/migration"),
        Path("/tmp"),
    ]
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except OSError:
            continue
    return Path("/tmp")


def _read_refs(path):
    refs = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        ref = line.strip()
        if ref:
            refs.append(ref)
    return list(dict.fromkeys(refs))


refs_path = os.getenv("SC_DIRECT_ATTACHMENT_NO_DATA_REFS_PATH", "/mnt/tmp/direct_no_data_refs.txt")
apply_changes = os.getenv("APPLY", "0") == "1"
refs = _read_refs(refs_path)

Model = env["sc.legacy.direct.acceptance.fact"].sudo()  # noqa: F821
domain = [("active", "=", True), ("attachment_ref", "in", refs)]
records = Model.search(domain)

by_label = {}
for record in records:
    by_label[record.acceptance_label or ""] = by_label.get(record.acceptance_label or "", 0) + 1

if apply_changes and records:
    records.write({"attachment_ref": False})
    env.cr.commit()  # noqa: F821

payload = {
    "mode": "scbs55_direct_attachment_no_data_cleanup",
    "apply": apply_changes,
    "refs_path": refs_path,
    "input_ref_count": len(refs),
    "matched_record_count": len(records),
    "by_acceptance_label": dict(sorted(by_label.items())),
}

out = _artifact_root() / "scbs55_direct_attachment_no_data_cleanup_v1.json"
try:
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
except PermissionError:
    out = Path("/tmp/scbs55_direct_attachment_no_data_cleanup_v1.json")
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
print("REPORT", out)
