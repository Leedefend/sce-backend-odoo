# v1.1 Historical Backlog Scope Decision

Date: 2026-07-12
Decision owner: release owner
Related issue: `#1025`

## Decision

Historical BOQ and model backlog issues remain outside the `v1.1 Engineering Convergence` milestone.

They are valid product and domain backlog items, but they are not accepted into the current convergence milestone because v1.1 is a freeze, governance, evidence, quality-gate, and pilot-readiness convergence track. Pulling unfinished domain feature backlog into this milestone would expand scope after the freeze and weaken the release evidence.

## Included in v1.1

- GitHub governance, PR rules, CODEOWNERS, and branch protection.
- Unified local and remote CI quality gates.
- Test inventory, test layering, dedupe disposition, and follow-up test issues.
- Fixed-data E2E evidence for the selected convergence journeys.
- Architecture boundaries, dependency map, complexity budget, and split-plan queue.
- Security scan baseline and release evidence documentation.

## Deferred Historical Backlog

These issues are explicitly deferred from v1.1 and should keep no v1.1 milestone until a product-scope milestone is opened:

| Issue | Scope | Decision |
| --- | --- | --- |
| `#2` | Model backlog baseline document | Defer to product/domain backlog planning |
| `#4` | `project.budget` / `project.budget.line` model creation | Defer to product/domain backlog planning |
| `#5` | `project.contract` / `project.contract.line` model creation | Defer to product/domain backlog planning |
| `#6` | `project.change.order` model creation | Defer to product/domain backlog planning |
| `#7` | `sc.work.visa` model creation | Defer to product/domain backlog planning |
| `#8` | `sc.settlement` model creation | Defer to product/domain backlog planning |
| `#9` | `progress.entry` / `progress.line` refactor | Defer to product/domain backlog planning |
| `#64` | BOQ Excel template parsing rules | Defer to BOQ productization milestone |
| `#65` | BOQ chapter structure parsing | Defer to BOQ productization milestone |
| `#66` | BOQ item normalization and numbering | Defer to BOQ productization milestone |
| `#67` | BOQ unit recognition | Defer to BOQ productization milestone |
| `#68` | BOQ feature description recognition | Defer to BOQ productization milestone |
| `#69` | BOQ quantity recognition | Defer to BOQ productization milestone |
| `#70` | BOQ line classification | Defer to BOQ productization milestone |
| `#71` | BOQ conversion to `project.boq.line` | Defer to BOQ productization milestone |
| `#72` | BOQ import validation errors | Defer to BOQ productization milestone |
| `#73` | BOQ tree structure construction | Defer to BOQ productization milestone |
| `#74` | BOQ to budget mapping | Defer to BOQ productization milestone |
| `#75` | BOQ to contract line mapping | Defer to BOQ productization milestone |
| `#76` | BOQ import wizard enhancement | Defer to BOQ productization milestone |

## Re-entry Rule

A deferred item can enter an active milestone only when all of these are true:

1. It has a named product milestone separate from v1.1 convergence, or it is decomposed into a current convergence issue with explicit acceptance criteria.
2. It has a single owner and a rollback plan.
3. It names required test evidence: unit, Odoo integration, API contract, E2E, migration, or manual evidence.
4. It does not bypass the branch-protected PR flow and required quality gate.

## Evidence

Open issue audit on 2026-07-12 confirms that `#2`, `#4`-`#9`, and `#64`-`#76` are labeled with priority/area/evidence labels and have no v1.1 milestone. This is the intended state for the current release convergence phase.
