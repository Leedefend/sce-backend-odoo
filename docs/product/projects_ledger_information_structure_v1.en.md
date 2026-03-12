# Projects Ledger Information Structure v1

## 1. Goal

Upgrade `projects.ledger` from a card collection into a portfolio management ledger.

## 2. Information Hierarchy

### 2.1 Layer 1: Portfolio Overview (new)

- Active projects count
- Warning projects count
- Completed projects count
- Portfolio scale (project count)

This layer appears before project cards for first-glance control visibility.

### 2.2 Layer 2: Project Cards (kept)

Card priority:

- Project name
- Status (localized)
- Owner/manager
- Key amount (`dashboard_invoice_amount`)

Cards use light status tones for high-risk/abnormal signals.

## 3. Status Mapping Examples

- `draft` -> 草稿
- `01_in_progress` / `in_progress` / `open` -> 进行中
- `done` -> 已完成
- `blocked` / `overdue` / `risk` -> 风险
- `cancel` / `cancelled` -> 已取消

## 4. Compatibility

- Card click navigation remains unchanged.
- Underlying action/scene route protocol remains unchanged.
- Changes are display-layer only.
