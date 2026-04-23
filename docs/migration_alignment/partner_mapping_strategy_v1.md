# Partner mapping strategy v1

Status: L1 DRY-RUN PASS  
Iteration: `ITER-2026-04-14-0028`

This document defines the first full-rebuild partner importer mapping shape.
The batch is no-DB and does not authorize partner writes.

## Inputs

| Source | Role | Rows |
| --- | --- | ---: |
| `tmp/raw/partner/company.csv` | primary partner source | 7864 |
| `tmp/raw/partner/supplier.csv` | supplier supplemental source | 3041 |

## Unified Shape

| Field | Company source | Supplier source |
| --- | --- | --- |
| `legacy_partner_id` | `Id` | `ID` |
| `partner_name` | `DWMC` | `f_SupplierName` |
| `tax_number` | `SH`, fallback `TYSHXYDM` | `SH`, fallback `SHXYDM`, `NSRSBH`, `TISHXYDM` |
| `phone` | `YWLXRHM` | `f_Phone` |
| `email` | `YWLXRYX` | `f_Email` |
| `supplier_flag` | derived from source role evidence | `true` |
| `customer_flag` | `true` | `false` |

## Dry-Run Result

| Item | Result |
| --- | ---: |
| primary total | 7864 |
| supplier source rows | 3041 |
| combined source rows | 10905 |
| deduplicated partner groups | 7172 |
| create-ready groups | 7037 |
| duplicate groups to merge | 3186 |
| conflict groups | 135 |
| safe slice rows | 100 |

## Safe Slice

`artifacts/migration/partner_safe_slice_v1.csv` contains 100 no-DB candidate
rows selected for L2 review.

Safe slice requirements:

- no duplicate group
- no conflicts
- `legacy_partner_id` present
- `partner_name` present
- `tax_number` present

## Boundary

This batch remains L1 dry-run. It does not create, update, merge, or unlink any
`res.partner` record. Any L3 bounded write requires a new task and explicit
write authorization.
