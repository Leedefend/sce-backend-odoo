# Partner Import Source Alignment Audit v1

Status: Evidence batch
Branch: `feature/user-history-data-alignment`
Source root: `/home/odoo/workspace/partner_import_source`
Current payload: `artifacts/migration/fresh_db_partner_l4_replay_payload_v1.csv`

## Conclusion

The current partner replay payload is not aligned with the user's current source
snapshot. The source is not a pure customer list or a pure supplier list: it is a
mixed counterparty register assembled from supplier registry files, expense-unit
registry files, and counterparty cash-flow files.

The current payload also loses basic entity information. It only carries
identity and role fields such as `legacy_partner_source`, `legacy_partner_id`,
`name`, `tax_no`, `source_type`, and replay metadata. It does not carry bank
account, bank name, project source, cooperation type, region, address, or tax
rate evidence from the Excel source.

## Evidence

Generated with:

```bash
python3 scripts/migration/partner_import_source_audit.py
```

Artifacts:

- `artifacts/migration/partner_import_source_audit_v1/summary_v1.json`
- `artifacts/migration/partner_import_source_audit_v1/source_rows_v1.csv`
- `artifacts/migration/partner_import_source_audit_v1/source_entities_v1.csv`
- `artifacts/migration/partner_import_source_audit_v1/source_payload_gap_samples_v1.csv`

Normalized no-DB asset generated with:

```bash
python3 scripts/migration/partner_import_source_asset_build.py
```

Asset artifacts:

- `artifacts/migration/partner_import_source_asset_v1/partner_master_source_v1.csv`
- `artifacts/migration/partner_import_source_asset_v1/partner_master_review_queue_v1.csv`
- `artifacts/migration/partner_import_source_asset_v1/partner_master_source_summary_v1.json`

## Source Shape

| Metric | Value |
| --- | ---: |
| source rows | 12,272 |
| source entities | 7,792 |
| counterparty-flow rows | 5,812 |
| supplier-registry rows | 6,254 |
| expense-unit registry rows | 206 |
| entities with tax number | 2,253 |
| entities without tax number | 5,539 |
| personal/name fragments | 705 |

Role evidence split:

| Target role from source evidence | Entities |
| --- | ---: |
| supplier | 7,083 |
| customer and supplier | 51 |
| customer | 13 |
| unknown | 645 |

The role split is evidence-based, not final business approval. It proves the
source must be normalized as mixed counterparty data before any write.

## Current Payload Gap

| Metric | Value |
| --- | ---: |
| current payload rows | 6,541 |
| current payload `cooperat_company` rows | 3,899 |
| current payload `company_supplier` rows | 2,642 |
| source names missing in payload | 1,399 |
| source tax numbers missing in payload | 410 |
| payload names missing in source | 1,382 |
| payload tax numbers missing in source | 1,785 |
| source/payload name overlap | 4,584 |
| source/payload tax overlap | 1,843 |

Basic-info schema gap:

| Field family | Present in source | Present in current payload |
| --- | --- | --- |
| bank name / bank account | yes | no |
| project source | yes | no |
| cooperation type / main supply type | yes | no |
| region / address | partial | no |
| tax rate | yes | no |

Source completeness counts:

| Source evidence | Entity count |
| --- | ---: |
| entities with bank account | 6,602 |
| entities with bank name | 6,606 |
| entities with region | 791 |
| entities with address | 8 |
| entities with business scope | 0 |

## Normalized Asset Output

The first normalized asset is no-DB and does not write Odoo. It preserves the
source evidence that the old payload did not carry.

| Asset status | Rows |
| --- | ---: |
| loadable | 2,253 |
| missing-tax review | 4,245 |
| unknown-role review | 645 |
| personal-fragment review | 598 |
| mixed-role review | 51 |

The asset contains 7,792 rows, including 6,602 rows with bank account evidence
and 6,606 rows with bank name evidence. Review rows are intentionally separated
into `partner_master_review_queue_v1.csv` so the loader can later apply a narrow
write policy instead of silently importing ambiguous identities.

## Design Implication

The next iteration should not patch `customer_rank` and `supplier_rank` directly
from the old replay payload. It should first build a normalized partner source
asset from `/home/odoo/workspace/partner_import_source` with explicit evidence:

- stable identity: tax number when valid, otherwise normalized name plus source
  provenance;
- role evidence: supplier registry, payment amount, receipt amount, expense-unit
  tags, and project source;
- basic info: bank name, bank account, account holder, tax rate, region,
  address, cooperation type, and source file/row;
- conflict status: loadable, mixed-role, missing-tax, personal-fragment,
  duplicate-name, and unknown-role.

Only after that asset is reviewed should a loader update `res.partner` and, where
appropriate, create `res.partner.bank` records. This keeps the partner entity
contract separate from cash-flow facts and avoids silently losing user-provided
basic information.
