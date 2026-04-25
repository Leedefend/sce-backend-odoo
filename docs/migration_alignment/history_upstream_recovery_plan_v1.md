# History Upstream Recovery Plan v1

Status: ACTIVE

Task: `ITER-2026-04-24-HISTORY-UPSTREAM-RECOVERY-001`

## Goal

Freeze the upstream recovery plan required before continuing Group B historical
business fact replay into `sc_demo`.

The target is not merely to load more packages. The target is:

- historical data enters the new system through the same staged rebuild logic;
- upstream anchor and header coverage is complete enough to support downstream
  business fact replay;
- continuity replay follows the original rebuild pipeline instead of bypassing it.

## Original Rebuild Process (Frozen)

The original rebuild process is not a single importer. It is a staged ladder:

```text
source probe
-> asset generate / verify
-> adapter payload
-> replay precheck
-> bounded replay write
-> carrier/promote
-> business usable surface
```

References:

- `docs/migration_alignment/fresh_db_operation_contract_v1.md`
- `docs/migration_alignment/full_rebuild_migration_blueprint_v1.md`
- `docs/migration_alignment/full_rebuild_importer_promotion_standard_v1.md`
- `artifacts/migration/fresh_db_replay_manifest_v1.json`

## Current Group B Blockers

### 1. Contract Core Coverage Gap

Observed fact:

- `contract_line_sc_v1` replay is blocked by missing parent `construction.contract`
  rows in current `sc_demo`.
- Representative missing parent:
  - `legacy_contract_id = 002cc1eac1a54e889f7c28531ab6553f`
- This parent exists in `migration_assets/20_business/contract/contract_header_v1.xml`
  but is absent from current replayed `construction.contract`.

Interpretation:

- current `contract_sc_v1` continuity replay is not full coverage;
- downstream `contract_line_sc_v1` must not proceed until contract header replay
  coverage is reconciled.

### 2. General/Supplier Partner Anchor Gap

Observed fact:

- `supplier_contract_sc_v1` replay is blocked by missing upstream partner anchors.
- Representative missing partner:
  - `legacy_partner_id = a4d55ad0464b43dab4f89d8ed06b5bed`
- This id is not present in current loaded:
  - `partner_sc_v1`
  - `contract_counterparty_partner_sc_v1`
  - `receipt_counterparty_partner_sc_v1`

Interpretation:

- supplier contract replay depends on a broader partner anchor surface than the
  currently loaded counterparty supplements;
- partner upstream recovery must happen before supplier business replay.

## Recovery Batches

### Batch-UR-A Contract Core Recovery

Target:

- reconcile why `contract_sc_v1` currently replayed only a subset required by
  downstream `contract_line_sc_v1`.

Actions:

1. classify `contract_header_v1.xml` rows into:
   - already replayed into `sc_demo`
   - missing from `sc_demo`
   - intentionally excluded
2. compare with `fresh_db_contract_remaining_write.py` source and bounded scope
3. identify whether missing rows require:
   - a new adapter/recovery lane, or
   - widening current contract replay contract

Acceptance:

- a machine-readable missing-contract coverage report exists;
- one explicit recovery decision exists for the missing header set.

### Batch-UR-A Execution Result (Frozen)

Read-only audit result:

- asset package rows: `1492`
- bounded historical payload rows: `1332`
- special 12-row payload rows: `12`
- bounded payload union: `1344`
- retry lane rows: `57`
- bounded + retry historical coverage: `1401`
- asset rows never entering any replay payload: `91`

Runtime probe against `sc_demo`:

- bounded payload rows present: `1332 / 1344`
- bounded payload rows missing: `12`
- retry lane rows present: `0 / 57`

Interpretation:

- current `sc_demo` has replayed only the main `1332` contract header lane;
- the special `12-row` slice has not been replayed into `sc_demo`;
- the `57 retry` lane has not been replayed into `sc_demo`;
- even if both are replayed, `91` asset rows still remain outside any known
  replay lane.

Frozen recovery decomposition:

1. `special_slice_gap_12`
2. `retry_lane_gap_57`
3. `never_reached_asset_gap_91`

Artifacts:

- `artifacts/migration/history_contract_core_gap_audit_v1.json`
- `artifacts/migration/ur_a_contract_unreached_asset_rows_v1.csv`
- `docs/migration_alignment/history_contract_core_gap_report_v1.md`

### Batch-UR-A.1 Execution Result (sc_demo)

Executed recovery lanes:

- `contract_12_row_missing_partner_anchor_write`
- `contract_12_row_create_only_write`
- `fresh_db_contract_57_retry_write`

Live result on `sc_demo`:

- bounded payload rows present: `1344 / 1344`
- retry lane rows present: `57 / 57`
- effective contract header runtime coverage: `1401 / 1492`
- remaining upstream contract gap: `91`

Interpretation:

- `special_slice_gap_12` is closed
- `retry_lane_gap_57` is closed
- `never_reached_asset_gap_91` remains the only contract-core gap

Operational implication:

- `history.continuity.replay` default path must now include:
  - `contract_12_row_missing_partner_anchor_write`
  - `contract_12_row_create_only_write`
  - `fresh_db_contract_57_retry_write`
- blocked Group B lanes remain opt-in only until the `91` upstream contract
  gap is resolved

### Batch-UR-A.2 Execution Result (sc_demo)

Executed recovery lane:

- `history_contract_unreached_ready_replay_adapter`
- `history_contract_unreached_ready_replay_write`

Live result on `sc_demo`:

- ready unreached replay rows: `56 / 56`
- effective contract header runtime coverage: `1457 / 1492`
- remaining blocked unreached rows: `35`
- continuity probe: `PASS`

Interpretation:

- the `91` never-reached asset rows are no longer a single bucket;
- `56` are now recovered into runtime;
- the remaining contract-core upstream gap is reduced to `35`, all of which
  require upstream partner/direction recovery rather than direct replay.

Operational implication:

- `history.continuity.replay` default path must now include:
  - `history_contract_unreached_ready_replay_adapter.py`
  - `history_contract_unreached_ready_replay_write.py`
- blocked Group B lanes remain opt-in only until the remaining `35` blocked
  rows are reclassified and recovered.

### Batch-UR-B General Partner Recovery

Target:

- identify the upstream source of supplier/general partners required by
  `supplier_contract_sc_v1`.

Actions:

1. compare supplier contract partner ids against:
   - `partner_sc_v1`
   - `contract_counterparty_partner_sc_v1`
   - `receipt_counterparty_partner_sc_v1`
2. classify partner ids into:
   - already covered
   - recoverable from existing partner source packages
   - requiring a dedicated supplemental partner lane
3. freeze the canonical partner recovery source for supplier continuity

Acceptance:

- a machine-readable supplier-partner gap report exists;
- one explicit upstream lane decision exists for supplier/general partner anchors.

### Batch-UR-B Contract Partner Gap Audit Result

Read-only audit result:

- blocked rows after `UR-A.2`: `35`
- partner source buckets:
  - `partner_master_recoverable = 4`
  - `no_asset_source_in_current_packages = 31`
- direction buckets:
  - `both_blank = 3`
  - `both_non_own = 3`
  - `fbf_only_non_own = 5`
  - `mixed_own_non_own = 1`

Interpretation:

- only `4` blocked rows are replay/anchor coverage gaps inside the current
  partner master asset;
- the remaining `31` rows are upstream source gaps and do not exist in the
  current 23-package partner/counterparty assets;
- `direction_defer` rows require a dedicated recovery lane and must not be
  merged into the generic partner recovery lane.

### Batch-UR-B Strong-Evidence Backtrace Result

Read-only backtrace result:

- blocked rows total: `35`
- split now freezes as:
  - `partner_master_replay_gap_4`
  - `strong_evidence_backtrace_19`
  - `direction_defer_blank_counterparty_12`

Backtrace result for the `19` rows:

- `19 / 19` matched inside
  `artifacts/migration/contract_counterparty_strong_evidence_candidates_v1.csv`
- all matched rows are:
  - `evidence_type = repayment_single_counterparty`
  - `evidence_strength = strong`
  - `manual_confirm_required = yes`
  - `confirmed_partner_action = <empty>`

Interpretation:

- these `19` rows are not source-missing;
- they already belong to the original full-rebuild business-analysis result;
- the real gap is not source discovery but candidate confirmation / promotion
  back into continuity delivery assets.

Frozen next split:

1. `UR-B.1 partner_master_replay_gap_4`
2. `UR-B.2 strong_evidence_promotion_gap_19`
3. `UR-B.3 direction_defer_blank_counterparty_12`

Artifacts:

- `artifacts/migration/history_contract_partner_gap_audit_v1.json`
- `artifacts/migration/history_contract_partner_gap_rows_v1.csv`
- `docs/migration_alignment/history_contract_partner_gap_report_v1.md`
- `artifacts/migration/history_contract_strong_evidence_backtrace_audit_v1.json`
- `artifacts/migration/history_contract_strong_evidence_backtrace_rows_v1.csv`
- `docs/migration_alignment/history_contract_strong_evidence_backtrace_report_v1.md`

### Batch-UR-B.1 + Batch-UR-B.2 Execution Result (sc_demo)

Executed recovery lanes:

- `history_partner_master_targeted_replay_adapter`
- `history_partner_master_targeted_replay_write`
- `history_contract_partner_recovery_adapter`
- `history_contract_partner_recovery_write`

Live result on `sc_demo`:

- targeted partner-master backfill: `4 / 4`
- partner-recovered contract headers: `23 / 23`
- effective contract header runtime coverage: `1480 / 1492`
- remaining blocked rows: `12`
- continuity probe: `PASS`

Interpretation:

- `UR-B.1 partner_master_replay_gap_4` is closed;
- `UR-B.2 strong_evidence_promotion_gap_19` is closed;
- the only remaining upstream contract blocker family is now:
  - `UR-B.3 direction_defer_blank_counterparty_12`

### Batch-UR-B.3 Execution Result (sc_demo)

Executed dedicated direction-defer lanes:

- `history_partner_master_direction_defer_replay_adapter`
- `history_partner_master_direction_defer_replay_write`
- `history_contract_direction_defer_recovery_adapter`
- `history_contract_direction_defer_recovery_write`

Live result on `sc_demo`:

- direction-defer partner targeted replay: `PASS`
  - `input_rows = 12`
  - `created_rows = 2`
  - `skipped_existing = 10`
- direction-defer contract recovery replay: `PASS`
  - `created_rows = 12`
- continuity probe: `PASS`
- effective contract header runtime coverage: `1492 / 1492`

Interpretation:

- `UR-B.3 direction_defer_blank_counterparty_12` is closed;
- the remaining `12` rows were not source-missing, they were recoverable from
  the original `repayment_single_counterparty` strong-evidence analysis once a
  dedicated lane was introduced;
- `contract_sc_v1` contract-header continuity coverage is now complete.

Operational implication:

- `history.continuity.replay` default path must now also include:
  - `history_partner_master_direction_defer_replay_adapter.py`
  - `history_partner_master_direction_defer_replay_write.py`
  - `history_contract_direction_defer_recovery_adapter.py`
  - `history_contract_direction_defer_recovery_write.py`

Operational implication:

- `history.continuity.replay` default path must now include:
  - `history_partner_master_targeted_replay_adapter.py`
  - `history_partner_master_targeted_replay_write.py`
  - `history_contract_partner_recovery_adapter.py`
  - `history_contract_partner_recovery_write.py`

### Batch-UR-C Resume Group B

Only after Batch-UR-A and Batch-UR-B pass:

- retry `supplier_contract_sc_v1`
- retry `supplier_contract_line_sc_v1`
- retry `contract_line_sc_v1`

Only after these pass:

- continue to payment-side Group B packages:
  - `outflow_request_sc_v1`
  - `actual_outflow_sc_v1`
  - `outflow_request_line_sc_v1`
  - `receipt_invoice_line_sc_v1`

## Stop Rule

Do not continue Group B downstream replay while either of these remains true:

- parent contract header coverage is incomplete;
- supplier/general partner anchor source is unresolved.

## Server Replay Implication

The one-click server replay contract must continue to reflect reality:

- loaded packages may be included in default continuity replay;
- blocked packages must remain blocked with explicit reason;
- no package may be marked replay-ready merely because its adapter exists.
