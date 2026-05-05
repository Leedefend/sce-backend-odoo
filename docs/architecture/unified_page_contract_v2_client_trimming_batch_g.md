# Unified Page Contract v2+ Client Trimming Batch-G

Date: 2026-05-01
Status: Batch-G implementation note

## Layer Target

Contract Governance / Client Trimming

## Module

- `addons/smart_core/core/unified_page_contract_v2_client.py`
- `docs/architecture/unified_page_contract_v2/snapshots/client_trimming_snapshot_v1.json`
- `scripts/verify/unified_page_contract_v2_client_guard.py`
- `Makefile`

## Reason

v2+ must support multiple terminals without creating different business semantics. Client trimming is allowed to change layout density, adapter selection, and mobile presentation hints. It must never change permissions, action IDs, field IDs, data keys, or business meaning.

## Stable Clients

- `web_pc`
- `wx_mini`
- `harmony_h5`

## Reserved Clients

- `mobile_app`

`mobile_app` remains a reserved extension slot in this batch. If requested, it defaults to `web_pc` instead of becoming a stable protocol value.

## Trimming Policy

| Client | Policy |
| --- | --- |
| `web_pc` | `adaptMode=pc`, 12 columns, full component registry, selected web adapter. |
| `wx_mini` | `adaptMode=mobile`, single column, compact density, selected mini-program adapter, mobile full-width widget hint. |
| `harmony_h5` | `adaptMode=mobile`, single column, compact density, selected H5 adapter, mobile full-width widget hint. |

## Terminal Delivery Profiles

Batch-G keeps `full` as the semantic verification profile. Cross-client drift guards still run on `full`, so v2 field IDs, action IDs, selectors, data keys, and page identity remain stable.

Mobile terminals now default to `mobile_compact` for actual delivery:

- page/layout delivery keeps only the first mobile-relevant containers and widgets (`12` widgets by default);
- action delivery keeps only the first high-priority executable rules (`4` actions by default);
- navigation delivery keeps a shallow, bounded menu tree (`8` items and `2` levels by default);
- `meta.compat` is replaced with source fingerprints for compact delivery, so mobile clients do not receive the full legacy/source payload by accident;
- every compact response reports `meta.deliveryTrim.original/delivered/omitted/limits`.

This is a delivery cut only. The platform source of truth stays Unified Page Contract v2, and industry modules may contribute menus/scenes/actions but must not define a separate mobile protocol.

## Semantic Invariants

The guard asserts stability across all stable clients for:

- `pageId`
- `sceneKey`
- `containerId`
- `widgetId`
- `fieldCode`
- `componentKey`
- `actionId`
- `dataKey`
- `selector`

## Upgrade Assessment

No Odoo model field, view, security, data XML, cron, or manifest dependency is added.

Result:

- `-u smart_core`: not required for this batch.
- service restart: not required for static validation; required only if a live Odoo worker must import the new module without process reload.

## Verification

Primary restricted target:

```bash
make verify.unified_page_contract.v2
```

Client-only target:

```bash
make verify.unified_page_contract.v2.client
```

## Rollback

Revert:

- `addons/smart_core/core/unified_page_contract_v2_client.py`
- `scripts/verify/unified_page_contract_v2_client_guard.py`
- `docs/architecture/unified_page_contract_v2/snapshots/client_trimming_snapshot_v1.json`
- `Makefile` client target changes

No database rollback is required.
