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

Read-only acceptance postcheck:

```bash
BUSINESS_FACT_REPLAY_MODE=postcheck \
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

Decision marker:

`business_fact_replay_acceptance_passed`
