#!/usr/bin/env python3
"""Project legacy work-part names into construction WBS nodes.

Run inside ``odoo shell``.  This projection only uses parsed legacy facts that
carry an actual work-part label.  Raw ID-only SGBW/QDKM relations remain in the
residual fact table until their name source is available.
"""

from __future__ import annotations

import hashlib
import json


Work = env["construction.work.breakdown"].sudo()  # noqa: F821


def clean(value):
    return str(value or "").strip()


def code_for(project_id, path):
    digest = hashlib.sha1(f"{project_id}:{path}".encode("utf-8")).hexdigest()[:12]
    return f"LEGACY-WP-{digest}"


def level_type_for(depth):
    if depth <= 1:
        return "location"
    if depth == 2:
        return "sub_division"
    if depth == 3:
        return "sub_section"
    return "inspection_lot"


def source_rows(model_name):
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    if "work_part" not in Model._fields:
        return []
    rows = Model.read_group(
        [
            ("active", "=", True),
            ("project_id", "!=", False),
            ("work_part", "!=", False),
        ],
        ["project_id", "work_part"],
        ["project_id", "work_part"],
        lazy=False,
    )
    out = []
    for row in rows:
        project = row.get("project_id")
        work_part = clean(row.get("work_part"))
        if not project or not work_part:
            continue
        out.append(
            {
                "model": model_name,
                "project_id": project[0],
                "work_part": work_part,
                "count": int(row.get("__count") or 0),
            }
        )
    return out


sources = (
    source_rows("sc.legacy.material.stock.fact")
    + source_rows("sc.legacy.labor.subcontract.fact")
    + source_rows("sc.legacy.equipment.lease.fact")
)

paths_by_project = {}
source_fact_count = 0
for item in sources:
    source_fact_count += item["count"]
    path = [clean(part) for part in item["work_part"].replace("/", "-").split("-") if clean(part)]
    if not path:
        continue
    project_paths = paths_by_project.setdefault(item["project_id"], set())
    for index in range(1, len(path) + 1):
        project_paths.add(tuple(path[:index]))

counts = {
    "source_groups": len(sources),
    "source_fact_count": source_fact_count,
    "source_project_count": len(paths_by_project),
    "created": 0,
    "updated": 0,
    "nodes": 0,
}

for project_id, paths in sorted(paths_by_project.items()):
    path_to_node = {}
    for path in sorted(paths, key=lambda value: (len(value), value)):
        parent = path_to_node.get(path[:-1]) if len(path) > 1 else False
        level_type = level_type_for(len(path))
        code = code_for(project_id, "/".join(path))
        vals = {
            "name": path[-1],
            "code": code,
            "project_id": project_id,
            "parent_id": parent.id if parent else False,
            "level_type": level_type,
            "active": True,
            "sequence": len(path) * 10,
        }
        node = Work.search([("project_id", "=", project_id), ("code", "=", code), ("level_type", "=", level_type)], limit=1)
        if node:
            node.write(vals)
            counts["updated"] += 1
        else:
            node = Work.create(vals)
            counts["created"] += 1
        counts["nodes"] += 1
        path_to_node[path] = node

env.cr.commit()  # noqa: F821
print("FRESH_DB_WORK_BREAKDOWN_PROJECTION_WRITE=" + json.dumps({"status": "PASS", "counts": counts}, ensure_ascii=False, sort_keys=True))
