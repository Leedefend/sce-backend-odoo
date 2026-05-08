# Business Fact Data Cleanup v1

Status: `ready_for_acceptance_screening`

Task: `ITER-2026-05-07-BUSINESS-FACT-DATA-CLEANUP`

## Purpose

This cleanup lane separates replayable business facts from legacy visible
balance fields on construction contracts.

The current acceptance replay proves that invoice and receipt facts reconcile
with the visible `累计开票` and `累计收款` columns. The remaining visible balance
differences are therefore treated as legacy surface observations until a source
table or approved accounting adjustment lane proves that they are independent
transaction facts.

## Command

Static guard:

```bash
make verify.native.business_fact.static
```

Acceptance cleanup:

```bash
BUSINESS_FACT_REPLAY_MODE=cleanup \
DB_NAME=sc_partner_acceptance \
MIGRATION_REPLAY_DB_ALLOWLIST=sc_partner_acceptance \
bash scripts/migration/business_fact_upgrade_replay_flow.sh
```

Outputs:

- `business_fact_visible_balance_cleanup_result_v1.json`
- `business_fact_visible_balance_cleanup_rows_v1.csv`
- `business_fact_visible_balance_cleanup_report_v1.md`

Optional old-source probe after cleanup:

```bash
MIGRATION_ARTIFACT_ROOT=/path/to/business_fact_cleanup_run \
BUSINESS_FACT_REPLAY_MODE=legacy-source \
bash scripts/migration/business_fact_upgrade_replay_flow.sh
```

Or attach it to `write` / `all` explicitly:

```bash
BUSINESS_FACT_REPLAY_LEGACY_SOURCE_PROBE=1 \
BUSINESS_FACT_REPLAY_MODE=all \
DB_NAME=sc_partner_acceptance \
MIGRATION_REPLAY_DB_ALLOWLIST=sc_partner_acceptance \
bash scripts/migration/business_fact_upgrade_replay_flow.sh
```

Outputs:

- `business_fact_visible_balance_legacy_source_probe_result_v1.json`
- `business_fact_visible_balance_legacy_source_probe_rows_v1.csv`
- `business_fact_visible_balance_legacy_source_probe_report_v1.md`

When cleanup runs as part of `BUSINESS_FACT_REPLAY_MODE=acceptance`, `write`, or
`all`, the flow also emits:

- `business_fact_additional_fact_inventory_v1.json`
- `business_fact_additional_fact_inventory_v1.md`
- `business_fact_acceptance_bundle_summary_v1.json`
- `business_fact_acceptance_bundle_summary_v1.md`

The additional fact inventory currently covers 44 replay artifact lanes. For
lanes that declare row artifacts, it also verifies that the CSV payload exists
and that parsed CSV record counts match the adapter result.

## Classification Contract

| Classification | Meaning | Replay decision |
| --- | --- | --- |
| `legacy_visible_negative_balance_without_transaction_fact` | The old visible balance is negative while visible invoice and receipt facts are both zero. | Do not create a negative receipt or correction row from the balance alone. |
| `legacy_visible_over_receipt_or_manual_credit_balance` | The old visible balance implies over-receipt or a manual credit balance. | Requires a dedicated adjustment lane before replay. |
| `legacy_visible_partial_or_closed_balance_without_transaction_fact` | The old visible balance implies partial/closed collection but no visible transaction facts exist. | Keep as observation until old source detail is proven. |
| `legacy_visible_manual_balance_delta` | Invoice/receipt facts reconcile, but visible balance still differs. | Keep as observation; do not override computed platform balance. |

## Guardrail

The script is read-only. It records `db_writes: 0` and fails only when the
invoice/receipt facts no longer reconcile. Balance deltas alone are not replay
blockers because the current model computes receivables from contract amount and
materialized invoice/receipt facts.

The static guard is host-only. It verifies shell syntax and Python compilation
for the business-fact replay/postcheck/cleanup scripts without connecting to the
acceptance database or legacy MSSQL container.

The old-source probe is also read-only and is opt-in for `write` / `all` because
production-style rebuilds do not require the legacy MSSQL container. It checks
`T_ProjectContract_Out` plus linked receipt and invoice candidates
(`C_JFHKLR`, `C_JXXP_XXKPDJ`). If those candidate tables have no linked rows, the
visible balance remains a legacy surface observation rather than a transaction
replay source.

`legacy-source` reads
`business_fact_visible_balance_cleanup_result_v1.json` from the same
`MIGRATION_ARTIFACT_ROOT`. To inspect a previous cleanup run, pass
`BUSINESS_FACT_CLEANUP_RESULT_JSON=/path/to/business_fact_visible_balance_cleanup_result_v1.json`
explicitly.
