# History Contract Strong Evidence Backtrace Report v1

## Scope

This report backtraces the remaining blocked contract-header rows to the
original full-rebuild analysis assets instead of treating the current
23-package continuity delivery assets as the source of truth.

Source inputs:

- `artifacts/migration/history_contract_partner_gap_rows_v1.csv`
- `artifacts/migration/contract_counterparty_strong_evidence_candidates_v1.csv`

Generated artifacts:

- `artifacts/migration/history_contract_strong_evidence_backtrace_audit_v1.json`
- `artifacts/migration/history_contract_strong_evidence_backtrace_rows_v1.csv`

## Frozen Result

Current blocked contract-header rows remain:

- total blocked rows: `35`

They are now frozen into three distinct recovery families:

1. `partner_master_replay_gap_4`
   - already present in `partner_master_v1`
   - this is an anchor/delivery coverage gap

2. `strong_evidence_backtrace_19`
   - not present in current continuity delivery assets
   - but fully present in original
     `contract_counterparty_strong_evidence_candidates_v1.csv`

3. `direction_defer_blank_counterparty_12`
   - no valid current counterparty text
   - still blocked at direction/source interpretation level

## Strong-Evidence Backtrace Facts

For the `19` rows in `strong_evidence_backtrace_19`:

- matched rows: `19 / 19`
- evidence type:
  - `repayment_single_counterparty = 19`
- evidence strength:
  - `strong = 19`
- manual confirmation:
  - `manual_confirm_required = yes` for all `19`
- confirmed partner action:
  - still empty for all `19`

This means these rows are **not source-missing**. They already went through the
original full-rebuild business analysis and were retained as strong-evidence
partner candidates awaiting confirmation/promotion.

## Interpretation

The previous shorthand statement:

- "missing in current 23-package continuity assets"

must not be interpreted as:

- "missing in original rebuild analysis"

For the `19` rows, the correct interpretation is:

- original analysis exists,
- strong evidence exists,
- but the candidate/promotion result was not yet carried into current
  continuity delivery assets.

## Recovery Decision

`UR-B` must now be split into three explicit tracks:

1. `UR-B.1 partner_master_replay_gap_4`
2. `UR-B.2 strong_evidence_promotion_gap_19`
3. `UR-B.3 direction_defer_blank_counterparty_12`

No downstream replay should treat these three families as a single partner gap.
