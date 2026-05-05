# Construction Material Deproductization Release Audit

Date: 2026-05-05

## Release Gate

施工材料业务上线口径：用户办理材料业务时，材料身份必须是
`sc.material.catalog` 或材料事实文本，不是 `product.product`。

`product.product` 只允许出现在以下技术场景：

- Odoo stock/purchase/accounting integration needs a product field.
- Historical compatibility fields preserve old technical links.
- Tests create technical products to exercise Odoo internals.

It must not be the visible construction-material business identity.

## User-Facing Matrix

| Business Area | Visible Material Identity | Product Exposure | Status |
| --- | --- | --- | --- |
| material catalog | `sc.material.catalog` fields | promotion fields removed from views | pass |
| material price library | `material_catalog_id` | `product_id` hidden from views and label downgraded | pass |
| material plan | `material_catalog_id` required | hidden technical placeholder | pass |
| purchase request | `material_catalog_id` required | hidden technical placeholder | pass |
| RFQ | `material_catalog_id` required | hidden technical placeholder | pass |
| acceptance | `material_catalog_id` required | hidden technical placeholder | pass |
| inbound | `material_catalog_id` required; summary uses catalog name | hidden technical placeholder | pass |
| outbound | `material_catalog_id` required | hidden technical placeholder | pass |
| material settlement | `material_catalog_id` required; report groups by catalog | hidden technical placeholder | pass |
| rental plan/order/settlement | `material_catalog_id` required plus material fact text | hidden optional technical field | pass |
| legacy material detail | legacy material fact fields | promotion action disabled | pass |
| Odoo stock moves | standard Odoo product mechanics | technical only | accepted technical dependency |
| Odoo purchase order lines | standard Odoo product mechanics | technical only; description uses material catalog through RFQ | accepted technical dependency |

## Residual Product References

Allowed residual references:

- `SC-SYSTEM-DEFAULT-MATERIAL` hidden technical product.
- Hidden `product_id` fields on material business lines.
- `product.template` extension fields for historical technical links.
- Stock valuation/cost integration through Odoo stock moves.
- Existing tests that verify technical product fallback behavior.

Blocked or removed:

- Material/legacy material promotion UI.
- Backend `action_promote_to_product`; it now raises a business error.
- Product-based material settlement grouping.
- Product-based material entry on plan/purchase/RFQ/acceptance/inbound/outbound/settlement/rental forms.

## Verification Evidence

- Static Python compilation passed for changed material modules.
- XML parsing passed for changed material views.
- `smart_construction_core` upgraded successfully on `sc_prod_sim`.
- Database `ir.ui.view` audit passed for material line/catalog/price/legacy
  material models: 11 loaded tree/form/search views checked, 0 visible
  `product_id` nodes, 0 `product_id` grouping filters.
- Rollback ORM smoke checks passed for:
  - material plan line with only material catalog;
  - plan-to-RFQ material catalog propagation;
  - acceptance-to-inbound material catalog propagation;
  - material settlement with only material catalog;
  - rental plan/order/settlement with only material catalog;
  - legacy material promotion action blocked.
- `git diff --check` passed.

## Remaining Release Risk

The remaining risk is not ordinary construction-material UX. It is technical
integration visibility if a power user enters standard Odoo product, purchase,
or stock menus outside the Smart Construction material menus.

For this release, that is accepted as an Odoo platform dependency. The Smart
Construction material business menus, forms, grouping, and migration policy are
aligned to material catalog identity.
