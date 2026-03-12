# List Pages Convergence v1

Target pages: `task.center`, `risk.center`, `cost.project_boq`.

## 1. Unified Elements

1. Unified top info layer:
   - page title
   - page mode tag
   - record count
   - status label
2. Unified toolbar: search / filter / sort
3. Unified batch bar: selected count / batch actions / export
4. Unified status column: localized text + semantic tone badge
5. Unified amount and percentage rendering (`万/亿`, `%`)

## 2. Preserved Differences

- `task.center`: action rhythm (in-progress/overdue/done).
- `risk.center`: severity and warning emphasis.
- `cost.project_boq`: quantity and amount readability.

## 3. Implementation Strategy

- Keep underlying list contract unchanged.
- Use `ListPage` as common shell carrier.
- Let `ActionView` provide scene-aware page mode and context.
- Preserve existing search/filter/sort behavior.
