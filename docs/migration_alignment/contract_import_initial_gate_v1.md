# Contract Import Initial Gate v1

Iteration: `ITER-2026-04-13-1838`

Decision: `NO-GO for direct import`

Recommended next state: `CONTRACT_MAPPING_DRY_RUN_REQUIRED`

## Gate Result

Direct import of `tmp/raw/contract/contract.csv` is not allowed yet.

This batch only authorizes the next low-risk step: contract mapping dry-run and safe import slice design.

## Reasons

1. Project relation is mandatory in the target model.

   `construction.contract.project_id` is required. Legacy `XMID` is populated on all 1694 rows, but only 1606 rows match the raw project export and only 121 rows match the known written project skeleton IDs from current migration artifacts.

2. Partner relation is mandatory in the target model.

   `construction.contract.partner_id` is required. Legacy source only provides text values such as `FBF` and `CBF`; this requires partner matching and manual confidence rules before writing.

3. Tax is required and has business constraints.

   `construction.contract.tax_id` is required and must match income/expense direction. The old file does not provide a direct safe `account.tax` id.

4. Contract direction is not yet frozen.

   Target `type` is only `out` or `in`. Legacy values include `SJBMC`, `LX`, `HTLX`, `FBF`, `CBF`, and source-specific markers. A deterministic income/expense rule must be defined first.

5. Amount semantics are not safe yet.

   Target amount fields are computed from contract lines and tax. Legacy `GCYSZJ` and related fields may be useful as reference values, but writing computed amount fields directly is not appropriate.

6. Contract lines are not represented as a structured target-ready line source in this file.

   `construction.contract.line` is BOQ/budget-linked. The old contract CSV mostly contains master, terms, date, party, and summary amount fields.

7. Old deletion/status fields require policy.

   `DEL=1` appears on 65 rows. `DJZT` has values `2`, `0`, empty, `1`, `-1`. These need import filtering/status mapping before create-only write.

## First Safe Field Candidates

These fields are candidates for a future safe slice, not approved for writing in this batch:

| Legacy | Target candidate | Current decision |
|---|---|---|
| `Id` | `legacy_contract_id` if field exists or is added in a later field-alignment batch | needs model coverage audit |
| `HTBT` | `subject` | candidate |
| `HTBH` | reference/code field | needs policy because target `name` is system-generated |
| `XMID` | `project_id` via `project.project.legacy_project_id` | mapping required |
| `FBF` / `CBF` | `partner_id` via text match | mapping required |
| `f_HTDLRQ` | `date_contract` | candidate |
| `f_GCKGRQ` | `date_start` | candidate |
| `JGRQ` | `date_end` | candidate |
| `HTYDFKFS` | `note` or legacy terms field | needs text policy |
| `GCYSZJ` | reference amount field or line-derived amount design | not direct-write safe |

## Required Next Batch

Next recommended batch:

`ITER-2026-04-13-1839 合同数据映射干跑与安全切片专项 v1`

Minimum outputs for the next batch:

- contract field mapping master
- project relation match table by `XMID`
- partner text match table for `FBF` and `CBF`
- contract type/direction mapping table
- status/deletion mapping table
- amount/date/text preprocessing rules
- safe import slice proposal
- GO/NO-GO for small sample contract dry-run
