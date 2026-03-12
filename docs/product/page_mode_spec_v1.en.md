# Page Mode Specification v1

## 1. Purpose

Define explicit page semantics so core scenes are no longer rendered as a single “generic page” style. This spec defines `dashboard`, `workspace`, and `list`.

## 2. Page Modes

### 2.1 `dashboard`

- Product goal: answer “health, risks, next actions” within 10 seconds.
- Shell:
  1) Scene Header (title/context/actions)
  2) Optional Summary Strip
  3) Main zones (KPI/risk/progress/thematic blocks)
- Typical structure: KPI cards, high-priority risk alerts, progress summary, and supporting finance/cost/contract blocks.

### 2.2 `workspace`

- Product goal: support continuous role-based operations in one business domain.
- Shell:
  1) Scene Header
  2) Action strip (search/filter/quick actions)
  3) Main working area (list/cards/grouping)
- Typical structure: actionable records, readable status hierarchy, and batch operations.

### 2.3 `list`

- Product goal: stable ledger-style browse/filter/sort/batch process.
- Shell:
  1) Scene Header (title/record count/reload)
  2) Table Toolbar (search/filter/sort)
  3) List area (key columns first, readable status)
- Typical structure: identifier columns, business metrics, batch actions/export.

## 3. Core Scene Classification

- `project.management` -> `dashboard`
- `my_work.workspace` -> `workspace`
- `risk.center` -> `workspace`
- `projects.ledger` -> `workspace` (dashboard-like overview layer)
- `projects.list` / `task.center` / `cost.project_boq` -> `list`

Note: `projects.ledger` is currently card-driven and should prioritize portfolio-level summary before project-level drilldown.

## 4. Frontend Consumption

### 4.1 Existing semantic source

Use `Scene.layout.kind` as the minimal current source:

- `layout.kind=ledger|workspace` -> `workspace`
- `layout.kind=list` -> `list`
- `project.management` is forced to `dashboard`

### 4.2 Minimum integration this round

1. Add a frontend page-mode normalization helper.
2. Let `ProjectManagementDashboardView` and `ActionView/ListPage` consume it.
3. Use page mode for:
   - Header semantics
   - Summary Strip visibility
   - Toolbar style and information priority
4. Keep scene registry and contract envelope unchanged.

## 5. Future (Out of this round)

- Add explicit `page_mode` to scene payload `page` node.
- Extend page contract with mode-specific render hints.
- Include mode clarity as regression checklist item.
