# Product Native Alignment Business Mapping v1

## Goal
- Freeze the native carrier for `payment / contract / cost` before any new product slice is implemented.
- Ensure product expansion is `native model reuse + scene orchestration`, not `new project-scoped business implementation`.

## Mapping Principles
- Domain truth must stay on an existing native or already-settled business carrier model.
- Product scenes may add entry guidance, filters, summaries, and next actions.
- Product scenes may not replace the native record lifecycle with a new shadow lifecycle.
- `project.*` scenes may carry context and orchestration only. They may not become the primary finance / contract / cost system of record.

## Payment Mapping
- Primary native carriers:
  - `account.move`
  - `payment.request` in the current repo as existing finance workflow carrier
  - `mail.activity` for finance follow-up only when already part of the native flow
- Preferred scene anchor:
  - `finance.payment_requests`
  - native `account.move` list/form when the scenario is invoice-driven
- Allowed orchestration:
  - from project execution, emit a next action that deep-links into finance scene with `project_id`
  - show readiness summary and blocker explanation on the project side
  - reuse existing finance approval / review action chain
- Forbidden expansion:
  - new `project.payment.*` scene family as a finance shadow product
  - project-side custom payment state machine
  - duplicating payment list/detail runtime blocks that restate native finance records

## Contract Mapping
- Primary native carriers:
  - `construction.contract`
  - `construction.contract.line`
  - `sc.settlement.order`
- Preferred scene anchor:
  - contract center / native contract list-form entry
- Allowed orchestration:
  - project side only provides contract entry hint, filter context, and dependency summary
  - settlement / payment relation is exposed through native contract references
- Forbidden expansion:
  - `project.contract.*` shadow scene family
  - project-side duplicate contract lifecycle
  - contract truth copied into project dashboard-only records

## Cost Mapping
- Primary native carriers:
  - `project.budget`
  - `project.budget.boq.line`
  - `project.cost.ledger`
  - `account.move.line` as upstream accounting evidence
- Preferred scene anchor:
  - native budget / ledger / analytic views already bound to project context
- Allowed orchestration:
  - project side exposes cost readiness, reconciliation summary, and native deep links
  - cost view may aggregate from existing ledger and budget carriers
- Forbidden expansion:
  - `project.cost.*` transaction scene family
  - custom project-side cost posting workflow
  - bypassing `account.move.line` or `project.cost.ledger` evidence path

## Product Boundary
- Product layer owns:
  - scene entry
  - blocker copy
  - navigation continuity
  - orchestration hints
- Native/business layer owns:
  - record lifecycle
  - write semantics
  - approval semantics
  - accounting / contract / cost truth

## Immediate Impact
- Any v0.2 slice proposal must first declare:
  - target native model
  - target native scene
  - orchestration-only additions
  - explicit non-goals preventing shadow implementation
