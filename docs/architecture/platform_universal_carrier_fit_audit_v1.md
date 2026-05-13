# Platform Universal Carrier Fit Audit v1

Status: evidence audit

This audit grounds the platform abstraction in the current backend model set.
It answers whether the existing construction backend already proves a need for
new platform tables such as `sc.business` or `sc.business.carrier`.

## Kernel Question

The platform abstraction is:

```text
platform -> company -> business -> carrier -> fact -> projection
```

The current construction binding is:

```text
carrier_type=project -> project.project
```

The audit question is not "how many project models exist". The question is
which backend models are platform/company concepts, which are business concepts
before carrier, which are truly project-carried facts, and which are derived or
historical evidence.

## Carrier Fit Counts

Static audit date: 2026-05-13.

| carrier fit | count | meaning |
| --- | ---: | --- |
| platform_company_level | 33 | platform, company, policy, approval, subscription, capability, and governance objects |
| company_identity | 8 | partner, counterparty, product, material identity objects |
| business_level_no_carrier | 1 | business object currently forced through project because no business/carrier abstraction exists |
| pre_carrier_pre_project | 7 | pre-carrier business records, mostly tender child facts |
| carrier_primary_project | 91 | facts whose operational lifecycle is project-carried in construction |
| carrier_optional_project | 45 | facts that can attach to project but are not platform-kernel project concepts |
| derived_projection | 18 | read models, summaries, ledgers, cockpit/workbench visibility |
| legacy_evidence | 51 | replay and historical source carriers |
| technical_bridge | 9 | native extensions, compatibility mixins, and bridge models |

Additional field evidence:

- project_required_model_count: 66
- project_optional_model_count: 98
- universal_carrier_fit_review_count: 0
- universal_carrier_fit_unclassified_count: 0

## What The Models Solve

Platform/company-level models solve platform operation and tenant governance:
company identity, role/policy, workflow dictionaries, subscriptions,
entitlements, scene capability, and audit/validation.

Company identity models solve reusable master data: partner, counterparty,
bank, supplier type, product, material catalog, and material price. They should
not become project facts.

Business-level and pre-carrier models solve work that exists before or outside a
confirmed construction project. The current hard evidence is `tender.bid`: it is
a business opportunity/tender record but currently requires `project_id`. Its
child models carry tender details and are classified as pre-carrier/pre-project.

Carrier-primary project models solve construction execution: contract,
settlement, payment, receipt, invoice, tax, material, labor, equipment,
subcontract, quality, safety, risk, progress, diary, BOQ, budget, cost, and
project structure. In construction, `project.project` is the dominant carrier.

Carrier-optional project models solve company or operational objects that may
be anchored to a project but should not define the platform kernel. Examples
include fund accounts, document/admin/payroll records, optional project
attachments, and price tables.

Derived projection models solve visibility and aggregation. They should not own
business truth; they read from facts and are refreshed by their registered
implementation mode.

Legacy evidence models solve historical replay and traceability. They are input
evidence, not target business ownership.

Technical bridge models solve compatibility with native Odoo models and shared
mixins. They are not business facts.

## Boundary Findings

The existing backend is reasonable for a construction-first system because most
runtime facts are project-carried. The architecture is not yet sufficient as a
cross-industry platform because at least one business object (`tender.bid`) is
currently forced to require `project_id` before the universal carrier boundary is
explicit.

The current boundary is:

- platform manages companies, policies, capabilities, and shared identity.
- company manages businesses.
- construction business is currently mostly carried by projects.
- project is an industry carrier, not the platform kernel.
- projections are visibility, not source-of-truth.
- legacy models are evidence, not runtime ownership.

## Decision

Do not introduce `sc.business` or `sc.business.carrier` as tables yet.

The evidence supports the universal vocabulary and carrier registry now, but it
does not yet justify a broad schema migration. The next implementation should be
non-invasive:

1. keep the platform kernel and construction project carrier binding in the
   registry.
2. mark `tender.bid` as the first explicit business-level/no-carrier pressure
   point.
3. define carrier metadata for model families before adding new relational
   fields.
4. only add optional business/carrier fields where a workflow proves that a
   business can exist before project, span multiple projects, or require
   business-level reporting independent of project.

## Next Step

The carrier-fit registry is maintained at:

```text
docs/architecture/platform_universal_carrier_fit_registry_v1.json
```

It records this gate for every model family:

```text
family -> carrier_fit -> current_binding -> future_platform_pressure
```

That registry is the gate before any new platform business model is introduced.
