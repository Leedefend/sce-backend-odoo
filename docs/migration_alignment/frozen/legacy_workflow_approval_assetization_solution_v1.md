# Legacy Workflow Approval Assetization Solution v1

Status: `FROZEN_JUDGMENT`

## Decision

Do not write legacy approvals into tier.review in the first assetization
implementation.

Legacy `S_Execute_Approval` rows must be treated as historical approval audit
facts first. They may be linked to target business records, displayed for
traceability, and packaged as replayable migration assets after a dedicated
carrier is approved. They must not create current approval todos, validation
status, or runtime workflow transitions.

## Why

The new system currently uses OCA `base_tier_validation` for approval runtime:

- `payment.request` inherits `tier.validation`.
- `request_validation()` creates `tier.review` rows.
- `tier.review` rows carry current waiting/pending/approved/rejected review
  state.
- approval callbacks can change the business document state.

That mechanism is a live approval runtime. The legacy rows are old processing
traces and comments. Directly importing them into `tier.review` would fabricate
live approval state and could confuse pending work, reviewer queues, validation
status, and callback semantics.

## Legacy Data Shape

Source table: `S_Execute_Approval`

Read-only analysis result:

| Metric | Value |
|---|---:|
| raw rows | 163245 |
| loadable historical approval facts | 79702 |
| blocked rows | 83543 |
| matched target records | 29932 |
| ambiguous rows | 0 |

Target lane coverage:

| Lane | Approval rows |
|---|---:|
| outflow_request | 45693 |
| supplier_contract | 13281 |
| receipt | 8556 |
| actual_outflow | 6088 |
| contract | 6084 |

Important field observations:

| Field | Observation |
|---|---|
| `DJID` | present on all rows and is the strongest target business anchor |
| `business_Id` | present on all rows, but often describes workflow setup/context rather than target document |
| `pid` | present on all rows and useful for legacy traceability |
| `f_LRRId` / `f_LRR` | present on all rows; actor identity is useful audit evidence |
| `f_SPSJ` | present on all rows; approval/processing time is useful audit evidence |
| `RecevieTime` | present on most rows; includes default-looking historical values |
| `f_SPYJ` | present on 141822 rows; this is the business-visible approval note |
| `f_SPZT` | mostly `0`, with only 947 rows at `2`; unsafe as a direct approve/reject mapping |
| `f_Back_YJLX` | all rows are `0`; unsafe as a direct rejection mapping |
| `SPLX` | mostly `自审`; useful as raw classification, not runtime workflow type |

Top legacy templates and steps show the rows are cross-business approval traces,
including payment request, supplier contract, income receipt, reimbursement, and
financial income/expense processes. This confirms the data is business history,
not one homogeneous workflow runtime that can be replayed into the new module.

## Target Boundary

Historical approval audit facts:

- preserve old approval row id, target business anchor, actor, time, note,
  source status, source step/template identifiers, and raw legacy labels
- link to target business records by stable external id
- remain read-only after import
- support search, display, and audit review
- support XML or mixed asset replay after model approval

New approval runtime facts:

- continue to use `base_tier_validation`
- create `tier.review` only through normal new-system submission flow
- drive `validation_status`, reviewer queues, and callbacks only for new or
  intentionally re-opened business processes

## Rejected Options

| Option | Decision | Reason |
|---|---|---|
| import to `tier.review` | reject for first implementation | would fabricate live pending/approved validation state |
| import to `sc.workflow.instance` | reject | existing model is runtime instance state, not neutral history |
| import to `sc.workflow.workitem` | reject | would fabricate current/old workitems |
| import to `sc.workflow.log` | reject | requires runtime instance/node references and cannot stand alone |
| import only as chatter messages | reject as primary carrier | loses structured source ids, actor ids, step ids, and target lane classification |
| discard all approval history | reject | 79702 rows are anchored business audit facts |

## Approved Direction

Use a two-lane approval strategy:

1. Historical lane: legacy approval rows become read-only audit facts.
2. Runtime lane: new system approvals remain under `base_tier_validation`.

The historical lane may later expose contextual links from business documents,
but it must not participate in current approval queues or validation callbacks.

## Proposed Historical Carrier

Create a dedicated model only after this solution is accepted.

Candidate model name:

`sc.legacy.workflow.audit`

Candidate fields:

| Field | Purpose |
|---|---|
| `legacy_workflow_id` | stable source row id from `S_Execute_Approval.Id` |
| `legacy_pid` | source pid for traceability |
| `legacy_djid` | target business document anchor from old system |
| `legacy_business_id` | old workflow/setup context anchor |
| `legacy_source_table` | raw/normalized `SJBMC` |
| `target_model` | target Odoo model |
| `target_external_id` | stable target external id; no runtime integer id required in XML |
| `target_lane` | asset lane such as `outflow_request` or `supplier_contract` |
| `actor_legacy_user_id` | old user id |
| `actor_name` | old actor name |
| `approved_at` | old processing time |
| `received_at` | old receive time, kept as source fact |
| `approval_note` | old approval comment |
| `legacy_status` | raw `f_SPZT`; do not over-interpret |
| `legacy_back_type` | raw `f_Back_YJLX`; do not over-interpret |
| `legacy_step_id` | source step id |
| `legacy_template_id` | source template id |
| `legacy_step_name` | optional enriched step label |
| `legacy_template_name` | optional enriched template label |
| `import_batch` | replay batch identity |

Model semantics:

- read-only by ordinary business users after import
- no inheritance from `tier.validation`
- no relation to `tier.review`
- no runtime workflow transition methods
- no automatic update to business document state

## XML Asset Position

After carrier approval, the replay package should be XML-first for the
historical lane because the loadable approval facts are structured and
reference stable external ids.

Expected package:

```text
migration_assets/30_relation/legacy_workflow_audit/
  legacy_workflow_audit_v1.xml
migration_assets/manifest/
  legacy_workflow_audit_external_id_manifest_v1.json
  legacy_workflow_audit_asset_manifest_v1.json
```

Large-file risk should be handled by splitting XML by target lane or batch if
needed. The split must preserve one deterministic external id per source row.

## External ID Rule

Use deterministic external ids:

```text
legacy_workflow_audit_sc_<S_Execute_Approval.Id>
```

Target references must use existing target external ids from asset manifests.
The XML must not depend on current database integer ids.

## Data Inclusion Rule

Include rows when all are true:

- source row exists in `S_Execute_Approval`
- `DJID` or fallback anchor maps to exactly one loadable target business asset
- actor id/name and processing time are present
- row can be represented as historical audit evidence without claiming a new
  approval runtime status

Do not include rows when:

- target business record is not yet assetized
- target anchor maps to multiple target records
- row would require fabricating approval state
- row has no useful target trace after all asset lanes are complete

Blocked rows should remain excluded until their target business lanes are
assetized or intentionally discarded by a later decision.

## Next Implementation Gates

Next implementation gates are mandatory before any code or XML work resumes.

Implementation may resume only through these gates:

1. Carrier design batch: add a neutral historical audit model, no XML yet.
2. Usability/authority batch: add read-only access and business document entry
   points after the model exists.
3. Asset generation batch: generate XML assets from the 79702 currently
   loadable rows.
4. Replay verification batch: import into a fresh database and verify counts,
   anchors, and no `tier.review` pollution.

Stop immediately if a later design attempts to:

- write legacy rows into `tier.review`
- change `payment.request.validation_status` from legacy rows
- trigger approval callbacks from imported history
- replay old workflow instance state as current state
- use database integer ids instead of stable external ids in assets

## Current Judgment

`legacy_approval_history_as_readonly_audit_asset`

The migration mainline should continue with historical approval audit
assetization only after this boundary is accepted.
