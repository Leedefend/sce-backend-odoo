# Full Rebuild Promotion Queue v1

Iteration: `ITER-2026-04-13-1853`

## Queue Decision

The migration program is now organized as a repeatable full new-database rebuild pipeline, not as one-off table imports.

## P0 Baseline Rebuild

Purpose: ensure a fresh database can install and run the system baseline.

Includes:

- modules;
- permissions and groups;
- menus and views;
- dictionaries;
- stages;
- stable configuration;
- templates.

Preferred mechanism: module XML/CSV/data loading, not ad hoc importer scripts.

## P1 Subject Master Data

Purpose: rebuild cross-business anchors.

Order:

1. partner primary source from `T_Base_CooperatCompany`;
2. supplier role/supplement from `T_Base_SupplierInfo`;
3. cross-source merge governance.

Current status:

- partner strong-evidence candidate slice: 369 rows;
- no-DB importer: PASS;
- write mode: NO-GO until dedicated 30-row create-only sample authorization.

## P2 Project Skeleton

Purpose: rebuild the business container.

Includes:

- project skeleton;
- project legacy identity;
- lifecycle/state semantics;
- project member strategy.

Project member is not a simple detail table. It requires user mapping and permission-impact review before write mode.

## P3 Contract Safe Slice

Purpose: rebuild contract headers only after partner and project anchors are ready.

Includes:

- contract header dry-run;
- project link validation;
- counterparty link validation;
- contract line reconstruction dry-run;
- tax/currency semantics gate.

Current status:

- direct contract import remains blocked by partner/project readiness and counterpart ambiguity.

## P4 Business Documents

Purpose: rebuild business occurrence facts.

Includes:

- receipts;
- payment and settlement only after dedicated high-risk governance;
- later accounting-facing facts only after separate authorization.

Payment, settlement, and account paths remain blocked by repository stop rules unless a dedicated task line is opened.

## P5 Attachment Index

Purpose: keep evidence traceable without blocking core master-data rebuild.

First stage:

- legacy file id;
- business model;
- record identity;
- file name;
- path/hash/size where available;
- old relation;
- availability status.

Do not make full file-content synchronization a prerequisite for partner/project/contract skeleton rebuild.

## P6 Attachment Entity Backfill

Purpose: batch-fill physical files after index traceability is stable.

This stage can run later and must have its own retry, checksum, missing-file, and storage policy.

## Immediate Queue

1. Keep partner as the first importer candidate.
2. Do not promote contract before partner identity and sample write are validated.
3. Do not treat supplier as a separate primary create stream; model it as role/supplement after partner primary governance.
4. Do not process project members until user mapping and permission impact are reviewed.
5. Keep attachment file entities out of the critical path.
