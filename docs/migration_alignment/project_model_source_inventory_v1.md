# Project Model Source Inventory v1

## Scope

- Task: `ITER-2026-04-13-1816`
- Legacy input: `tmp/raw/project/project.csv`
- Target model: `project.project`
- Target addon: `addons/smart_construction_core`

This inventory is limited to project model alignment. It does not change menus,
data import jobs, contract/payment/supplier models, ACLs, record rules, or
manifests.

## Model Sources

| Source | Role | Notes |
| --- | --- | --- |
| `addons/smart_construction_core/models/core/project_core.py` | Main `project.project` extension | Owns project business facts, lifecycle fields, stage sync helpers, project metrics, related action helpers. |
| `addons/smart_construction_core/models/core/project_project_financial.py` | Financial projection extension | Out of this batch. Read as context only because financial semantics are not part of first-round project import alignment. |
| `addons/smart_construction_core/models/core/project_dashboard.py` | Dashboard extension | Out of this batch. It adds presentation/support facts for dashboards, not legacy import identity fields. |
| `addons/smart_construction_core/models/support/project_extend_boq.py` | BOQ support extension | Out of this batch. It depends on project but is not project master-data alignment. |
| `addons/smart_construction_demo/models/project_demo_cockpit_seed.py` | Demo-only extension | Out of this batch. Demo seed behavior is not a source for import schema. |

## View Sources

| Source | Role | Notes |
| --- | --- | --- |
| `addons/smart_construction_core/views/core/project_views.xml` | Main inherited form and create views | First-round new fields are displayed in the existing construction tab under import identity, stage/region, participants, and text facts groups. |
| `addons/smart_construction_core/views/core/project_list_views.xml` | Project list view | Read-only inventory context. Not changed because this batch only requires form display. |
| `addons/smart_construction_core/views/core/project_search_views.xml` | Project search view | Read-only inventory context. Not changed to avoid expanding search behavior. |
| `addons/smart_construction_core/views/core/project_lifecycle_kanban_views.xml` | Project lifecycle kanban | Read-only inventory context. Not changed in this batch. |

## Import-Adjacent Sources

| Source | Role | Notes |
| --- | --- | --- |
| `addons/smart_construction_core/wizard/project_boq_import_wizard.py` | BOQ import wizard | Out of scope. It imports BOQ data, not project master data. |
| `addons/smart_construction_core/wizard/project_quick_create_wizard.py` | Quick project creation wizard | Read-only context. No import or field expansion is added here. |
| `addons/smart_construction_custom/data/customer_project_seed.xml` | Customer project seed | Out of scope for this batch. No legacy data import is performed. |
| `addons/smart_construction_demo/data/base/20_projects.xml` | Demo project seed | Out of scope. Demo data is not used as migration truth. |

## Ownership Decision

- Layer Target: Odoo Domain Model + Native View
- Module Owner: `smart_construction_core`
- Kernel or Scenario: scenario
- Backend sub-layer: business-fact layer
- Reason: legacy project CSV fields are project facts required for later import identity and mapping. They are not platform kernel mechanisms, scene orchestration semantics, or frontend-specific structures.
