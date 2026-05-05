"""Classify legacy fund daily snapshots after enterprise-scope upgrade.

Rows with a business entity are enterprise documents. Older project-bound
snapshots without a business entity are historical project-source rows and must
not appear in the enterprise fund daily entry or summary.

Dry-run by default. Set APPLY=1 to write.
"""

from __future__ import annotations

import json
import os


def main() -> None:
    apply = os.getenv("APPLY") == "1"
    Snapshot = env["sc.legacy.fund.daily.snapshot.fact"].sudo().with_context(active_test=False)  # noqa: F821

    project_source_domain = [
        ("business_entity_id", "=", False),
        ("project_id", "!=", False),
        ("document_scope", "!=", "project"),
    ]
    enterprise_domain = [
        ("business_entity_id", "!=", False),
        ("document_scope", "!=", "enterprise"),
    ]

    project_source_rows = Snapshot.search(project_source_domain)
    enterprise_rows = Snapshot.search(enterprise_domain)

    if apply:
        if project_source_rows:
            project_source_rows.write({"document_scope": "project"})
        if enterprise_rows:
            enterprise_rows.write({"document_scope": "enterprise"})
        env.cr.commit()  # noqa: F821

    payload = {
        "status": "APPLIED" if apply else "DRY_RUN",
        "database": env.cr.dbname,  # noqa: F821
        "project_source_to_classify": len(project_source_rows),
        "enterprise_to_classify": len(enterprise_rows),
        "project_source_after": Snapshot.search_count(
            [
                ("business_entity_id", "=", False),
                ("project_id", "!=", False),
                ("document_scope", "=", "project"),
            ]
        ),
        "enterprise_after": Snapshot.search_count(
            [
                ("business_entity_id", "!=", False),
                ("document_scope", "=", "enterprise"),
            ]
        ),
    }
    print("SCBS_FUND_DAILY_SCOPE_BACKFILL=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
