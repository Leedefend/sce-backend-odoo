"""Accept SCBS fund daily enterprise-document projection.

This is a focused guard for the口径 shift:
- SCBS fund daily rows are enterprise/business-entity documents;
- SCBS fund daily rows must not bind to project_id;
- enterprise summary must exclude project-source rows while preserving source
  totals.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


SOURCE_TABLE = "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"
IMPORT_BATCH = "scbs_fund_daily_enterprise_v1"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path("/tmp")


def fetch_one(sql: str) -> dict[str, object]:
    env.cr.execute(sql)  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return dict(zip(names, row or []))


def float_equal(left: object, right: object) -> bool:
    return abs(float(left or 0) - float(right or 0)) < 0.01


def main() -> None:
    artifacts = artifact_root()
    output_json = artifacts / "scbs_fund_daily_enterprise_acceptance_result_v1.json"
    output_md = artifacts / "scbs_fund_daily_enterprise_acceptance_v1.md"

    formal = fetch_one(
        """
        SELECT COUNT(*) AS rows,
               COUNT(business_entity_id) AS with_business_entity,
               COUNT(project_id) AS with_project,
               ROUND(COALESCE(SUM(source_account_balance_total), 0)::numeric, 2) AS account_balance_total,
               ROUND(COALESCE(SUM(source_bank_balance_total), 0)::numeric, 2) AS bank_balance_total,
               ROUND(COALESCE(SUM(source_bank_system_difference), 0)::numeric, 2) AS bank_system_difference_total
          FROM sc_legacy_fund_daily_snapshot_fact
         WHERE legacy_source_table = '%s'
           AND import_batch = '%s'
        """
        % (SOURCE_TABLE, IMPORT_BATCH)
    )
    scope = fetch_one(
        """
        SELECT COUNT(*) FILTER (WHERE document_scope = 'enterprise') AS enterprise_rows,
               COUNT(*) FILTER (WHERE document_scope = 'project') AS project_source_rows,
               COUNT(*) FILTER (WHERE document_scope = 'enterprise' AND project_id IS NOT NULL) AS enterprise_with_project,
               COUNT(*) FILTER (WHERE document_scope = 'enterprise' AND business_entity_id IS NULL) AS enterprise_missing_entity
          FROM sc_legacy_fund_daily_snapshot_fact
        """
    )
    summary = fetch_one(
        """
        SELECT COUNT(*) AS rows,
               COALESCE(SUM(line_count), 0) AS summarized_source_rows,
               COUNT(project_id) AS with_project,
               ROUND(COALESCE(SUM(current_account_balance), 0)::numeric, 2) AS account_balance_total,
               ROUND(COALESCE(SUM(current_bank_balance), 0)::numeric, 2) AS bank_balance_total,
               ROUND(COALESCE(SUM(bank_system_difference), 0)::numeric, 2) AS bank_system_difference_total
          FROM sc_fund_daily_summary
        """
    )
    action = fetch_one(
        """
        SELECT COALESCE(a.domain, '') AS domain,
               COALESCE(a.context, '') AS context
          FROM ir_model_data d
          JOIN ir_act_window a ON a.id = d.res_id
         WHERE d.module = 'smart_construction_core'
           AND d.name = 'action_sc_fund_daily'
           AND d.model = 'ir.actions.act_window'
         LIMIT 1
        """
    )

    checks = {
        "formal_rows": int(formal["rows"] or 0) == 3798,
        "formal_all_have_business_entity": formal["rows"] == formal["with_business_entity"],
        "formal_has_no_project": int(formal["with_project"] or 0) == 0,
        "scope_enterprise_rows": int(scope["enterprise_rows"] or 0) == 3798,
        "scope_project_source_rows": int(scope["project_source_rows"] or 0) == 496,
        "scope_enterprise_no_project": int(scope["enterprise_with_project"] or 0) == 0,
        "scope_enterprise_no_missing_entity": int(scope["enterprise_missing_entity"] or 0) == 0,
        "summary_source_rows_match": summary["summarized_source_rows"] == formal["rows"],
        "summary_has_no_project": int(summary["with_project"] or 0) == 0,
        "summary_account_balance_match": float_equal(summary["account_balance_total"], formal["account_balance_total"]),
        "summary_bank_balance_match": float_equal(summary["bank_balance_total"], formal["bank_balance_total"]),
        "summary_difference_match": float_equal(summary["bank_system_difference_total"], formal["bank_system_difference_total"]),
        "action_domain_has_enterprise_scope": "document_scope" in str(action.get("domain") or "")
        and "business_entity_id" in str(action.get("domain") or ""),
    }
    status = "PASS" if all(checks.values()) else "REVIEW_REQUIRED"
    payload = {
        "status": status,
        "database": env.cr.dbname,  # noqa: F821
        "formal": formal,
        "scope": scope,
        "summary": summary,
        "action": action,
        "checks": checks,
    }
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(
        "\n".join(
            [
                "# SCBS Fund Daily Enterprise Acceptance",
                "",
                "Status: `%s`" % status,
                "",
                "- formal rows: %(rows)s; with business entity: %(with_business_entity)s; with project: %(with_project)s"
                % formal,
                "- summary rows: %(rows)s; summarized source rows: %(summarized_source_rows)s; with project: %(with_project)s"
                % summary,
                "- enterprise scope rows: %(enterprise_rows)s; project-source rows: %(project_source_rows)s"
                % scope,
                "- account balance total: %(account_balance_total)s" % formal,
                "- bank balance total: %(bank_balance_total)s" % formal,
                "- bank-system difference total: %(bank_system_difference_total)s" % formal,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print("SCBS_FUND_DAILY_ENTERPRISE_ACCEPTANCE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
