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

Semantics:
- done: 现场已竣工，待结算
- closing: 结算流程进行中（至少存在 confirmed/done settlement 或在跑支付/审价）
- warranty: 进入保修履约阶段（不再产生工程量，但可能产生保修任务/费用）

Transitions:
- draft -> in_progress | paused | closed
- in_progress -> paused | done | closing | closed
- paused -> in_progress | closed
- done -> closing | warranty | closed
- closing -> warranty | closed
- warranty -> closed

Triggers:
- action_*: explicit user actions (buttons)
- write/unlink: implicit actions (edit/delete)
- cron: system actions (future)
- Manual lifecycle changes (future guard rules in P0-02+)

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

Running criteria (suggested):
- confirmed: contract effective but no execution evidence
- running: first execution evidence exists (e.g., payment approved, settlement confirmed, or BOQ execution > 0)

## BOQ (project.boq.line)

BOQ has no explicit workflow state yet. Current controlled enums:
- source_type: tender | contract | settlement

Quantity semantics (P0-03):
- qty_planned: plan quantity (alias of quantity)
- qty_done: executed quantity (cannot exceed planned)
- qty_remain = qty_planned - qty_done

Derived import status (computed on project):
- empty: no BOQ lines
- imported: line_count > 0

Transitions:
- empty -> imported (import/seed)
- imported -> imported (re-import/replace)
- imported -> empty (delete all)

Freeze principle (for P0-03+ guards):
- re-import is allowed
- after settlement/payment key nodes, BOQ edits are guarded or versioned

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

Note:
- Settlement Order: process-oriented document (审批型单据)
- Settlement: result/ledger document (生效型单据)

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
