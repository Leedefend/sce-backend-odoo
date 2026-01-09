# Phase P0 State Machine Spec

Purpose: unify core status semantics so model-layer guards can reference one source of truth.

## Project (project.project.lifecycle_state)

States:
- draft (立项)
- in_progress (在建)
- paused (停工)
- done (竣工)
- closing (结算中)
- warranty (保修期)
- closed (关闭)

Transitions:
- draft -> in_progress | paused | closed
- in_progress -> paused | done | closing | closed
- paused -> in_progress | closed
- done -> closing | warranty | closed
- closing -> warranty | closed
- warranty -> closed

Triggers:
- Manual project lifecycle changes (future guard rules in P0-02+)

## Contract (construction.contract.state)

States:
- draft (草稿)
- confirmed (已生效)
- running (执行中)
- closed (已关闭)
- cancel (已取消)

Transitions:
- draft -> confirmed | cancel
- confirmed -> running | closed | cancel
- running -> closed | cancel

Triggers:
- action_confirm, action_close (or equivalent)

## BOQ (project.boq.line)

BOQ has no explicit workflow state yet. Current controlled enums:
- source_type: tender | contract | settlement

Derived import status (computed on project):
- empty: no BOQ lines
- imported: line_count > 0

Transitions:
- empty -> imported (import/seed)
- imported -> imported (re-import/replace)
- imported -> empty (delete all)

## Settlement Order (sc.settlement.order.state)

States:
- draft (草稿)
- submit (提交)
- approve (批准)
- done (完成)
- cancel (取消)

Transitions:
- draft -> submit | cancel
- submit -> approve | cancel
- approve -> done | cancel

Triggers:
- action_submit, action_approve, action_done

## Settlement (project.settlement.state)

States:
- draft (草稿)
- confirmed (已确认)
- done (完成)
- cancel (取消)

Transitions:
- draft -> confirmed | cancel
- confirmed -> done | cancel

Triggers:
- action_confirm, action_done

## Payment Request (payment.request.state)

States:
- draft (草稿)
- submit (提交)
- approve (审批中)
- approved (已批准)
- rejected (已驳回)
- done (已完成)
- cancel (已取消)

Transitions:
- draft -> submit | cancel
- submit -> approve | rejected | cancel
- approve -> approved | rejected | cancel
- approved -> done | cancel
- rejected -> draft | cancel

Triggers:
- action_submit, action_approve, action_on_tier_approved, action_on_tier_rejected

## Code location

Unified constants live in:
- addons/smart_construction_core/models/support/state_machine.py

Selection fields should reference those constants directly.
