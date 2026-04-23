#!/usr/bin/env python3
"""Build a readonly profile and accelerated migration rebuild-bus plan."""

from __future__ import annotations

import csv
import io
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path.cwd()
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/migration_acceleration_rebuild_bus_profile_v1.json"
OUTPUT_DOC = REPO_ROOT / "docs/migration_alignment/migration_acceleration_rebuild_bus_plan_v1.md"

DB_CONTAINER = os.environ.get("DB_CONTAINER", "sc-backend-odoo-dev-db-1")
DB_USER = os.environ.get("DB_USER", "odoo")
DB_NAME = os.environ.get("DB_NAME", "sc_demo")

SOURCE_FILES = {
    "project": REPO_ROOT / "tmp/raw/project/project.csv",
    "partner_company": REPO_ROOT / "tmp/raw/partner/company.csv",
    "partner_supplier": REPO_ROOT / "tmp/raw/partner/supplier.csv",
    "project_member": REPO_ROOT / "tmp/raw/project_member/project_member.csv",
    "contract": REPO_ROOT / "tmp/raw/contract/contract.csv",
    "receipt": REPO_ROOT / "tmp/raw/receipt/receipt.csv",
    "payment": REPO_ROOT / "tmp/raw/payment/payment.csv",
}

EVIDENCE_FILES = {
    "contract_header_final": REPO_ROOT / "artifacts/migration/contract_header_final_aggregate_confirm_result_v1.json",
    "contract_source_coverage": REPO_ROOT / "artifacts/migration/contract_source_coverage_nodb_screen_result_v1.json",
    "contract_remaining_blockers": REPO_ROOT / "artifacts/migration/contract_remaining_blocker_policy_screen_result_v1.json",
    "contract_partner_anchor_screen": REPO_ROOT / "artifacts/migration/contract_partner_anchor_recovery_screen_result_v1.json",
    "contract_partner_source_57_design": REPO_ROOT / "artifacts/migration/contract_partner_source_57_design_result_v1.json",
    "partner_l4_blocked_remainder": REPO_ROOT / "artifacts/migration/partner_l4_blocked_remainder_consolidated_screen_result_v1.json",
    "project_member_neutral_final": REPO_ROOT / "artifacts/migration/project_member_neutral_aggregate_review_7389_v1.json",
}


def csv_profile(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"exists": False, "rows": 0, "columns": 0, "headers": []}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        headers = next(reader, [])
        rows = sum(1 for _ in reader)
    return {
        "exists": True,
        "rows": rows,
        "columns": len(headers),
        "headers": headers[:80],
    }


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"exists": False}
    return {"exists": True, **json.loads(path.read_text(encoding="utf-8"))}


def psql_copy(sql: str) -> list[dict[str, str]]:
    command = [
        "docker",
        "exec",
        "-i",
        DB_CONTAINER,
        "psql",
        "-U",
        DB_USER,
        "-d",
        DB_NAME,
        "-c",
        f"\\copy ({sql}) TO STDOUT WITH CSV HEADER",
    ]
    proc = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return [dict(row) for row in csv.DictReader(io.StringIO(proc.stdout))]


def target_profile() -> dict[str, object]:
    models = psql_copy(
        """
        select
          m.model,
          coalesce(m.name->>'en_US', m.name::text, '') as name,
          count(f.id)::text as field_count,
          sum(case when f.required then 1 else 0 end)::text as required_fields
        from ir_model m
        left join ir_model_fields f on f.model_id = m.id
        where
          m.model in ('res.partner', 'project.project', 'construction.contract', 'construction.contract.line', 'sc.project.member.staging')
          or m.model ilike '%receipt%'
          or m.model ilike '%payment%'
          or m.model ilike '%settlement%'
        group by m.model, m.name
        order by m.model
        """
    )
    table_counts = psql_copy(
        """
        select 'res_partner' as table_name, count(*)::text as rows from res_partner
        union all
        select 'project_project' as table_name, count(*)::text as rows from project_project
        union all
        select 'construction_contract' as table_name, count(*)::text as rows from construction_contract
        union all
        select 'sc_project_member_staging' as table_name, count(*)::text as rows from sc_project_member_staging
        """
    )
    legacy_fields = psql_copy(
        """
        select model, name
        from ir_model_fields
        where name ilike 'legacy_%'
          and model in ('res.partner', 'project.project', 'construction.contract', 'sc.project.member.staging')
        order by model, name
        """
    )
    return {
        "models": models,
        "table_counts": table_counts,
        "legacy_fields": legacy_fields,
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_doc(profile: dict[str, object]) -> None:
    sources = profile["source_profiles"]
    evidence = profile["migration_evidence"]
    target = profile["target_profile"]
    contract_cov = evidence["contract_source_coverage"]
    remaining = evidence["contract_remaining_blockers"]
    partner_design = evidence["contract_partner_source_57_design"]

    source_lines = "\n".join(
        f"- `{name}`: rows `{info['rows']}`, columns `{info['columns']}`"
        for name, info in sources.items()
    )
    table_lines = "\n".join(
        f"- `{row['table_name']}`: `{row['rows']}` rows"
        for row in target["table_counts"]
    )
    model_lines = "\n".join(
        f"- `{row['model']}`: fields `{row['field_count']}`, required `{row['required_fields']}`"
        for row in target["models"]
    )
    legacy_lines = "\n".join(
        f"- `{row['model']}.{row['name']}`"
        for row in target["legacy_fields"]
    )

    text = f"""# Migration Acceleration Rebuild Bus Plan v1

Status: PASS

Task: `ITER-2026-04-15-MIGRATION-ACCELERATION-REBUILD-BUS-PLAN`

## Objective

Replace slow row-slice migration with a dependency-aware rebuild bus. The
strategy is to profile all legacy source files once, resolve anchors in large
groups, write business facts by dependency lane, and run aggregate reviews after
each lane instead of after every small slice.

## Legacy Source Shape

{source_lines}

Key shape conclusion:

- The legacy source is file-based and denormalized. Contracts carry text
  counterparties and project ids rather than stable target foreign keys.
- Project, partner, project-member, contract, receipt, and payment files are
  separate dependency surfaces; the correct write order is anchors first,
  dependent facts second, financial/high-risk facts last.
- Bad or incomplete legacy rows are common enough that discard policy must be a
  first-class lane, not an exception handled inside every write batch.

## Target Structure Snapshot

Target row counts:

{table_lines}

Target model field shape:

{model_lines}

Legacy identity fields currently available:

{legacy_lines}

Structure conclusion:

- The new system can support high-throughput rebuild if every lane uses legacy
  identity fields as idempotency keys.
- Required foreign keys force strict anchor order: partner/project before
  contract; contract header before line/receipt/payment-style lanes.
- Payment, settlement, and accounting paths remain high-risk and must stay
  behind separate dedicated authority tasks.

## Current Migration Evidence

- Contract header: `{evidence['contract_header_final'].get('target_match_rows')}` rows confirmed in target.
- Contract full source: `{contract_cov.get('source_rows')}` rows total.
- Contract existing or migrated: `{contract_cov.get('header_lane_migrated_rows')}` header-lane + `{contract_cov.get('pre_existing_target_rows')}` pre-existing.
- Contract remaining blocked: `{contract_cov.get('remaining_blocked_rows')}`.
- Remaining blocker routes: `{json.dumps(remaining.get('policy_route_counts'), ensure_ascii=False)}`.
- Partner-source 57 design: `{partner_design.get('design_rows')}` rows, `{partner_design.get('distinct_counterparties')}` distinct counterparties.

## Why The Current Process Is Too Slow

1. It repeatedly performs scan/screen/design/write/review for small row slices.
2. It treats dependent contract rows as the work unit, while the real blocker is
   usually an anchor group such as project id or counterparty text.
3. It runs many post-write reviews that could be collapsed into one aggregate
   review when the write script is idempotent and rollback keyed.
4. It opens downstream readiness after each local success instead of computing a
   global lane manifest and consuming it in larger batches.

## Accelerated Rebuild Bus

### Bus 0: Global Profile Ledger

Create one generated manifest for every legacy file:

- source row count, headers, key fields, delete flags;
- target model/table, legacy identity field, required target anchors;
- discard policy route;
- high-risk domain flag.

This replaces ad hoc per-lane discovery.

### Bus 1: Anchor Lanes

Run anchors as grouped batches, not dependent rows:

- Partner anchor: group by normalized partner name and legacy source identity.
- Project anchor: group by legacy project id.
- User/member anchor: group by project/person/role neutral carrier.

Write size should be based on distinct anchors, not contract rows. For the
current contract blockers, the 57-row contract retry depends on only 12
counterparty anchors.

### Bus 2: Fact Header Lanes

After anchors are stable, write header facts in larger idempotent lanes:

- contract header;
- receipt header;
- later approved high-risk financial headers only under dedicated contracts.

Use fixed lanes of 500-1000 rows when all rows share the same write template and
rollback key.

### Bus 3: Dependent Detail Lanes

Open only after header aggregate closure:

- contract lines or BOQ-bound details;
- receipt/detail rows;
- file attachments or auxiliary facts.

Do not mix line/detail writes with header anchor recovery.

### Bus 4: Discard And Hold Ledger

Discard/hold rows must be materialized as evidence artifacts once per domain:

- deleted legacy rows;
- source-missing anchors;
- direction-deferred contracts;
- ambiguous partner or project anchors;
- high-risk financial rows requiring separate authorization.

This prevents the same bad rows from being re-screened every batch.

### Bus 5: Aggregate Verification

Verification should move from slice-local to lane-global:

- pre-write profile hash;
- write result with legacy ids and rollback ids;
- post-write aggregate count by source/target/rollback;
- residual blocker manifest.

Per-slice post-write review remains only for high-risk batches.

## Immediate Execution Plan

1. Open `CONTRACT-PARTNER-SOURCE-12-ANCHOR-DESIGN`: collapse the 57 contract rows
   into 12 distinct company-source partner anchors.
2. Open one bounded partner-anchor write only if the 12-anchor design proves
   idempotent and rollback-keyed.
3. Re-run contract readiness only for the 57 dependent contract ids after the
   12 anchors exist.
4. Keep 65 deleted, 88 project-source-missing, 74 partner-source-missing, and 61
   direction-deferred rows in discard/hold artifacts; do not re-screen them in
   every batch.
5. Generate a global migration manifest for receipt/payment-style source files,
   but do not open payment, settlement, or accounting writes without dedicated
   high-risk task contracts.

## New Batch Size Rule

- No-DB scan/screen/design: full lane, not 100/200 row slices.
- Low-risk create-only writes with stable anchors: 500-1000 rows.
- Anchor writes: distinct anchor count, normally 50-500 per batch.
- High-risk authority/financial writes: dedicated task and smaller batch.
- Aggregate reviews: one per lane after write completion.

## Stop Rules

- Any failed `make verify.*` stops the bus.
- Any payment/settlement/accounting write requires a dedicated high-risk task.
- Any missing legacy identity stops DB write and stays in design.
- Any frontend or ACL need is a separate task line.
"""
    OUTPUT_DOC.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_DOC.write_text(text, encoding="utf-8")


def main() -> int:
    profile = {
        "status": "PASS",
        "mode": "migration_acceleration_rebuild_bus_plan",
        "database": DB_NAME,
        "db_writes": 0,
        "source_profiles": {name: csv_profile(path) for name, path in SOURCE_FILES.items()},
        "migration_evidence": {name: load_json(path) for name, path in EVIDENCE_FILES.items()},
        "target_profile": target_profile(),
        "decision": "accelerated_rebuild_bus_ready",
        "next_step": "open 12-counterparty partner-anchor no-DB design",
    }
    write_json(OUTPUT_JSON, profile)
    write_doc(profile)
    print(
        "MIGRATION_ACCELERATION_REBUILD_BUS_PLAN="
        + json.dumps(
            {
                "status": profile["status"],
                "source_files": len(profile["source_profiles"]),
                "db_writes": 0,
                "decision": profile["decision"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
