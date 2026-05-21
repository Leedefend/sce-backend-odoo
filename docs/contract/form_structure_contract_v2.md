# Form Structure Contract v2

## Purpose

`formStructureContract` is the v2 form-page structure contract. It sits between
raw business facts and `layoutContract.containerTree`.

Business models and Odoo native views may be inconsistent. The contract layer
normalizes those inputs into one product-level form structure before the web
client renders the page.

## Responsibility Boundaries

### Fact Layer

Sources:

- Odoo model fields and field metadata.
- Odoo native form XML layout.
- `ui.form.field.policy` overlays.
- Business object policies and governance outputs.
- Runtime access, status, action and data facts.

The fact layer owns facts only. It may expose inconsistent field names, view
groups, pages, legacy fields, projection fields and relation fields.

### Form Structure Contract Layer

`formStructureContract` owns form-page structure:

- Stable structure slots.
- Slot/group labels.
- Field references inside slots.
- Readonly/collapsible/priority hints.
- Source authority metadata.

It must not create business facts. It only arranges facts that already exist.

### V2 Projection Layer

The v2 assembler projects `formStructureContract` into
`layoutContract.containerTree`. It also keeps `formStructureContract` on the v2
snapshot so clients and audits can inspect the normalized structure source.

### Frontend Layer

The frontend renders v2 contracts. It should not infer business semantics from
model names, field names, or Chinese titles.

## Contract Shape

```json
{
  "source": "ui.contract.v2.form_structure_contract",
  "structureVersion": "1.0",
  "model": "example.model",
  "viewType": "form",
  "mode": "business_task_form",
  "layoutPolicy": "overview_then_task_slots",
  "objectProfile": {
    "model": "example.model",
    "kind": "business_form",
    "factAuthority": "business_object_model_and_view"
  },
  "navigation": {
    "title": "业务办理"
  },
  "fieldRoles": {
    "name": {
      "role": "identity",
      "slot": "primary_facts",
      "group": "identity"
    },
    "state": {
      "role": "status_or_date",
      "slot": "amount_progress",
      "group": "status_dates"
    }
  },
  "slots": [
    {
      "slot": "overview",
      "title": "办理总览",
      "role": "overview",
      "readonly": true,
      "fieldRefs": ["name", "state"]
    },
    {
      "slot": "primary_facts",
      "title": "主业务事实",
      "role": "facts",
      "groups": [
        {
          "name": "identity",
          "title": "业务识别",
          "role": "identity",
          "fieldRefs": ["name"]
        }
      ]
    }
  ],
  "sourceAuthority": {
    "kind": "unified_page_contract_v2",
    "runtime_carrier": "ui.contract.v2.form_structure_contract",
    "projection_only": true,
    "no_business_fact_authority": true,
    "governed_form_structure": true,
    "governance_source": {
      "source": "business_view_orchestration",
      "owner_layer": "business_view_orchestration"
    }
  }
}
```

## Standard Slots

- `overview`: first-screen summary, usually readonly.
- `primary_facts`: identity, relations, terms and other core facts.
- `amount_progress`: amount, status and date/progress facts.
- `collaboration`: approval, remarks and attachments.
- `details_source`: x2many details and provenance/source fields.

Business domains may change labels through object profiles, but slot keys remain
stable so the product structure stays consistent.

## Projection Metadata

When projected to `layoutContract.containerTree`, slot and group containers keep
their structural identity:

- Page containers receive `formStructure.slot` and `formStructure.role`.
- Group containers receive `formStructure.slot`, `formStructure.group` and
  `formStructure.role`.
- Field nodes may receive `formStructureRole`, copied from `fieldRoles`.

This lets audits and future renderers reason from contract roles instead of
Chinese titles or model-specific field names.

## Runtime Guard Rules

The v2 runtime guard validates the structure contract as a global contract, not
as a frontend convention:

- `source` must be `ui.contract.v2.form_structure_contract`.
- `slots` must exist and slot keys must be unique.
- `fieldRefs` must reference known contract fields.
- `sourceAuthority.governed_form_structure` must be `true`.
- `sourceAuthority.governance_source` must identify the governance source.
- A field may appear in the task structure only once. A readonly overview
  summary may reference the same field once.
- `fieldRoles.*.slot` must reference a declared slot.
- Referenced fields must be projected into `layoutContract.containerTree`.

These checks keep business-object differences in the fact layer while ensuring
the product-level form structure remains coherent after v2 projection.

## Non-Goals

- Do not make Odoo XML views globally consistent by hand.
- Do not let one model family, such as contracts, define global form structure.
- Do not let frontend components infer form-page business semantics.
- Do not generate `formStructureContract` directly from all readable fields,
  broad `visible_fields`, or ungoverned native layout snapshots.
