# Legacy DB Full Business Fact Loss Scan v1

Status: `PASS`

Source: `legacy-mssql-restore:LegacyDb`

## Summary

```json
{
  "total_tables": 4312,
  "non_empty_tables": 1128,
  "candidate_tables": 0,
  "candidate_rows": 0,
  "classification_counts": {
    "known_replayed_or_assetized": 498,
    "system_or_audit_noise": 362,
    "reference_or_import_catalog": 489,
    "low_business_fact_signal": 2963
  },
  "classification_row_counts": {
    "known_replayed_or_assetized": 3795228,
    "system_or_audit_noise": 1245813,
    "reference_or_import_catalog": 2518257,
    "low_business_fact_signal": 19746
  },
  "top_candidate_families": [],
  "top_candidates": []
}
```

## Top Candidate Tables

| Table | Rows | Classification | Score | Signals |
|---|---:|---|---:|---|


## Top Candidate Families

| Family | Tables | Rows | Effective Tables | Top Tables |
|---|---:|---:|---:|---|


## Boundary

- Read-only legacy DB scan
- DB writes: `0`
- This is a table/column signal screen; every candidate still needs lane-level SQL and replay mapping before ingestion.
