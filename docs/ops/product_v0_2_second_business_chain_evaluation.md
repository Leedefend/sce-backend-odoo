# Product v0.2 Second Business Chain Evaluation

## Purpose
- Evaluate the best next business chain after v0.1 project execution.
- Candidate set:
  - cost
  - contract
  - payment

## Evaluation Criteria
- adjacency to v0.1 execution flow
- existing repository evidence and semantic surface
- role clarity
- operator explainability
- implementation risk
- ability to produce a clear pilot story

## Candidate 1: Cost
- Evidence:
  - `addons/smart_construction_core/models/core/cost_domain.py`
  - `addons/smart_construction_core/tests/test_cost_compare.py`
- Strengths:
  - strong analytical value
  - project-adjacent data
- Risks:
  - more report-like than action-like
  - operator “next step” path may be weaker than execution/payment
  - harder to make a clean non-developer transactional story in the next phase
- Assessment:
  - good secondary visibility chain
  - weaker as the first v0.2 expansion chain

## Candidate 2: Contract
- Evidence:
  - `addons/smart_construction_core/views/core/contract_views.xml`
  - `addons/smart_construction_core/tests/test_contract_center.py`
- Strengths:
  - business importance is high
  - clear project relationship
- Risks:
  - document and line-item semantics are richer and heavier
  - broader lifecycle and accounting coupling
  - likely higher modeling cost before a simple pilot story emerges
- Assessment:
  - strategically important
  - better as a later expansion after one lighter cross-role chain is proven

## Candidate 3: Payment
- Evidence:
  - `addons/smart_construction_core/models/core/payment_request.py`
  - `addons/smart_construction_core/handlers/payment_request_available_actions.py`
  - `addons/smart_construction_core/tests/test_payment_request_available_actions_backend.py`
  - `addons/smart_construction_core/core_extension.py`
- Strengths:
  - already has action semantics and handoff hints
  - naturally introduces multi-role behavior without requiring a full permission redesign
  - easier to demonstrate a compact operator flow:
    - project side prepares
    - finance side reviews/acts
    - executive side escalates on exception
- Risks:
  - touches approval semantics
  - requires careful role-boundary explanation
- Assessment:
  - best candidate for v0.2 first expansion

## Recommended Priority
1. payment
2. contract
3. cost

## Decision
- Choose `payment` as the preferred v0.2 second business chain.

## Why Payment Wins
- It already contains action-oriented behavior instead of pure reporting.
- It gives the cleanest bridge from single-operator execution to multi-role product behavior.
- It can validate handoff semantics before the system attempts heavier contract or cost orchestration.

## Deferred Topics
- contract can become the next chain after payment if role handoff semantics stabilize
- cost should stay as an insight/analysis chain until a stronger operator path is defined
