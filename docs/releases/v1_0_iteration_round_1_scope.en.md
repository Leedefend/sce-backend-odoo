# v1.0 Iteration Round 1 Scope (Product Expression Iteration)

## 1. Goal

This round focuses on product expression refinement on `release/construction-system-v1.0`, not platform architecture expansion.

- Upgrade UX from “internal tooling feel” to “construction management product feel”.
- Improve page mode semantics, information hierarchy, field readability, and demo storytelling.
- Keep all kernel mechanisms stable while improving user-facing clarity.

## 2. Hard Boundaries (No Change)

The following kernel areas are out of scope:

1. Core mechanisms of `scene registry / scene governance / delivery policy`.
2. ACL, record rules, and permission baseline.
3. Main logic of deployment, rollback, and release scripts.
4. Core contract envelope structure.

## 3. Allowed Change Scope

- Page mode semantics and frontend consumption (`dashboard/workspace/list`).
- Page shell structure, header/actions/content strip, state expression.
- Block-level visual priority and semantic copywriting.
- Technical-to-product value mapping (display layer first).
- Demo data completion and a few display-only aggregate fields.

## 4. In-Scope Pages

- `project.management`
- `projects.ledger`
- `projects.list`
- `task.center`
- `risk.center`
- `cost.project_boq`

## 5. Output Standard

- Clear differentiation of page modes.
- Dashboard highlights KPI/risk/progress first.
- Ledger emphasizes project-portfolio overview before project cards.
- List pages feel like management ledgers, not raw database tables.
- Core pages avoid direct technical values (`draft`, `done`, `No`).

## 6. Validation & Release Strategy

- Do not release immediately after this round.
- Run product expression validation first.
- Then run minimum regression:
  - `make verify.frontend.build`
  - `make verify.frontend.typecheck.strict`
  - `make verify.project.dashboard.contract`
  - `make verify.phase_next.evidence.bundle`

## 7. Risks & Controls

- Risk: display-layer changes may affect local visual consistency.
- Control: keep contract-stable changes only and preserve verify mainline.
