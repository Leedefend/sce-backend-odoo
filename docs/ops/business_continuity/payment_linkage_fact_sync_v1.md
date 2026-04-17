# Payment Linkage Fact Sync v1

## Scope
- Database: `sc_demo`
- Batch: `ITER-2026-04-17-PAYMENT-LINKAGE-FACT-SYNC`
- Mode: high-risk deterministic business-fact write
- Target: `payment.request.company_id` and `payment.request.contract_id`

## Rules Applied
- Existing `contract_id` -> copy `company_id` from linked contract.
- Missing `contract_id` -> use the only matching contract where:
  - same `project_id`
  - same `partner_id`
  - payment `type=pay` maps to contract `type=in`
  - payment `type=receive` maps to contract `type=out`
  - exactly one contract matches
- Ambiguous and no-candidate records were excluded.
- No amount/name/text similarity inference was used.

## Write Result
- Candidate rows: 12108
- Company updates needed: 12108
- Contract updates needed: 10305
- Updated `company_id`: 12108
- Updated `contract_id`: 10305

## Post-Check
- Payment requests total: 30102
- Company linked after sync: 12108
- Contract linked after sync: 12108
- Missing company after sync: 17994
- Missing contract after sync: 17994
- Company/contract mismatch after sync: 0

## Artifacts
- Snapshot: `artifacts/migration/payment_linkage_fact_sync_snapshot_v1.csv`
- Rollback: `artifacts/migration/payment_linkage_fact_sync_rollback_v1.csv`
- Result: `artifacts/migration/payment_linkage_fact_sync_result_v1.json`

## Risk Boundary
- No ledger records were changed.
- No settlement records were changed.
- No accounting records were changed.
- No approval workflow was triggered.
- No ambiguous contract candidate was selected.

## Result
PASS.

The deterministic payment linkage slice is now aligned. Remaining payment records require stronger source facts because they either have multiple possible contracts or no contract candidate.
