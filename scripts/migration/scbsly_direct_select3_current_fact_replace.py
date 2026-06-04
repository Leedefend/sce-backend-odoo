#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replace current SCBSLY direct acceptance facts for labels in Select3 dump.

This handles labels whose stable identity is the old list RowIndex. When the
live old system has added rows at the head, counts can remain equal while row
identity drifts. Replaying the current online rows for the affected labels
keeps the user acceptance carrier aligned with the live old system.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


ARTIFACT_NAME = "artifacts/migration/scbsly_direct_select3_status_online_dump_20260603.json"
LABELS = {
    item.strip()
    for item in os.getenv("SCBSLY_SELECT3_REPLACE_LABELS", "入库,零星用工").replace("，", ",").split(",")
    if item.strip()
}

for root in (
    Path("/opt/projects/repos/sce-backend-odoo"),
    Path("/mnt"),
    Path("/mnt/extra-addons"),
    Path.cwd(),
):
    artifact = root / ARTIFACT_NAME
    replay_source = root / "scripts/migration/scbsly_direct_project_direct_acceptance_replay.py"
    if artifact.exists() and replay_source.exists():
        ROOT = root
        ARTIFACT = artifact
        REPLAY_SOURCE = replay_source
        break
else:
    raise RuntimeError({"missing_select3_artifact_or_replay_source": ARTIFACT_NAME})

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

namespace = globals()
namespace["__name__"] = "__scbsly_direct_select3_replace_helper__"
exec(REPLAY_SOURCE.read_text(encoding="utf-8").split("\ndef main():", 1)[0], namespace)

dump = json.loads(ARTIFACT.read_text(encoding="utf-8"))
rows_by_label = {
    label_data.get("label"): label_data.get("rows") or []
    for label_data in dump.get("rows") or []
    if label_data.get("label") in LABELS
}
specs = {
    "入库": {
        "label": "入库",
        "category": "材料管理类单据",
        "config_id": "41cceeadbf804062855559255f1c3cdc",
        "identity_field": "RowIndex",
    },
    "零星用工": {
        "label": "零星用工",
        "category": "劳务管理类单据",
        "config_id": "9acae0644eab4a728a8b70bea7006509",
        "identity_field": "RowIndex",
    },
}

Model = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
project_cache = {}
results = []

for label in sorted(LABELS):
    rows = rows_by_label.get(label) or []
    if not rows:
        results.append({"label": label, "status": "FAIL", "reason": "missing_rows_in_select3_artifact"})
        continue
    spec = specs[label]
    Model.search([("source_system", "=", "online_old_scbsly"), ("acceptance_label", "=", label)]).write(
        {"active": False}
    )
    created = updated = skipped = 0
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            skipped += 1
            continue
        values = namespace["values_for"](row, spec, project_cache)
        key = values["legacy_record_id"]
        if not key or key in seen:
            skipped += 1
            continue
        seen.add(key)
        existing = Model.search(
            [
                ("source_system", "=", "online_old_scbsly"),
                ("acceptance_label", "=", label),
                ("legacy_record_id", "=", key),
            ],
            limit=1,
        )
        if existing:
            existing.write(values)
            updated += 1
        else:
            Model.create(values)
            created += 1
    active_count = Model.search_count(
        [("source_system", "=", "online_old_scbsly"), ("acceptance_label", "=", label), ("active", "=", True)]
    )
    results.append(
        {
            "label": label,
            "input_rows": len(rows),
            "active_count": active_count,
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "status": "PASS" if active_count == len(rows) and not skipped else "FAIL",
        }
    )

env.cr.commit()  # noqa: F821
print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))
if any(item.get("status") != "PASS" for item in results):
    raise RuntimeError(results)
