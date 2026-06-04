# -*- coding: utf-8 -*-
"""Backfill SCBSLY direct acceptance attachment refs from raw visible rows.

Run through ``odoo shell``. The visible acceptance rows may show ``附件(n)``
even when the carrier ``attachment_ref`` is empty, because the old list payload
contains a raw ``FJ`` BillId. Click/download must use that BillId.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


LABEL_FILTER = {
    item.strip()
    for item in re.split(r"[,，]", os.getenv("SCBSLY_DIRECT_ATTACHMENT_BACKFILL_LABELS", ""))
    if item.strip()
}
SOURCE_SYSTEM = os.getenv("SCBSLY_DIRECT_ATTACHMENT_SOURCE", "online_old_scbsly")
OUTPUT_JSON = Path(
    os.getenv(
        "SCBSLY_DIRECT_ATTACHMENT_BACKFILL_OUTPUT",
        "/tmp/scbsly_direct_attachment_ref_backfill_result_v1.json",
    )
)
ATTACHMENT_ID_RE = re.compile(r"^[0-9a-fA-F]{32}$")
ATTACHMENT_LABEL_RE = re.compile(r"^附件\([1-9]\d*\)$")
ATTACHMENT_FIELDS = ("FJ", "f_FJ")


def clean(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def attachment_ref_value(row, acceptance_label=""):
    if acceptance_label == "分包方单" and not ATTACHMENT_LABEL_RE.match(clean(row.get("f_FJ"))):
        return ""
    for field in ATTACHMENT_FIELDS:
        value = clean(row.get(field))
        if value and ATTACHMENT_ID_RE.match(value):
            return value
    for field in ATTACHMENT_FIELDS:
        value = clean(row.get(field))
        if value and not ATTACHMENT_LABEL_RE.match(value):
            return value
    return ""


def main():
    Model = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
    domain = [("source_system", "=", SOURCE_SYSTEM)]
    if LABEL_FILTER:
        domain.append(("acceptance_label", "in", sorted(LABEL_FILTER)))
    records = Model.search(domain, order="acceptance_label, id")
    counts = Counter()
    examples = []
    for record in records:
        counts["checked"] += 1
        try:
            payload = json.loads(record.raw_payload or "{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            counts["invalid_payload"] += 1
            continue
        if not isinstance(payload, dict):
            counts["invalid_payload"] += 1
            continue
        expected = attachment_ref_value(payload, record.acceptance_label or "")
        current = clean(record.attachment_ref)
        if not expected:
            if current:
                record.write({"attachment_ref": False})
                counts["cleared"] += 1
                if len(examples) < 20:
                    examples.append(
                        {
                            "record_id": record.id,
                            "label": record.acceptance_label,
                            "legacy_record_id": record.legacy_record_id,
                            "document_no": record.document_no,
                            "old_attachment_ref": current,
                            "new_attachment_ref": "",
                        }
                    )
            else:
                counts["no_payload_attachment_ref"] += 1
            continue
        if current == expected:
            counts["already_ok"] += 1
            continue
        record.write({"attachment_ref": expected})
        counts["updated"] += 1
        if len(examples) < 20:
            examples.append(
                {
                    "record_id": record.id,
                    "label": record.acceptance_label,
                    "legacy_record_id": record.legacy_record_id,
                    "document_no": record.document_no,
                    "old_attachment_ref": current,
                    "new_attachment_ref": expected,
                }
            )
    env.cr.commit()  # noqa: F821
    result = {
        "status": "PASS",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_name": env.cr.dbname,  # noqa: F821
        "source_system": SOURCE_SYSTEM,
        "label_filter": sorted(LABEL_FILTER),
        "counts": dict(counts),
        "examples": examples,
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


main()
