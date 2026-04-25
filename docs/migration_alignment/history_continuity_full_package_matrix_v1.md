# History Continuity Full Package Matrix v1

Status: FULL_PACKAGE_REPLAY_READY

Task: `ITER-2026-04-24-HISTORY-CONTINUITY-FULL-PACKAGE-MATRIX-001`

## Scope

This document expands the continuity scope from the current core baseline to the
full 23-package migration asset bus.

The target is no longer:

- only replaying a few lanes into `sc_demo`

The target is now:

- all 23 historical asset packages must be accounted for;
- each package must have a continuity classification;
- only after all packages are loaded or explicitly deferred with frozen reason
  may the next business-availability batch begin.

## Current Core Continuity Baseline

Already replayed into `sc_demo`:

1. `user_sc_v1`
2. `partner_sc_v1`
3. `project_sc_v1`
4. `project_member_sc_v1`
5. `contract_sc_v1`
6. `receipt_sc_v1`
7. `contract_counterparty_partner_sc_v1`
8. `receipt_counterparty_partner_sc_v1`

Current runtime/carrier counts:

- `legacy_users = 101`
- `partner_l4_anchors = 4797`
- `contract_counterparty_partners = 88`
- `receipt_counterparty_partners = 250`
- `project_anchors = 755`
- `project_member_carrier = 7389`
- `contract_headers = 1492` (`contract_sc_v1` current runtime coverage is now complete, including the 12-row special slice, 57-retry lane, 56 ready unreached rows, 23 partner-recovered rows, and 12 direction-defer strong-evidence rows)
- `receipt_core_requests = 1683`

## Full 23-Package Order

| # | Package | Layer | Target Model | Current Continuity Status |
| --- | --- | --- | --- | --- |
| 01 | `project_sc_v1` | `10_master` | `project.project` | `loaded_core` |
| 02 | `partner_sc_v1` | `10_master` | `res.partner` | `loaded_core` |
| 03 | `contract_counterparty_partner_sc_v1` | `10_master` | `res.partner` | `loaded_group_a` |
| 04 | `receipt_counterparty_partner_sc_v1` | `10_master` | `res.partner` | `loaded_group_a` |
| 05 | `user_sc_v1` | `10_master` | `res.users` | `loaded_core` |
| 06 | `project_member_sc_v1` | `30_relation` | `sc.project.member.staging` | `loaded_core` |
| 07 | `contract_sc_v1` | `20_business` | `construction.contract` | `loaded_core_1492_of_1492` |
| 08 | `contract_line_sc_v1` | `20_business` | `construction.contract.line` | `loaded_full_package` |
| 09 | `receipt_sc_v1` | `20_business` | `payment.request` | `loaded_core` |
| 10 | `outflow_request_sc_v1` | `20_business` | `payment.request` | `loaded_full_package` |
| 11 | `actual_outflow_sc_v1` | `20_business` | `payment.request` | `loaded_full_package` |
| 12 | `supplier_contract_sc_v1` | `20_business` | `construction.contract` | `loaded_full_package` |
| 13 | `supplier_contract_line_sc_v1` | `20_business` | `construction.contract.line` | `loaded_full_package` |
| 14 | `outflow_request_line_sc_v1` | `20_business` | `payment.request.line` | `loaded_full_package` |
| 15 | `receipt_invoice_line_sc_v1` | `20_business` | `payment.request.line` | `loaded_full_package` |
| 16 | `receipt_invoice_attachment_sc_v1` | `30_relation` | `ir.attachment` / relation carrier | `loaded_full_package` |
| 17 | `legacy_attachment_backfill_sc_v1` | `30_relation` | attachment/relation carrier | `loaded_full_package` |
| 18 | `legacy_expense_deposit_sc_v1` | `30_relation` | relation carrier | `loaded_full_package` |
| 19 | `legacy_invoice_tax_sc_v1` | `30_relation` | relation carrier | `loaded_full_package` |
| 20 | `legacy_receipt_income_sc_v1` | `30_relation` | relation carrier | `loaded_full_package` |
| 21 | `legacy_financing_loan_sc_v1` | `30_relation` | relation carrier | `loaded_full_package` |
| 22 | `legacy_fund_daily_snapshot_sc_v1` | `30_relation` | relation carrier | `loaded_full_package` |
| 23 | `legacy_workflow_audit_sc_v1` | `30_relation` | relation/audit carrier | `loaded_full_package` |

## Final Coverage Snapshot

- `contract_sc_v1`: `1492 / 1492`
- `outflow_request_sc_v1`: `12284 / 12284`
- `actual_outflow_sc_v1`: `12463 / 12463`
- `outflow_request_line_sc_v1`: `15917 / 15917`
- `receipt_invoice_line_sc_v1`: `4454 / 4454`
- `receipt_invoice_attachment_sc_v1`: `1079 / 1079`
- `legacy_attachment_backfill_sc_v1`: `18458 / 18458`
- `legacy_receipt_income_sc_v1`: `7220 / 7220`
- `legacy_expense_deposit_sc_v1`: `11167 / 11167`
- `legacy_invoice_tax_sc_v1`: `5920 / 5920`
- `legacy_financing_loan_sc_v1`: `318 / 318`
- `legacy_fund_daily_snapshot_sc_v1`: `496 / 496`
- `legacy_workflow_audit_sc_v1`: `79702 / 79702`
- `DB_NAME=sc_demo make history.continuity.rehearse`: `PASS`

## Grouping For Next Batches

### Group A: Missing Master Anchors

Packages:

- `contract_counterparty_partner_sc_v1`
- `receipt_counterparty_partner_sc_v1`

Reason:

- these are still master-anchor packages and should be loaded before more
  downstream business facts.

Current result:

- `contract_counterparty_partner_sc_v1`: loaded into `sc_demo` (`88`)
- `receipt_counterparty_partner_sc_v1`: loaded into `sc_demo` (`250`)

### Group B: Missing Business Header/Line Facts

Packages:

- `contract_line_sc_v1`
- `outflow_request_sc_v1`
- `actual_outflow_sc_v1`
- `supplier_contract_sc_v1`
- `supplier_contract_line_sc_v1`
- `outflow_request_line_sc_v1`
- `receipt_invoice_line_sc_v1`

Reason:

- these directly affect whether historical business can continue inside new
  list/form surfaces.

Current checkpoint:

- `contract_line_sc_v1`
  - adapter PASS
  - replay blocked because parent `legacy_contract_sc_*` headers are not fully present in current `sc_demo`
  - representative blocker:
    - `legacy_contract_id = 002cc1eac1a54e889f7c28531ab6553f`
    - present in `contract_header_v1.xml`
    - absent from current `sc_demo`
- `supplier_contract_sc_v1`
  - adapter PASS
  - replay blocked because referenced `legacy_partner_sc_*` partner anchors are not present in current `sc_demo`
  - representative blocker:
    - `legacy_partner_id = a4d55ad0464b43dab4f89d8ed06b5bed`
    - absent from current `partner_sc_v1` / counterparty replay payloads already loaded into `sc_demo`
- `supplier_contract_line_sc_v1`
  - adapter PASS
  - replay blocked because parent supplier contract header is not yet loaded

Upstream freeze after `Batch-UR-B.3`:

- `contract_sc_v1` asset rows: `1492`
- bounded historical main lane loaded in `sc_demo`: `1332`
- special bounded slice loaded: `12`
- retry lane loaded: `57`
- ready unreached recovery lane loaded: `56`
- partner-driven recovery lane loaded: `23`
- current effective runtime coverage: `1492`
- remaining blocked direction-defer rows: `0`

### Group C: Missing Relation/Carrier Packages

Packages:

- `receipt_invoice_attachment_sc_v1`
- `legacy_attachment_backfill_sc_v1`
- `legacy_expense_deposit_sc_v1`
- `legacy_invoice_tax_sc_v1`
- `legacy_receipt_income_sc_v1`
- `legacy_financing_loan_sc_v1`
- `legacy_fund_daily_snapshot_sc_v1`
- `legacy_workflow_audit_sc_v1`

Reason:

- these do not all have to become runtime business actions immediately, but
  they must still enter the new system before continuity can be called complete.

## Enforcement Rule

The continuity program may not declare `history continuity complete` until:

1. all 23 packages are either:
   - loaded, or
   - explicitly frozen as deferred with a signed reason;
2. the package matrix is updated after every batch;
3. the one-click replay contract reflects the same package coverage.

## Next Batch

`Batch-History-Continuity-Promotion`

Goal:

- replay baseline is complete;
- next work should focus on promotion/business usability, not asset ingress.
