# Business Fact Upgrade Replay Flow v1

Status: `ready_for_acceptance_postcheck`

Task: `ITER-2026-05-07-BUSINESS-FACT-UPGRADE-REPLAY`

## Purpose

This flow upgrades the business fact replay layer after project master anchors.
It focuses on the contract-visible business facts that users validate in the
acceptance database:

- income and expense contract split integrity;
- contract lines;
- visible invoice and receipt facts derived from legacy construction contracts;
- legacy purchase contract facts projected into general contracts.

## Command

Static guard:

```bash
make verify.native.business_fact.static
```

Read-only acceptance postcheck:

```bash
BUSINESS_FACT_REPLAY_MODE=postcheck \
DB_NAME=sc_partner_acceptance \
MIGRATION_REPLAY_DB_ALLOWLIST=sc_partner_acceptance \
bash scripts/migration/business_fact_upgrade_replay_flow.sh
```

Read-only acceptance bundle:

```bash
BUSINESS_FACT_REPLAY_MODE=acceptance \
DB_NAME=sc_partner_acceptance \
MIGRATION_REPLAY_DB_ALLOWLIST=sc_partner_acceptance \
bash scripts/migration/business_fact_upgrade_replay_flow.sh
```

Attach old-source evidence to the acceptance bundle explicitly when the old
MSSQL container is available:

```bash
BUSINESS_FACT_REPLAY_LEGACY_SOURCE_PROBE=1 \
BUSINESS_FACT_REPLAY_MODE=acceptance \
DB_NAME=sc_partner_acceptance \
MIGRATION_REPLAY_DB_ALLOWLIST=sc_partner_acceptance \
bash scripts/migration/business_fact_upgrade_replay_flow.sh
```

Read-only visible balance cleanup, also run automatically at the end of `write`
and `all`:

```bash
BUSINESS_FACT_REPLAY_MODE=cleanup \
DB_NAME=sc_partner_acceptance \
MIGRATION_REPLAY_DB_ALLOWLIST=sc_partner_acceptance \
bash scripts/migration/business_fact_upgrade_replay_flow.sh
```

Read-only old-source probe for the cleanup observations:

```bash
MIGRATION_ARTIFACT_ROOT=/path/to/business_fact_cleanup_run \
BUSINESS_FACT_REPLAY_MODE=legacy-source \
bash scripts/migration/business_fact_upgrade_replay_flow.sh
```

Attach the old-source probe to `write` / `all` explicitly when the old MSSQL
container is available:

```bash
BUSINESS_FACT_REPLAY_LEGACY_SOURCE_PROBE=1 \
BUSINESS_FACT_REPLAY_MODE=all \
DB_NAME=sc_partner_acceptance \
MIGRATION_REPLAY_DB_ALLOWLIST=sc_partner_acceptance \
bash scripts/migration/business_fact_upgrade_replay_flow.sh
```

Adapter refresh:

```bash
BUSINESS_FACT_REPLAY_MODE=adapters \
bash scripts/migration/business_fact_upgrade_replay_flow.sh
```

The legacy purchase contract adapter depends on the old source database
container. It is skipped by default and can be refreshed explicitly with
`BUSINESS_FACT_REPLAY_REFRESH_LEGACY_PURCHASE=1` when the old source is online.

Guarded write replay:

```bash
BUSINESS_FACT_REPLAY_MODE=write \
BUSINESS_FACT_REPLAY_EXECUTE_WRITES=1 \
DB_NAME=sc_partner_acceptance \
MIGRATION_REPLAY_DB_ALLOWLIST=sc_partner_acceptance \
bash scripts/migration/business_fact_upgrade_replay_flow.sh
```

`write` and `all` are intentionally gated by
`BUSINESS_FACT_REPLAY_EXECUTE_WRITES=1`.

The static guard is host-only and should be run before database replay. It checks
the business-fact shell flow and Python scripts for syntax/compile drift without
touching Odoo or legacy MSSQL.

The `acceptance` mode is the preferred read-only handoff command. It runs the
postcheck and cleanup in the same artifact root, and adds legacy-source evidence
only when `BUSINESS_FACT_REPLAY_LEGACY_SOURCE_PROBE=1`.

`acceptance`, `write`, and `all` emit a final summary:

- `business_fact_additional_fact_inventory_v1.json`
- `business_fact_additional_fact_inventory_v1.md`
- `business_fact_acceptance_bundle_summary_v1.json`
- `business_fact_acceptance_bundle_summary_v1.md`

The additional fact inventory is read-only. It summarizes 44 existing adapter
artifact lanes across project, partner, contract, receipt, outflow, invoice,
tax, fund, account, construction diary, evidence, catalog, attachment,
workflow, user context, and residual facts. Where an adapter declares row
artifacts, it also checks payload CSV presence and parsed record counts. It does
not create or replay those rows into Odoo.

## Acceptance Facts

The current acceptance target is:

| Surface | Expected |
| --- | ---: |
| project anchors | 798 |
| all legacy construction contracts | 6850 |
| income contracts | 1541 |
| expense contracts | 5309 |
| contract lines | 6566 |
| legacy purchase contract facts | 49 |
| projected general contracts | 41 |
| visible invoice facts | 6 |
| visible receipt facts | 5 |

The postcheck also verifies that every `construction.contract` row has exactly
one matching professional wrapper in either `construction.contract.income` or
`construction.contract.expense`, and that visible invoice/receipt facts still
reconcile back to the user-visible invoice and receipt fields. Legacy visible
unreceived-balance differences are emitted as observations because the current
model computes the balance from replayed invoice/receipt facts while the old
surface may carry over-receipt or manual balance values.

The cleanup mode expands those observations into classified rows without writing
business records. A visible balance alone must not create a negative receipt,
over-receipt, or manual correction row until an independent source table proves
that transaction fact.

The legacy-source probe checks `T_ProjectContract_Out`, `C_JFHKLR`, and
`C_JXXP_XXKPDJ` for those observations. It is opt-in at the end of `write` and
`all` so production-style rebuilds do not depend on the old MSSQL container,
while acceptance runs can still carry both platform postcheck evidence and
old-source fact evidence.

When run as a standalone mode, `legacy-source` reads the cleanup result from the
same `MIGRATION_ARTIFACT_ROOT`; use `BUSINESS_FACT_CLEANUP_RESULT_JSON` only for
intentional inspection of an older cleanup artifact.

Decision marker:

`business_fact_replay_acceptance_passed`
