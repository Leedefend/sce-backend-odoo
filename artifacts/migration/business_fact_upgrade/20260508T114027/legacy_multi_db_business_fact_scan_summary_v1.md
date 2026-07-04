# Legacy Multi DB Business Fact Scan Summary v1

Status: PASS

## Sources

```json
[
  {
    "label": "main",
    "container": "legacy-mssql-restore",
    "database": "LegacyDb",
    "artifact_root": "artifacts/migration/business_fact_upgrade/20260508T114027",
    "full_scan_status": "PASS",
    "remaining_family_status": "PASS",
    "non_empty_tables": 1128,
    "candidate_tables": 347,
    "candidate_rows": 79525,
    "top_candidate": "YSZJ_CZBS_CZQDBS",
    "screened_tables": 78,
    "screened_rows": 10479,
    "screened_active_rows": 10438,
    "top_family": "labor_subcontract"
  },
  {
    "label": "scbs",
    "container": "legacy-mssql-scbs",
    "database": "LegacyScbs20260417",
    "artifact_root": "artifacts/migration/business_fact_upgrade/20260508T114027/scbs",
    "full_scan_status": "PASS",
    "remaining_family_status": "PASS",
    "non_empty_tables": 710,
    "candidate_tables": 290,
    "candidate_rows": 23733,
    "top_candidate": "D_SMWZ_WZ_XSHTFB_XSHTFB_XSHTFB",
    "screened_tables": 76,
    "screened_rows": 11527,
    "screened_active_rows": 11484,
    "top_family": "lease_equipment"
  }
]
```

## Totals

```json
{
  "source_count": 2,
  "non_empty_tables": 1838,
  "candidate_tables": 637,
  "candidate_rows": 103258,
  "screened_tables": 154,
  "screened_rows": 22006,
  "screened_active_rows": 21922
}
```

## Errors

```json
[]
```

## Decision

`legacy_multi_db_business_fact_sources_screened`
