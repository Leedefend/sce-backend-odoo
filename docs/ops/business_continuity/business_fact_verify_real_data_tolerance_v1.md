# Business Fact Verify Real Data Tolerance v1

## Purpose

Payment and settlement verification guards must run in real customer business
data environments. Demo showroom fixture absence is an environment baseline
condition, not a payment or settlement consistency failure.

## Classification

- `PASS`: configured target projects exist and all checked business facts match.
- `FAIL`: a found project has real consistency or evidence mismatches.
- `SKIP_ENV`: configured demo projects are missing, with no real mismatch found.

## Guard Scope

- `scripts/verify/payment_fact_consistency_guard.sh`
- `scripts/verify/settlement_evidence_guard.sh`

## Boundary

- No demo data is fabricated.
- No payment, settlement, account, ACL, manifest, frontend, or migration
  semantics are changed.
- Existing mismatch checks remain blocking failures.

## Verification

Run:

```bash
DB_NAME=sc_demo make verify.payment_fact_consistency.v1
DB_NAME=sc_demo make verify.settlement_evidence_guard
```

The generated artifacts remain under `/mnt/artifacts/backend/` and include the
final `status` plus any missing demo project list.
