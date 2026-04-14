# Full Migration Scope Freeze v1

## Scope

- Task: `ITER-2026-04-14-0006`
- Mode: no-DB governance scope freeze
- Request: `开启完整数据迁移动作`

## Current Materialized State

- Project rows created: 130
- Partner rows created: 30
- Contract rows created: 12
- Contract post-write review: `ROLLBACK_READY`

## Raw Source Counts

- Project: 755
- Partner company: 7864
- Partner supplier: 3041
- Contract: 1694
- Project member: 21390
- Payment: 13646
- Receipt: 7412

## Execution Lanes

- `project_expand`: next safe lane, bounded create-only expansion dry-run
- `partner_company_expand`: bounded company-primary dry-run after project lane
- `partner_supplier_supplement`: supplemental-only, no company-primary override
- `contract_expand`: depends on broader project and partner anchors
- `project_member`: screening only unless user/permission semantics are frozen
- `payment`: STOP, dedicated financial/payment task line required
- `receipt`: STOP, dedicated financial/receipt task line required

## Decision

Full migration is opened as a controlled batch chain, not a monolithic write.

The next safe batch is `project_expand` bounded create-only dry-run. Financial
lanes and permission-sensitive lanes remain blocked until a dedicated task line
and explicit authorization exist.
