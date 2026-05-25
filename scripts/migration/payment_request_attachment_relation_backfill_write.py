#!/usr/bin/env python3
"""Link migrated payment request attachments to the user-facing attachment field."""

from __future__ import annotations

import json
import os


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def fetch_count() -> int:
    row = env.cr.fetchone()  # noqa: F821
    return int(row[0] or 0) if row else 0


ensure_allowed_db()

env.cr.execute(  # noqa: F821
    """
    SELECT count(*)
      FROM payment_request_attachment_rel
    """
)
before_rel_count = fetch_count()

env.cr.execute(  # noqa: F821
    """
    INSERT INTO payment_request_attachment_rel (request_id, attachment_id)
    SELECT a.res_id, a.id
      FROM ir_attachment a
      JOIN payment_request r ON r.id = a.res_id
     WHERE a.res_model = 'payment.request'
       AND a.res_id IS NOT NULL
       AND NOT EXISTS (
             SELECT 1
               FROM payment_request_attachment_rel rel
              WHERE rel.request_id = a.res_id
                AND rel.attachment_id = a.id
       )
    """
)
direct_links_created = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO payment_request_attachment_rel (request_id, attachment_id)
    SELECT line.request_id, a.id
      FROM ir_attachment a
      JOIN payment_request_line line ON line.id = a.res_id
      JOIN payment_request request ON request.id = line.request_id
     WHERE a.res_model = 'payment.request.line'
       AND line.request_id IS NOT NULL
       AND NOT EXISTS (
             SELECT 1
               FROM payment_request_attachment_rel rel
              WHERE rel.request_id = line.request_id
                AND rel.attachment_id = a.id
       )
    """
)
line_links_created = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    SELECT count(DISTINCT request_id), count(*)
      FROM payment_request_attachment_rel
    """
)
requests_with_attachments, after_rel_count = env.cr.fetchone()  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    SELECT count(*)
      FROM ir_attachment
     WHERE res_model = 'payment.request'
       AND coalesce(url, '') <> ''
    """
)
direct_url_attachments = fetch_count()

env.cr.commit()  # noqa: F821

print(
    "PAYMENT_REQUEST_ATTACHMENT_RELATION_BACKFILL="
    + json.dumps(
        {
            "database": env.cr.dbname,  # noqa: F821
            "mode": "payment_request_attachment_relation_backfill_write",
            "status": "PASS",
            "before_rel_count": before_rel_count,
            "direct_links_created": direct_links_created,
            "line_links_created": line_links_created,
            "after_rel_count": int(after_rel_count or 0),
            "requests_with_attachments": int(requests_with_attachments or 0),
            "direct_url_attachments": direct_url_attachments,
            "decision": "linked_existing_migrated_ir_attachment_urls_to_payment_request_attachment_ids",
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
