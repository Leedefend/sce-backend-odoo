# -*- coding: utf-8 -*-
from __future__ import annotations


def _column_exists(cr, table_name, column_name):
    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = %s
           AND column_name = %s
         LIMIT 1
        """,
        (table_name, column_name),
    )
    return bool(cr.fetchone())


def _backfill_bool_column(cr, *, source, target):
    table_name = "project_project"
    if not (
        _column_exists(cr, table_name, source)
        and _column_exists(cr, table_name, target)
    ):
        return 0
    cr.execute(
        """
        UPDATE project_project
           SET {target} = TRUE
         WHERE COALESCE({source}, FALSE) = TRUE
           AND COALESCE({target}, FALSE) = FALSE
        """.format(source=source, target=target)
    )
    return cr.rowcount


def migrate(cr, version):
    showcase_count = _backfill_bool_column(
        cr,
        source="sc_demo_showcase",
        target="sc_project_showcase",
    )
    ready_count = _backfill_bool_column(
        cr,
        source="sc_demo_showcase_ready",
        target="sc_project_showcase_ready",
    )
    print(
        "[17.0.0.60] project showcase fields backfilled: showcase=%s ready=%s"
        % (showcase_count, ready_count)
    )
