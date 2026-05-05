# Construction Material Deproductization Audit

Date: 2026-05-05

## Business Position

Construction-enterprise material management is not production-enterprise product
management.

For this system, materials are project-scoped business facts used for:

- project cost statistics;
- budget and plan comparison;
- procurement, acceptance, inbound, outbound, settlement, and rental business
  processing;
- management control around project facts.

The material library is only an input and reuse convenience. It can be imported
from templates or accumulated from daily business. It is not a product master
and should not drive product-level lifecycle control.

## Target Rule

`sc.material.catalog` is the construction material identity.

`product.product` / `product.template` must not be exposed as the business
identity in construction material workflows. If an Odoo stock/accounting
technical path still requires a product field, that field is a hidden technical
placeholder only and must not become a user-facing management concept.

## Current Product-Concept Exposure

| Area | Current State | Business Risk | Target |
| --- | --- | --- | --- |
| material catalog UI | showed promoted product fields and filters | users may think material library must become product library | removed from construction material catalog views |
| legacy material UI | showed "promote to product" action and promotion state | migration may be interpreted as product-master creation | removed from visible legacy material views |
| material price library | exposed `product_id` | price facts may be attached to product instead of material catalog | removed from visible price form |
| material plan lines | `product_id` is required and visible | planning identity is product-centric | migrate to `material_catalog_id` as visible/required business field |
| purchase/acceptance/inbound/outbound/RFQ/settlement lines | `product_id` is required and visible beside `material_catalog_id` | business users see product as the material identity | make `material_catalog_id` the visible identity; keep product only as technical fallback if still required |
| rental lines | use `product_id` for turnover material | rental management becomes product-centric | add/shift to material catalog identity |
| stock move integration | uses Odoo stock product mechanics | technical stock valuation path can leak product semantics | isolate as optional technical integration, not ordinary construction material management |

## Immediate Changes Made

The first UI cleanup removes the product-promotion concept from construction
material catalog surfaces:

- `views/support/product_extend_views.xml`
  - removed "已提升产品" filter;
  - removed promoted product column/group;
  - removed product field from material price form.
- `views/support/legacy_material_catalog_views.xml`
  - removed "提升为产品" button;
  - removed promotion-state filters/columns/statusbar;
  - removed promoted product group.

These changes do not delete the underlying technical fields yet, because other
flows and tests still reference them. The next step is to migrate business
forms and computations from product identity to material catalog identity.

The legacy backend promotion action has also been disabled. Calling
`action_promote_to_product` now raises a business error that construction
materials must be maintained as material catalog records, not promoted into
products.

Deprecated historical product-link field labels have been renamed to
"历史技术产品/历史技术关联" wording. Field names remain unchanged to avoid schema
churn, but ordinary business labels no longer present them as product
promotion.

## Material Plan Refactor Progress

Material plan is now material-catalog-first:

- `project.material.plan.line` has visible `material_catalog_id`.
- The plan line form/tree uses `material_catalog_id` as the required business
  material field.
- `product_id` remains required by the technical model but is hidden in the
  material plan UI.
- If no product is provided, the line automatically uses
  `SC-SYSTEM-DEFAULT-MATERIAL` as a technical placeholder.
- Plan summaries compute material name/spec/unit from the material catalog and
  material unit text.
- Submit validation checks material catalog presence instead of product
  purchase-unit compatibility.
- Plan-to-RFQ generation carries `material_catalog_id` into RFQ lines and no
  longer rejects construction material units because they differ from a product
  purchase unit.

Validation:

- `smart_construction_core` module upgrade passed on `sc_prod_sim`.
- ORM smoke create with only `material_catalog_id` passed and was rolled back.

## RFQ And Purchase Request Refactor Progress

RFQ and purchase-request entry points now follow the same material-catalog-first
rule:

- Material purchase request line tree uses `material_catalog_id` as the visible
  required material field and hides `product_id`.
- Material RFQ line tree uses `material_catalog_id` as the visible required
  material field and hides `product_id`.
- The shared material line defaulting logic fills `material_spec` from
  `sc.material.catalog` before falling back to the technical product
  placeholder.
- RFQ purchase-order line description uses the material catalog name instead of
  product display name.
- Plan-to-RFQ generation was smoke-tested: the RFQ line retained the source
  material catalog ID and used `SC-SYSTEM-DEFAULT-MATERIAL` only as hidden
  technical product.

## Acceptance, Inbound, Outbound, And Settlement Refactor Progress

验收、入库、出库、结算链路已按同一口径收敛：

- Material acceptance line tree uses `material_catalog_id` as the visible
  required material field and hides `product_id`.
- Material inbound line tree uses `material_catalog_id` as the visible required
  material field and hides `product_id`.
- Material outbound line tree uses `material_catalog_id` as the visible
  required material field and hides `product_id`.
- Material settlement line tree/report uses `material_catalog_id` as the
  visible material field and hides `product_id`.
- Settlement line search groups "按材料" by `material_catalog_id`, not product.
- Acceptance/inbound/outbound/settlement line defaulting fills `material_spec` from
  `sc.material.catalog.spec_model` before using the hidden technical product
  fallback.
- Inbound material-name summary now uses `material_catalog_id.display_name`
  before falling back to product display name.

Validation:

- `smart_construction_core` module upgrade passed on `sc_prod_sim`.
- Acceptance/inbound ORM smoke create with only `material_catalog_id` passed
  and was rolled back:
  acceptance line used `SC-SYSTEM-DEFAULT-MATERIAL` only as the hidden product,
  acceptance-to-inbound propagation retained the same material catalog, and the
  inbound summary showed the material catalog name.

## Rental Refactor Progress

周转材料租赁链路已从产品口径切到材料档案口径：

- Rental plan lines now use visible required `material_catalog_id` and hide
  `product_id`.
- Rental order lines now use visible required `material_catalog_id` and hide
  `product_id`.
- Rental settlement lines now use visible required `material_catalog_id` and
  hide `product_id`.
- Existing business fact text fields (`material_name`, `material_spec`,
  `unit_name`) are preserved and automatically filled from the selected
  material catalog.
- No product placeholder is required for rental lines because this flow does
  not currently depend on Odoo stock product mechanics.

Validation:

- `smart_construction_core` module upgrade passed on `sc_prod_sim`.
- ORM smoke create with only `material_catalog_id` passed and was rolled back:
  rental plan/order/settlement lines retained the material catalog, filled
  material name/spec/unit text from the catalog, and kept amount calculations
  correct.

## Refactor Backlog

1. Stock/Odoo product integration:
   - mark as optional technical integration;
   - keep system-default material/product hidden if unavoidable;
   - prevent reports and menus from grouping business facts by product.

2. SCBS migration:
   - continue using `sc.legacy.scbs.material.map`;
   - require confirmed material catalog mappings before projecting stock-in
     project facts;
   - do not promote SCBS materials into products.

## Release Audit

上线口径审计见：

- `docs/migration_alignment/construction_material_deproductization_release_audit_v1.md`

Current conclusion: Smart Construction material business menus, forms,
grouping, and migration policy are aligned to material catalog identity.
Residual product references are accepted only as hidden technical Odoo
dependencies or historical technical links.
