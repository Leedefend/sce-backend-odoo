# SCBS Business Entity Acceptance Design

Date: 2026-05-05
Branch: `business-data-maintenance`

## Decision

SCBS legacy data has two different organization concepts:

1. Company-level isolation entity in the new system.
2. Business/accounting entity in the business facts.

These must remain separate.

`res.company` is the hard isolation boundary. It controls login company context,
record rules, approval scope, accounting ownership, and future company switching.

The legacy `XMID/XMMC` carrier should not be mapped directly to `res.company`.
It should first be accepted as a business/accounting entity under an accepted
new-system company.

## Target Concepts

| Concept | Target model | Purpose | Created by |
| --- | --- | --- | --- |
| Company isolation entity | `res.company` | Permission, company context, approval/accounting boundary | Manual business decision |
| Business/accounting entity | new support model, suggested `sc.business.entity` | Independent operating/accounting carrier inside a company | Migration mapping + review |
| Real construction project | `project.project` | Project ledger, project execution, cost/profit reporting | Project mapping |
| Counterparty | `res.partner` | Supplier, customer, owner, payable/receivable party | Partner mapping |
| Department | `hr.department` or legacy department staging | Handling / applicant / internal org dimension | Org mapping |

## Proposed Model

Suggested model: `sc.business.entity`

This should be a support/master-data model, not a replacement for `res.company`.

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | Char | yes | Accepted display name |
| `company_id` | Many2one `res.company` | yes | Hard isolation owner |
| `partner_id` | Many2one `res.partner` | no | Legal/counterparty identity if applicable |
| `entity_type` | Selection | yes | `internal`, `affiliate`, `trade`, `labor`, `platform`, `project_carrier`, `unknown` |
| `mapping_state` | Selection | yes | `draft`, `candidate`, `confirmed`, `conflict`, `archived` |
| `legacy_xmid` | Char | no | Main legacy carrier ID |
| `legacy_xmmc` | Char | no | Main legacy carrier name |
| `legacy_company_id` | Char | no | Raw legacy `COMPANYID` |
| `legacy_company_name` | Char | no | Raw legacy `COMPANYNAME` |
| `notes` | Text | no | Business review notes |
| `active` | Boolean | yes | Normal Odoo lifecycle |

Unique policy:

- Do not enforce unique `name` globally.
- Enforce unique active `legacy_xmid` when present.
- Allow many legacy IDs to one accepted target through a mapping table, because
  the restored data contains same-name different-ID carriers.

## Proposed Mapping Model

Suggested model: `sc.legacy.business.entity.map`

Purpose: preserve every old identity and bind it to an accepted business entity
only after review.

Fields:

| Field | Type | Notes |
| --- | --- | --- |
| `source_table` | Char | Example: `BASE_SYSTEM_PROJECT`, `T_GYSHT_INFO` |
| `legacy_xmid` | Char | Raw old ID |
| `legacy_xmmc` | Char | Raw old name |
| `legacy_company_id` | Char | Raw old company ID if present |
| `legacy_company_name` | Char | Raw old company name if present |
| `business_entity_id` | Many2one `sc.business.entity` | Accepted target |
| `company_id` | Many2one `res.company` | Accepted hard isolation company |
| `partner_id` | Many2one `res.partner` | Optional legal/counterparty match |
| `mapping_state` | Selection | `candidate`, `confirmed`, `conflict`, `ignored` |
| `confidence` | Float | Automated match confidence |
| `evidence` | Text | Counts, amounts, source facts |
| `reviewer_id` | Many2one `res.users` | User who accepted the mapping |
| `reviewed_at` | Datetime | Acceptance time |

This mapping model is the safety valve. It lets us keep old IDs exactly as they
were while preventing accidental company creation or accidental project mapping.

## Fact Model Extension

Existing legacy fact models already carry `project_id`, `company_id`, and
`partner_id` in several places. They are missing the business/accounting entity
axis.

Add these fields gradually to staging/fact models that import SCBS data:

| Field | Type | Meaning |
| --- | --- | --- |
| `business_entity_id` | Many2one `sc.business.entity` | Accepted business/accounting carrier |
| `business_entity_legacy_id` | Char | Raw `XMID` / `f_XMID` |
| `business_entity_legacy_name` | Char | Raw `XMMC` / `ProjectName` |
| `legacy_gcmc` | Char | Raw real project name field |
| `mapping_state` | Selection | Fact-level mapping status |

Priority fact models:

1. `sc.legacy.payment.residual.fact` or a new SCBS payment fact model for `T_FK_Supplier`.
2. `sc.legacy.purchase.contract.fact` or a new SCBS supplier contract fact model for `T_GYSHT_INFO`.
3. `sc.legacy.fund.daily.line` or a new SCBS fund daily snapshot/header model for `D_SCBSJS_ZJGL_ZJSZ_ZJRBB`.
4. Material stock-in/out staging models for `T_RK_RKD/T_CK_CKD`, if this slice is accepted into material facts.

Do not add `business_entity_id` to every formal business model in the first
iteration. Start with staging and reporting projections. Promote to formal
models only when the user confirms the dimension is needed in day-to-day forms
and workflows.

## Mapping Rules

### `res.company`

Create or map a `res.company` only when the user confirms a hard isolation
boundary:

- independent company login or company switching is required;
- users should not see records of other companies by default;
- approval/accounting ownership must be isolated;
- this is not just a name that looks like a company.

### `sc.business.entity`

Map `XMID/XMMC`, `f_XMID/XMMC`, or supplier-contract `XMID/ProjectName` here
first.

This dimension answers: which operating/accounting carrier owns this business
fact inside the company?

### `project.project`

Map `GCMC` here when it represents a real construction project.

This dimension answers: which construction project ledger should this fact
belong to?

### `res.partner`

Map `f_SupplierID/f_SupplierName`, `f_GYSID/f_GYSName`, and `DWMC` here.

Partner duplicate handling must use:

- tax code when reliable;
- normalized name as candidate evidence only;
- manual review for duplicate target partners;
- raw legacy source ID preservation.

## Import Flow

1. Restore and profile source backup.
2. Generate distinct legacy carrier matrix.
3. Generate distinct real-project `GCMC` matrix.
4. Generate partner duplicate matrix.
5. Create candidate `sc.legacy.business.entity.map` rows.
6. User reviews and confirms mapping rows.
7. Create or bind `sc.business.entity` rows.
8. Import facts into staging models with raw IDs and mapping state.
9. Produce reconciliation reports:
   - imported row count by source table;
   - amount totals by source table;
   - unresolved carrier count;
   - unresolved project count;
   - unresolved partner count;
   - duplicate/conflict count.
10. Only after reconciliation passes, project selected facts into formal
    business models or reporting projections.

## Access And Isolation

`sc.business.entity` itself should be company-owned:

- records have `company_id`;
- normal users only see entities whose `company_id` is in their allowed
  companies;
- migration/admin users can see all during mapping;
- platform shared resources remain outside this model unless explicitly bound.

Legacy staging facts should follow stricter rules:

- read/write for migration/admin users;
- read-only or hidden for normal users until accepted;
- no workflow actions from staging facts unless explicitly designed.

## Current SCBS Mapping Interpretation

Based on restored facts:

- high-weight `XMID/XMMC` values should be candidate `sc.business.entity`
  records under `四川保盛建设集团有限公司` until the user confirms any of them
  must become real `res.company` records.
- `GCMC` values should be candidate `project.project` matches.
- carrier names that already exist in `res.partner` should be linked as
  candidate `partner_id`, but duplicates must not be auto-merged.
- `公司综合平台` should be treated as a special platform/company-level carrier,
  not a construction project.
- deleted or test legacy carriers such as `测试项目` should be ignored or kept
  only as inactive staging evidence.

## Open Business Decisions

The final design needs these confirmations:

1. Which high-weight carriers are true legal companies requiring hard isolation?
2. Which carriers are internal/affiliate/accounting subjects under the main
   company?
3. Should users filter and report daily operations by business entity?
4. Should forms expose business entity as a required field, or only reports?
5. Should old same-name different-ID carriers merge into one business entity?
6. How should old supplier payments reconcile to contracts when `f_HTID` is empty?

## Recommended Next Step

Implement no live business imports yet.

Next technical iteration should build the candidate mapping matrix and, if
accepted, add the minimal support models:

- `sc.business.entity`
- `sc.legacy.business.entity.map`

Then import only mapping candidates and staging facts. Do not project into
formal contracts/payments until the mapping review passes.

## Implementation Status

Implemented in this branch:

- `sc.business.entity`
  - company-owned business/accounting carrier;
  - optional `res.partner` binding;
  - legacy `XMID/XMMC` preservation;
  - active legacy ID uniqueness inside one company.
- `sc.legacy.business.entity.map`
  - source-table plus legacy-ID mapping identity;
  - target business entity, company, and optional partner candidate;
  - candidate/confirmed/conflict/ignored review states;
  - review user and review timestamp;
  - evidence fields for source count, row count, and amount signal.
- Data-center menus for config admins:
  - `业务核算主体`
  - `旧库业务主体映射`
  - `旧库项目映射`
- `sc.legacy.project.map`
  - source-table plus legacy `GCMC` mapping identity;
  - target `project.project` candidate;
  - candidate/confirmed/conflict/ignored review states;
  - exact/fuzzy/manual/none match method;
  - source count, fact row count, amount, date range, and source-family
    evidence;
  - non-real labels such as `公司综合平台` stay in conflict state with no
    target project.
- `sc.legacy.partner.map`
  - source-table plus legacy partner mapping key;
  - target `res.partner` candidate;
  - candidate/confirmed/conflict/ignored review states;
  - tax-code/name/manual/multiple/none match method;
  - duplicate count, active row count, tax-code count, carrier count, and
    carrier sample evidence;
  - tax-code conflicts stay in conflict state and require manual target
    selection before confirmation.

Validation completed:

- Python compile passed for the new model file.
- XML parse passed for the new views.
- `git diff --check` passed.
- Odoo module upgrade passed on `sc_prod_sim`.
- Runtime smoke passed:
  - temporary business entity created;
  - temporary mapping created;
  - mapping confirmation wrote reviewer/review time;
  - duplicate `source_table + legacy_xmid` was blocked;
  - project candidate import created 43 review rows without creating formal
    projects;
  - repeated project import updated the same 43 rows and left
    `project.project` at 785 rows.
  - partner candidate import created 549 review rows without creating or
    merging partners;
  - repeated partner import updated the same 549 rows and left `res.partner`
    at 7288 total rows: 7284 active, 4 inactive;
  - partner smoke confirmed manual mappings, blocked duplicate source keys, and
    blocked non-manual confirmation of tax-code conflicts.
  - SCBS staging fact import created 15223 rows in
    `sc.legacy.scbs.fact.staging`;
  - repeated staging import updated the same 15223 rows;
  - staging reconciliation confirmed 0 projection-ready rows, 9536
    staging-only rows, 5146 missing-mapping rows, and 541 conflict rows;
  - fact partner candidate backfill created 431 partner review rows without
    creating or merging partners;
  - after rerunning staging import, partner-mapped staged facts increased from
    6371 to 11409, missing-mapping rows dropped from 5146 to 213, and
    staging-only rows increased from 9536 to 14469;
  - fact dimension candidate backfill created 29 business-entity mapping
    candidates and 1 project mapping candidate without creating companies,
    projects, partners, or formal facts;
  - after rerunning staging import again, missing-mapping rows dropped from
    213 to 0, staging-only rows increased to 14672, and conflict rows increased
    from 541 to 551 because test/non-project values are now explicitly
    represented as conflict or ignored mappings;
  - formal `res.company`, `project.project`, `res.partner`, and
    `construction.contract` counts stayed unchanged.
  - temporary records were cleaned up.

Still intentionally not implemented:

- SCBS fact projection into formal business documents.
- automatic creation of `res.company`.
- automatic merge of same-name legacy IDs.
- projection into formal contracts, payments, stock, or accounting documents.

## Candidate Import Status

The first SCBS business-entity candidate import has been executed in
`sc_prod_sim`.

Imported scope:

- 11 high-weight business entity candidates.
- 1 platform candidate: `公司综合平台`.

Result:

- `sc.business.entity`: 12 candidate rows.
- `sc.legacy.business.entity.map`: 12 candidate rows.
- `res.company`: unchanged at 1 row.
- all mappings remain `candidate`; none were auto-confirmed.

The import script is idempotent. A repeated write updated the existing 12 entity
rows and 12 mapping rows without creating duplicates.

## Current Acceptance Gate

The technical staging gate is now complete for the restored slice:

| Gate | Rows | Status |
| --- | ---: | --- |
| missing mapping / blocked | 0 | closed |
| staging-ready candidates | 14672 | waiting for business mapping confirmation |
| conflict review queue | 551 | waiting for manual decision |
| projection-ready facts | 0 | intentionally blocked until mappings are confirmed |

Remaining conflicts are expected business-review items, not loader failures:

- partner tax-code conflicts and duplicate target ambiguity;
- `公司综合平台` where a legacy label is not a real construction project;
- legacy test values such as `测试项目`;
- one malformed/placeholder legacy carrier key with amount 600.00, preserved as
  a candidate instead of being normalized away.

The accepted production rule remains: no row enters formal contracts, payments,
stock, accounting, or project ledgers until all dimensions required by that row
are confirmed or explicitly ignored by business review.

## Review Execution Layer

Added a controlled decision workflow for business review:

- `scripts/migration/scbs_mapping_decision_workbook.py` exports every
  unconfirmed SCBS mapping row that is attached to staged facts.
- `scripts/migration/scbs_mapping_decision_apply.py` applies approved decisions
  from the workbook.
- Apply mode defaults to dry-run. Write mode requires
  `SCBS_MAPPING_DECISION_APPLY_MODE=write`.
- Confirmation only binds existing target IDs:
  - `sc.business.entity` for business-entity mappings;
  - `project.project` for project mappings;
  - `res.partner` for partner mappings.
- The apply script does not create target records and does not write formal
  business facts.

This turns the remaining gap into an auditable approval queue instead of an
implicit migration rule.

The expected execution chain for a filled workbook is:

1. Run `scbs_mapping_decision_validate.py`.
2. Review validation errors and projection simulation.
3. Run `scbs_mapping_decision_apply.py` in dry-run mode.
4. Only if both pass, run apply with `SCBS_MAPPING_DECISION_APPLY_MODE=write`.
5. Rerun staging import/reconciliation to compute the real `projection_ready`
   rows.

The validator has been run against the current blank workbook. It produced no
errors and correctly simulated the current state: 14672 staging-ready rows, 551
conflict rows, and 0 projection-ready rows.

For practical review, the main workbook has also been split by suggested action.
Each split CSV can be validated and applied independently by setting
`SCBS_MAPPING_DECISION_CSV`. This allows the business to process tax-code
conflicts, non-counterparty labels, duplicate partner targets, business-entity
confirmation, project confirmation, and normal partner confirmation as separate
approval batches.

Added `scbs_mapping_decision_batch_validate.py` to validate all split workbooks
from the manifest in one pass. The current pre-review baseline is 8 `BLANK`
batches, 0 `READY`, 0 `PARTIAL`, and 0 `HAS_ERRORS`.

Added `scbs_mapping_decision_refresh_reports.sh` as the repeatable refresh
entry point for the decision phase. It rebuilds the workbook, split batches,
target candidate reports, validation artifacts, batch validation, and readiness
dashboard in one run.
