# Page Mode Specification v1

## 1. Purpose

Define explicit page semantics so product pages are not rendered as one generic surface. This spec follows `docs/product/product_page_structure_design_v1.md`: page mode describes product task intent, not route shape, component choice, or layout kind.

The canonical page modes are:

| Mode | Product Goal | Typical Pages |
| --- | --- | --- |
| `dashboard` | Understand status, risk, and next actions within 10 seconds | role homepage, project cockpit, executive analytics |
| `workspace` | Continue work inside one business domain | my work, risk center, config workbench, project ledger workspace |
| `list` | Browse, filter, sort, and batch-handle records efficiently | contract ledger, task list, business master data |
| `form` | Capture, approve, save, or submit one business document | contract handling, payment request, project initiation |
| `detail` | Read one object's details, status, history, and relations | project detail, contract detail, attachment detail |
| `admin` | Configure rules, inspect release state, and support rollback | menu config, config center, release management |

## 2. Mode Boundaries

### 2.1 `dashboard`

- Goal: answer “what is happening, where are risks, what next” quickly.
- Shell: Page Header + Summary Strip + section cards.
- Must not host continuous editing or system configuration actions.

### 2.2 `workspace`

- Goal: support continuous role-based operations in one business domain.
- Shell: Page Header + scope actions + working area.
- `layout.kind=ledger` only describes the internal layout; it is not a page mode. The page mode remains `workspace`.

### 2.3 `list`

- Goal: stable ledger-style browse, filter, sort, and batch handling.
- Shell: Page Header + Toolbar + Table + Pagination.
- Batch actions stay near the selected list rows, not in the Header.

### 2.4 `form`

- Goal: complete business capture, approval, save, or submit.
- Shell: Page Header + status/primary action + form sections.
- Configuration actions must not leak into business runtime forms.

### 2.5 `detail`

- Goal: read one object's details, status, history, and related information.
- Shell: Page Header + Summary + Tabs/Sections.
- Must not carry batch management or system configuration responsibilities.

### 2.6 `admin`

- Goal: configure system rules, inspect release results, and support rollback.
- Shell: Page Header + management tools + auditable main content.
- Actions must name the configured object, for example “Save menu configuration”, not generic “Save”.

## 3. Core Scene Classification

- `project.management` -> `dashboard`
- `my_work.workspace` -> `workspace`
- `risk.center` -> `workspace`
- `projects.ledger` -> `workspace`; `layout.kind=ledger` only drives the project portfolio ledger layout and overview strip.
- `projects.list` / `task.center` / `cost.project_boq` -> `list`
- Contract handling, payment request, project initiation -> `form`
- Single-object pages -> `detail`
- Menu config, config center, release management -> `admin`

## 4. Frontend Consumption

### 4.1 Normalization

The frontend uses `resolvePageMode(sceneKey, layoutKind)`:

- `project.management` / `projects.dashboard` -> `dashboard`
- `layout.kind=list` -> `list`
- `layout.kind=ledger|workspace` -> `workspace`
- default -> `workspace`

The canonical frontend allowlist is exported as `PAGE_MODES` from `frontend/apps/web/src/app/pageMode.ts`, and `PageMode` must be derived from `PAGE_MODES[number]`. Static guards read this constant instead of maintaining a separate mode list.

`ledger` must not be returned as `PageMode`. When project ledger needs special visuals, read `layout.kind=ledger` instead of extending page mode.

### 4.2 DOM Evidence

Production pages must expose `data-product-page-mode` in runtime DOM. Allowed values:

```text
dashboard / workspace / list / form / detail / admin
```

This is guarded by `make verify.product.page_structure` and config workbench browser acceptance.

## 5. Future

- Add explicit `page_mode` to scene payload page nodes.
- Extend page contracts with mode-specific render hints.
- Use page mode as shared input for structure, operation, and professional-readiness acceptance.
