# Page Shell Guideline v1

## 1. Goal

Unify the product shell language (header, toolbar, content, states) without heavy component migration.

## 2. Scene Header Structure

Recommended order:

1. Main title (business object)
2. Subtitle (scope/filter context/update hint)
3. Status chip (ok/loading/empty/error)
4. Quick actions (reload + primary action)

## 3. Placement Rules

- Subtitle: one-line scope context.
- Description: used mainly in dashboard/workspace.
- Breadcrumb: route-level, avoid repeating in blocks.
- Quick actions: top-right, max 1 primary + 2 secondary.

## 4. Summary Strip (Optional)

- Position: below header, above toolbar.
- Usage: record count, warning count, key amount/progress.
- Applicability: required for dashboard, recommended for workspace, optional for list.

## 5. Search/Filter/Sort/Batch Bar

- Search/filter/sort in toolbar.
- Batch actions near table top, not mixed in header.
- View switch above toolbar (collapsible if needed).

## 6. Main Content Containers

- Page container uses unified grid + gap pattern.
- Clear layering for header/summary/toolbar/content.
- Consistent radius/border/shadow for cards.

## 7. Unified State Expression

- Loading: “loading...” style with retry if needed.
- Empty: business-semantic copy + suggested next action.
- Error: title + trace info + retry.
- Forbidden: capability-focused message, avoid technical internals.

## 8. Minimum Convergence Entry Points (This Round)

### 8.1 Entry points

- List-like pages: `ListPage.vue`.
- Dashboard page: `PageRenderer.vue` + `ProjectManagementDashboardView.vue`.

### 8.2 Target scenes

- `project.management`
- `projects.ledger`
- `projects.list`
- `task.center`
- `risk.center`
- `cost.project_boq`

### 8.3 Convergence method

- Keep underlying contract unchanged.
- Converge via page-mode detection + semantic field mapping.
- Improve readability with summary strips and status signals.
