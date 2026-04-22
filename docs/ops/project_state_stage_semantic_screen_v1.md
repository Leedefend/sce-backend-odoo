# Project State vs Stage Semantic Screen v1

## Scope

This screen is a docs-only business-fact semantic classification batch.
It does not change runtime code, contracts, schema, or frontend behavior.

Layer Target: `Business-fact semantic screen`
Module: `project status vs project stage`
Reason: 用户明确要求先回到业务事实层，把“项目状态”和“项目阶段”这两个容易混淆的语义边界先说清楚，再决定后续实现批次。

## Semantic Conclusion

### 1. Project stage should be named project execution stage

`项目阶段` should answer one question only, and the repository should prefer
the fuller name `项目执行阶段` in follow-up implementation and contract cleanup:

Which major business progression position is the project currently in?

At the business-fact layer, this carrier describes sequence/location in the
project execution mainline, such as preparation, execution, closing, warranty,
or done. It is a progression fact, not a value judgment, and it belongs to the
project aggregate itself.

### 2. Project status should not belong to the project aggregate

The user clarified a stronger rule than the first-pass screen:

`项目状态` is not a project semantic.

It should instead answer a document-level question:

What is the current status of the business document being processed?

Examples include contract status, settlement status, payment request status,
task status, or other document/carrier status. This is a record-status
semantic, not a project semantic.

If the product needs to describe the project's current condition, that wording
should use a different semantic lane such as risk, health, lifecycle judgment,
or execution condition, but should not be named `项目状态`.

### 3. The two carriers must not be collapsed

The following collapse is semantically invalid:

- using `项目执行阶段` to stand in for any business document `状态`
- using any business document `状态` to stand in for `项目执行阶段`
- presenting one merged summary as if project stage and document status are the
  same business fact
- deriving `status` from `stage_label`
- deriving project stage from document status text

### 4. The repository should stop using the phrase `项目状态`

Based on the user's clarification, `项目状态` is itself a confusing term and
should be treated as a retirement candidate in later implementation batches.

Preferred replacement directions:

- on project aggregate: use `项目执行阶段`, `项目风险`, `项目健康度`, `项目生命周期判断`
- on business records/documents: use `单据状态`, `合同状态`, `结算状态`, `付款申请状态`

## Current Evidence Of Confusion

### Frontend consumer evidence

`frontend/apps/web/src/views/RecordView.vue`

- The summary label is `项目状态与阶段`.
- The computed summary falls back across `stage_id || stage || state`.
- This means project execution stage and document status are currently merged
  into one display slot.

`frontend/apps/web/src/views/ProjectManagementDashboardView.vue`

- The dashboard already exposes separate text surfaces for `阶段说明` and
  `当前状态说明`.
- This is evidence that the product language already expects two concepts, but
  `当前状态说明` still needs follow-up cleanup to decide whether it should be
  renamed to a project-condition term or rebound to a true document-status
  carrier.

### Backend carrier evidence

`addons/smart_construction_core/services/project_context_contract.py`

- `project_context.stage` is currently filled from `project.lifecycle_state`.
- `project_context.stage_label` is a label translation of the same
  `lifecycle_state`.
- `project_context.status` is separately filled from
  `health_state` or fallback `state`.

This means the backend carrier already hints that `stage` and `status` are two
different facts, but the naming still incorrectly suggests that both belong to
the project aggregate.

`addons/smart_construction_core/services/project_state_explain_service.py`

- `stage_label` is currently derived from `lifecycle_state`.
- `status_explain` is separately derived from `health_state/state`.

This again shows two intended semantic lanes, but the wording is still not
clean enough: the project lane should be `项目执行阶段`, while `状态` should be
reserved for business documents or explicitly renamed to another project
condition semantic.

## Business-Fact Freeze

Until a dedicated implementation batch says otherwise, the repository should
follow this freeze:

- `项目执行阶段`: progression position in the lifecycle/project execution
  mainline
- `项目状态`: do not use as a project-facing semantic in new wording
- `单据状态`: status semantic for business documents/records
- `lifecycle_state`: belongs to the project execution stage lane unless
  reclassified by a later dedicated screen
- `health_state` or equivalent condition carrier: do not automatically label it
  as `项目状态`; later implementation must decide whether it maps to
  `项目健康度` or another project-condition term
- frontend must consume project stage and document status as separate semantics
  and must not merge them by fallback chaining

## Implementation Checkpoint

The first additive implementation batch is now landed:

- `ITER-2026-04-19-PROJECT-EXECUTION-STAGE-CARRIER-IMPLEMENT`
- `project_context` now supplies explicit `execution_stage` and
  `execution_stage_label` while keeping legacy `stage` aliases
- project explanation payloads now supply explicit
  `execution_stage_explain` and `project_condition_explain` while keeping
  legacy `stage_explain` and `status_explain` aliases
- contract/governance copy that labeled `lifecycle_state` as `项目状态` has been
  corrected to `项目执行阶段`

## Architecture Implication

This clarification belongs to the business-fact battlefield first.

That means the next implementation priority is not a frontend wording patch.
The next batch should first make backend semantic carriers explicit and stable:

- project aggregate keeps `项目执行阶段`
- business documents keep their own `状态`
- project condition terms, if still needed, must avoid the ambiguous label
  `项目状态`

Only after that should scene/frontend consume those separate carriers without
guessing.

## Next Recommended Batch

Open a dedicated business-fact implementation batch that:

- freezes the canonical carrier for `项目阶段`
- freezes the canonical carrier for `项目状态`
- removes ambiguous naming where `stage` actually means lifecycle status
- updates downstream contract consumers only after backend carriers are clear

## Decision

Result: `PASS`

Risk: `LOW`

Reason:

- The current repository already contains enough bounded evidence to classify
  the semantic confusion without reopening runtime implementation.
- No forbidden paths were modified in this screen batch.
