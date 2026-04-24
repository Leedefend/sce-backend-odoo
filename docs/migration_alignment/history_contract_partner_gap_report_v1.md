# History Contract Partner Gap Report v1

## Scope

This report freezes the remaining blocked contract-header set after `Batch-UR-A.2`.

Source inputs:

- `artifacts/migration/history_contract_unreached_reason_rows_v1.csv`
- `tmp/raw/contract/contract.csv`
- `migration_assets/10_master/partner/partner_master_v1.xml`
- `migration_assets/10_master/contract_counterparty_partner/contract_counterparty_partner_master_v1.xml`
- `migration_assets/10_master/receipt_counterparty_partner/receipt_counterparty_partner_master_v1.xml`

Generated artifacts:

- `artifacts/migration/history_contract_partner_gap_audit_v1.json`
- `artifacts/migration/history_contract_partner_gap_rows_v1.csv`

## Frozen Result

- blocked contract-header rows after `UR-A.2`: `35`
- partner-source buckets:
  - `partner_master_recoverable = 4`
  - `no_asset_source_in_current_packages = 31`
- direction buckets:
  - `both_blank = 3`
  - `both_non_own = 3`
  - `fbf_only_non_own = 5`
  - `mixed_own_non_own = 1`

## Interpretation

### 1. A small recoverable subset already exists in current partner master assets

The following counterparties are present in `partner_master_v1` and should be
treated as replay/anchor coverage gaps rather than source gaps:

- `渝北区石船镇人民政府` (`2` rows)
- `中石油煤层气有限责任公司` (`1` row)
- `成都市龙泉驿区第六中学` (`1` row)

This gives `4` rows that can be addressed by a focused partner-anchor recovery
lane without reopening full upstream source generation.

### 2. Most blocked rows do not exist in current 23-package partner assets

The remaining `31` blocked rows have no match in:

- `partner_master_v1`
- `contract_counterparty_partner_master_v1`
- `receipt_counterparty_partner_master_v1`

These rows are **not** replay gaps. They are upstream source/asset gaps and
must not be solved by guessing partner anchors inside downstream writers.

### 3. Direction-defer rows are a separate class

`12` rows still carry `direction_defer`, and their shapes are mixed:

- both contracting parties blank
- both parties non-own
- only `FBF` present and non-own
- mixed own/non-own company variants

These rows should not be merged into the same recovery lane as the
partner-master replay subset.

## Recovery Decision

The next recovery work must split into two bounded tracks:

1. `UR-B.1 partner_master_replay_gap_4`
   - recover the `4` rows whose counterparties already exist in
     `partner_master_v1`
   - goal: close the small anchor coverage gap first

2. `UR-B.2 source_probe_gap_31`
   - re-open upstream source analysis for the `31` rows with no source in the
     current 23-package assets
   - do not fabricate partner anchors from downstream contract data

`direction_defer` rows remain blocked until an explicit direction policy is
frozen.
