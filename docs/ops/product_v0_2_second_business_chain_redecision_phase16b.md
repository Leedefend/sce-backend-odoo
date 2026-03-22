# Product v0.2 Second Business Chain Re-Decision - Phase 16-B

## Why Re-Decide
- Phase 16-A chose `payment` because it looked closest to the execution flow.
- Phase 16-B adds a stricter rule:
  - future expansion must start from native carrier reuse
  - no shadow `project.<domain>` implementation path

## Re-Evaluation

### Payment
- Native reuse posture:
  - viable only if anchored to `finance.payment_requests` or native accounting views
- Current correction cost:
  - high, because the in-flight draft already drifted toward `project.payment.*`
- Decision:
  - not the first slice under the corrected policy

### Contract
- Native reuse posture:
  - medium, but current repo contract domain is still mostly custom-business heavy
- Current correction cost:
  - high, because contract lifecycle and references are broad
- Decision:
  - defer until orchestration template is proven on a lighter chain

### Cost
- Native reuse posture:
  - best among the three under the corrected policy
  - already reuses `account.move.line` evidence and `project.cost.ledger` / `project.budget` carriers
- Current correction cost:
  - lowest
- Decision:
  - choose `cost` as the next business chain candidate after this correction phase

## New Priority
1. cost
2. payment
3. contract

## Why Cost Wins Now
- It is closer to evidence aggregation than shadow transaction authoring.
- It can stay firmly on top of existing ledger and budget carriers.
- It requires less custom role/action invention than payment under native-only rules.

## Freeze
- The old `payment-first` conclusion is superseded for post-Phase-16-B planning.
