# Contract Migration Source Inventory v1

Iteration: `ITER-2026-04-13-1838`

Status: `PASS`

Mode: read-only source inventory.

## Scope

This document starts the contract migration line. It inventories the old contract export and the current repository surface for `construction.contract`.

This iteration did not import data, create an importer, change model fields, change views, change menus, or write to the database.

## Source File

| Item | Value |
|---|---|
| Source path | `tmp/raw/contract/contract.csv` |
| Files in source directory | `.gitkeep`, `contract.csv` |
| Row count | 1694 |
| Field count | 146 |

## Current Repository Contract Surface

Primary model:

- `addons/smart_construction_core/models/support/contract_center.py`
- Odoo model: `construction.contract`
- Line model: `construction.contract.line`

Primary views:

- `addons/smart_construction_core/views/core/contract_views.xml`
- `addons/smart_construction_core/views/core/contract_line_search.xml`

Related service and consumption points:

- `addons/smart_construction_core/services/project_dashboard_builders/project_contract_builder.py`
- `addons/smart_construction_core/services/project_overview_service.py`
- `addons/smart_construction_core/services/project_execution_item_projection_service.py`
- `addons/smart_construction_core/services/capability_registry.py`
- `addons/smart_construction_core/services/capability_matrix_service.py`

Menus and actions exist for:

- general project contract action
- my contracts
- income contracts
- expense contracts
- contract lines

This batch did not modify any of these files.

## Source Shape

The export is not a narrow contract master table. It includes:

- contract identity: `Id`, `DJBH`, `HTBH`, `PID`, `f_WBHTBH`
- project relation: `XMID`, `f_XMMC`, `f_XMJC`, `XMBM`
- participant text: `FBF`, `CBF`, `GCJSDW`, `GCJLDWMC`, `f_JSDW`
- contract subject and category: `HTBT`, `HTLX`, `LX`, `f_GCXZ`, `D_SCBSJS_HTJGFS`
- amount fields: `GCYSZJ`, `GCJSZJ`, `YFK`, `ZLBZJ`, `GCYSZJ`, `D_SCBSJS_JSJE`
- dates: `f_HTDLRQ`, `f_GCKGRQ`, `JGRQ`, `LRRQ`, `XGRQ`
- long-text terms: `HTYDFKFS`, `GQSM`, `GCQK`, `GCBGJL`, `GCZDSXJL`
- attachment references: `f_FJ`
- old status/deletion markers: `DJZT`, `DEL`, `IsUpload`, `UploadTime`

## Initial Boundary

Direct import is blocked in this first batch.

The next valid step is a contract mapping dry-run and safe import slice design. It must explicitly handle project relation, partner text matching, dictionary values, tax behavior, amount semantics, line/term text, and rollback identity before any create-only write batch.
