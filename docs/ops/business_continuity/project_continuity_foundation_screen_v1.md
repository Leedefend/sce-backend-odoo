# Project Continuity Foundation Screen v1

Task: `ITER-2026-04-17-PROJECT-CONTINUITY-FOUNDATION-SCREEN`

Source lane: `Lane A: Project Continuity Foundation`

Mode: screen only

Runtime:
- profile: daily
- database: `sc_demo`
- timestamp: `2026-04-17T20:49:57+08:00`

## Boundary

This screen defines project continuity candidate rules. It does not implement
database writes or code changes.

## Evidence

### Current imported project facts

- `project_project`: 756 records
- all records have `lifecycle_state=draft`
- all records have `phase_key=initiation`
- all records have `sc_execution_state=ready`
- all records have empty `legacy_state`
- all records have empty `legacy_stage_id`
- all records have empty `legacy_stage_name`
- all records have missing `company_id`
- all records have missing `partner_id`
- all records have missing `legacy_company_id`
- all records have missing `legacy_company_name`
- all records have `user_id`

### Downstream business facts

Out of 756 imported projects:

- 652 have contracts
- 621 have payment requests
- 595 have payment ledger records
- 616 have legacy financial fact records
- 701 have at least one downstream business fact

### Capability matrix

`draft`:
- allows basic edit and contract creation
- denies task creation/start/complete
- denies settlement creation
- denies payment submission
- denies cost entry

`in_progress`:
- allows task creation/start/complete
- allows settlement creation
- allows payment submission
- allows contract creation
- allows BOQ edit
- allows cost entry

## Screened Rules

### Rule A1: downstream-fact projects should leave draft

If an imported project has at least one downstream business fact, then keeping
it in `draft/initiation` blocks daily continuation.

Candidate target:

- `lifecycle_state`: `in_progress`
- `phase_key`: `execution`
- `sc_execution_state`: `in_progress`

Evidence basis:

- downstream contracts, payment requests, ledgers, or legacy financial facts
  prove that the project has moved beyond initial setup.
- `in_progress` is the lowest active lifecycle state that opens daily execution
  capabilities without implying closeout or completion.

Implementation preflight result:

- current ORM transition guard requires `owner_id`, `location`, and BOQ facts
  before `draft -> in_progress`.
- runtime evidence shows 756/756 projects miss `owner_id`.
- runtime evidence shows 756/756 projects miss `location`.
- runtime evidence shows 756/756 projects miss `boq_line_count`.
- runtime evidence shows 0/756 projects are transition-ready under the current
  guard.

Screen decision:

- do not run direct lifecycle writes in the first implementation batch.
- first implementation must either materialize the missing transition facts from
  reliable imported evidence or introduce a dedicated, auditable imported-record
  continuity path.
- direct SQL bypass of the lifecycle guard is not approved by this screen.

### Rule A2: no-downstream projects should remain draft

If an imported project has no downstream business facts, keep:

- `lifecycle_state`: `draft`
- `phase_key`: `initiation`
- `sc_execution_state`: `ready`

Reason:

- no evidence proves the project should enter execution.

### Rule A3: do not infer company/customer in this batch

No available project-level imported evidence exists for:

- `company_id`
- `partner_id`
- `legacy_company_id`
- `legacy_company_name`

Candidate treatment:

- keep company/customer fields unchanged.
- record this as a separate data-quality/business-fact exception.
- do not fabricate owner/customer facts from project name or downstream records in this batch.

### Rule A4: do not classify done/closing/warranty in this batch

The current evidence proves only that many projects are beyond draft. It does
not prove:

- closing
- warranty
- done
- closed

Candidate treatment:

- align only to `in_progress` for downstream-fact projects.
- later contract/payment/settlement screens may upgrade specific projects if
  stronger facts exist.

## First Implement Batch Recommendation

Original direct state-sync batch is blocked by transition preflight.

Create a narrower dedicated implementation-prep batch:

`ITER-2026-04-17-PROJECT-CONTINUITY-TRANSITION-GUARD-RECOVERY`

Objective:

- recover the missing transition prerequisites for imported projects or define
  an approved imported-record lifecycle alignment path.
- do not write lifecycle state until transition preconditions are satisfied or
  explicitly governed.

Allowed implementation ownership:

- business-fact layer
- `project.project` continuity facts
- script/report artifacts

Stop conditions:

- ORM transition guard blocks the update and requires missing project facts
- any rule tries to infer company/customer without evidence
- any implementation touches payment/settlement/account/security/manifest code
- any implementation changes frontend behavior

## Non-Goals

- Do not update contracts.
- Do not update payments.
- Do not create settlements.
- Do not create material/procurement records.
- Do not infer missing company/customer facts.
