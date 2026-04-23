# Migration Acceleration Rebuild Bus Plan v1

Status: PASS

Task: `ITER-2026-04-15-MIGRATION-ACCELERATION-REBUILD-BUS-PLAN`

## Objective

Replace slow row-slice migration with a dependency-aware rebuild bus. The
strategy is to profile all legacy source files once, resolve anchors in large
groups, write business facts by dependency lane, and run aggregate reviews after
each lane instead of after every small slice.

## Legacy Source Shape

- `project`: rows `755`, columns `63`
- `partner_company`: rows `7864`, columns `131`
- `partner_supplier`: rows `3041`, columns `145`
- `project_member`: rows `21390`, columns `8`
- `contract`: rows `1694`, columns `146`
- `receipt`: rows `7412`, columns `96`
- `payment`: rows `13646`, columns `107`

Key shape conclusion:

- The legacy source is file-based and denormalized. Contracts carry text
  counterparties and project ids rather than stable target foreign keys.
- Project, partner, project-member, contract, receipt, and payment files are
  separate dependency surfaces; the correct write order is anchors first,
  dependent facts second, financial/high-risk facts last.
- Bad or incomplete legacy rows are common enough that discard policy must be a
  first-class lane, not an exception handled inside every write batch.

## Target Structure Snapshot

Target row counts:

- `res_partner`: `6115` rows
- `project_project`: `1473` rows
- `construction_contract`: `1415` rows
- `sc_project_member_staging`: `7389` rows

Target model field shape:

- `account.payment`: fields `188`, required `8`
- `account.payment.method`: fields `9`, required `3`
- `account.payment.method.line`: fields `17`, required `1`
- `account.payment.register`: fields `46`, required `1`
- `account.payment.term`: fields `24`, required `2`
- `account.payment.term.line`: fields `13`, required `3`
- `construction.contract`: fields `65`, required `7`
- `construction.contract.line`: fields `23`, required `1`
- `payment.capture.wizard`: fields `18`, required `0`
- `payment.ledger`: fields `15`, required `3`
- `payment.link.wizard`: fields `16`, required `3`
- `payment.method`: fields `21`, required `3`
- `payment.provider`: fields `48`, required `4`
- `payment.provider.onboarding.wizard`: fields `14`, required `0`
- `payment.refund.wizard`: fields `15`, required `0`
- `payment.request`: fields `70`, required `6`
- `payment.token`: fields `16`, required `4`
- `payment.transaction`: fields `44`, required `7`
- `project.project`: fields `240`, required `10`
- `project.settlement`: fields `39`, required `5`
- `project.settlement.line`: fields `11`, required `2`
- `report.account.report_invoice_with_payments`: fields `0`, required `0`
- `res.partner`: fields `174`, required `2`
- `sc.project.member.staging`: fields `17`, required `7`
- `sc.settlement.order`: fields `30`, required `4`
- `sc.settlement.order.line`: fields `14`, required `2`

Legacy identity fields currently available:

- `construction.contract.legacy_contract_id`
- `construction.contract.legacy_contract_no`
- `construction.contract.legacy_counterparty_text`
- `construction.contract.legacy_deleted_flag`
- `construction.contract.legacy_document_no`
- `construction.contract.legacy_external_contract_no`
- `construction.contract.legacy_project_id`
- `construction.contract.legacy_status`
- `project.project.legacy_attachment_ref`
- `project.project.legacy_company_id`
- `project.project.legacy_company_name`
- `project.project.legacy_is_material_library`
- `project.project.legacy_is_shared_base`
- `project.project.legacy_parent_id`
- `project.project.legacy_price_method`
- `project.project.legacy_project_id`
- `project.project.legacy_project_manager_name`
- `project.project.legacy_project_nature`
- `project.project.legacy_region_id`
- `project.project.legacy_region_name`
- `project.project.legacy_sort`
- `project.project.legacy_specialty_type_id`
- `project.project.legacy_stage_id`
- `project.project.legacy_stage_name`
- `project.project.legacy_state`
- `project.project.legacy_technical_responsibility_name`
- `res.partner.legacy_credit_code`
- `res.partner.legacy_deleted_flag`
- `res.partner.legacy_partner_id`
- `res.partner.legacy_partner_name`
- `res.partner.legacy_partner_source`
- `res.partner.legacy_source_evidence`
- `res.partner.legacy_tax_no`
- `sc.project.member.staging.legacy_member_id`
- `sc.project.member.staging.legacy_project_id`
- `sc.project.member.staging.legacy_role_text`
- `sc.project.member.staging.legacy_user_ref`

Structure conclusion:

- The new system can support high-throughput rebuild if every lane uses legacy
  identity fields as idempotency keys.
- Required foreign keys force strict anchor order: partner/project before
  contract; contract header before line/receipt/payment-style lanes.
- Payment, settlement, and accounting paths remain high-risk and must stay
  behind separate dedicated authority tasks.

## Current Migration Evidence

- Contract header: `1332` rows confirmed in target.
- Contract full source: `1694` rows total.
- Contract existing or migrated: `1332` header-lane + `12` pre-existing.
- Contract remaining blocked: `350`.
- Remaining blocker routes: `{"discard_deleted_source": 65, "partner_anchor_recovery_screen": 197, "project_anchor_recovery_screen": 88}`.
- Partner-source 57 design: `57` rows, `12` distinct counterparties.

## Why The Current Process Is Too Slow

1. It repeatedly performs scan/screen/design/write/review for small row slices.
2. It treats dependent contract rows as the work unit, while the real blocker is
   usually an anchor group such as project id or counterparty text.
3. It runs many post-write reviews that could be collapsed into one aggregate
   review when the write script is idempotent and rollback keyed.
4. It opens downstream readiness after each local success instead of computing a
   global lane manifest and consuming it in larger batches.

## Accelerated Rebuild Bus

### Bus 0: Global Profile Ledger

Create one generated manifest for every legacy file:

- source row count, headers, key fields, delete flags;
- target model/table, legacy identity field, required target anchors;
- discard policy route;
- high-risk domain flag.

This replaces ad hoc per-lane discovery.

### Bus 1: Anchor Lanes

Run anchors as grouped batches, not dependent rows:

- Partner anchor: group by normalized partner name and legacy source identity.
- Project anchor: group by legacy project id.
- User/member anchor: group by project/person/role neutral carrier.

Write size should be based on distinct anchors, not contract rows. For the
current contract blockers, the 57-row contract retry depends on only 12
counterparty anchors.

### Bus 2: Fact Header Lanes

After anchors are stable, write header facts in larger idempotent lanes:

- contract header;
- receipt header;
- later approved high-risk financial headers only under dedicated contracts.

Use fixed lanes of 500-1000 rows when all rows share the same write template and
rollback key.

### Bus 3: Dependent Detail Lanes

Open only after header aggregate closure:

- contract lines or BOQ-bound details;
- receipt/detail rows;
- file attachments or auxiliary facts.

Do not mix line/detail writes with header anchor recovery.

### Bus 4: Discard And Hold Ledger

Discard/hold rows must be materialized as evidence artifacts once per domain:

- deleted legacy rows;
- source-missing anchors;
- direction-deferred contracts;
- ambiguous partner or project anchors;
- high-risk financial rows requiring separate authorization.

This prevents the same bad rows from being re-screened every batch.

### Bus 5: Aggregate Verification

Verification should move from slice-local to lane-global:

- pre-write profile hash;
- write result with legacy ids and rollback ids;
- post-write aggregate count by source/target/rollback;
- residual blocker manifest.

Per-slice post-write review remains only for high-risk batches.

## Immediate Execution Plan

1. Open `CONTRACT-PARTNER-SOURCE-12-ANCHOR-DESIGN`: collapse the 57 contract rows
   into 12 distinct company-source partner anchors.
2. Open one bounded partner-anchor write only if the 12-anchor design proves
   idempotent and rollback-keyed.
3. Re-run contract readiness only for the 57 dependent contract ids after the
   12 anchors exist.
4. Keep 65 deleted, 88 project-source-missing, 74 partner-source-missing, and 61
   direction-deferred rows in discard/hold artifacts; do not re-screen them in
   every batch.
5. Generate a global migration manifest for receipt/payment-style source files,
   but do not open payment, settlement, or accounting writes without dedicated
   high-risk task contracts.

## New Batch Size Rule

- No-DB scan/screen/design: full lane, not 100/200 row slices.
- Low-risk create-only writes with stable anchors: 500-1000 rows.
- Anchor writes: distinct anchor count, normally 50-500 per batch.
- High-risk authority/financial writes: dedicated task and smaller batch.
- Aggregate reviews: one per lane after write completion.

## Stop Rules

- Any failed `make verify.*` stops the bus.
- Any payment/settlement/accounting write requires a dedicated high-risk task.
- Any missing legacy identity stops DB write and stays in design.
- Any frontend or ACL need is a separate task line.
