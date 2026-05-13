# Platform Universal Business Abstraction v1

Status: draft architecture contract

Binding registry: `platform_universal_business_abstraction_registry_v1.json`
Rollout plan: `platform_universal_abstraction_rollout_v1.md`
Scope decision gate: `platform_universal_scope_decision_gate_v1.json`
Optional scope metadata: `platform_universal_optional_scope_metadata_v1.json`

This note separates the platform-level abstraction from the construction-industry binding.

The purpose of the abstraction is cross-industry and cross-company applicability. It is not a repair model for one customer's data and it is not limited to construction projects.

## Platform Kernel

The platform-level kernel is:

```text
platform -> company -> business -> carrier -> fact -> projection
```

| concept | platform meaning | should be industry-specific? |
| --- | --- | --- |
| platform | product/runtime that manages tenants, companies, capabilities, policies, integrations, scenes, subscriptions, and audit | no |
| company | managed organization that owns users, permissions, accounting boundary, and operating responsibility | no |
| business | company-managed economic activity or operating matter | no |
| business direction | economic direction such as income, expense, bilateral/mixed, governance, or neutral | mostly no |
| carrier | industry-specific object that carries business execution | yes |
| fact | dated, attributable occurrence or state change inside a business | no, but fact types are industry-specific |
| projection | derived management visibility over facts | no, but metrics are industry-specific |

The platform should therefore standardize company, business, direction, carrier, fact, provenance, policy, projection, and capability contracts.

It should not standardize construction project semantics as universal platform truth.

## Binding Registry

The abstraction is now backed by a machine-checked registry:

- platform kernel concepts: platform, company, business, business direction, carrier, fact, projection, policy
- construction carrier binding: `project.project` as carrier type `project`

The registry intentionally binds construction to project without promoting project into the platform kernel.

## Project Is Not Platform Kernel

Project is not a platform-level mandatory object.

Project is an industry carrier pattern. It is dominant in construction, common in engineering and services, optional in trading or retail, and may be replaced by order, policy, case, shipment, asset, loan, claim, production batch, store, contract, or service ticket in other industries.

The universal abstraction should say:

```text
business has one or more carriers
carrier type is industry-defined
project is one construction carrier type
```

This means `project.project` can remain the construction module's main carrier, but platform-level business logic should not require every industry to use project as the carrier.

## Industry Carrier

An industry carrier is the concrete object that lets a company operate, execute, and measure business.

Examples:

| industry | likely carrier |
| --- | --- |
| construction | project |
| professional service | engagement / project / case |
| retail | store / order / campaign |
| manufacturing | production order / batch / work order |
| logistics | shipment / route / warehouse operation |
| finance | account / loan / policy / claim |
| healthcare | episode / case / appointment |

The platform can define the carrier contract:

- carrier belongs to company-managed business
- carrier has lifecycle
- carrier scopes facts, permissions, tasks, documents, and projections
- carrier can be absent for company-level or pre-carrier facts

The platform should not define the carrier's industry semantics.

## Construction Binding

For the current construction backend, the binding is:

```text
platform -> company -> business -> construction project -> construction facts -> projections
```

Construction-specific facts include:

- tender and income contract
- expense/general/procurement contract
- payment request and execution
- receipt, invoice, and tax evidence
- treasury reconciliation and ledger
- material, labor, equipment, and subcontract lifecycle
- progress, quality, safety, risk, and diary
- BOQ, budget, cost period, and settlement

These are valid industry concepts, not platform kernel concepts.

## Consequence For Current Models

The current audit should be read in two layers:

1. Platform universal layer:
   - company
   - business
   - direction
   - carrier
   - fact
   - projection
   - policy/capability/governance

2. Construction industry binding:
   - project as the primary carrier
   - construction contracts
   - construction cost, material, labor, equipment, subcontract, safety, quality, progress, diary, treasury

The existing `platform -> company -> business -> project` hierarchy is therefore a construction binding of the universal form, not the universal form itself.

## Design Rule

Before promoting a model or field to platform level, it must pass this test:

1. Can the concept apply to more than one industry without construction vocabulary?
2. Can the concept work when the business carrier is not a project?
3. Does the concept describe company, business, direction, carrier, fact, projection, policy, or capability?
4. Is the implementation independent from one customer's historical data shape?

If the answer is no, keep it in the industry layer or customer/replay layer.

## Next Backend Implication

The next design question is whether to introduce a platform-level `business` or `business carrier` abstraction.

Do not add it immediately just because the concept exists. First verify whether current construction models only need a declared carrier contract around `project.project`, or whether multiple facts already need to belong to business before a project exists.

Likely staged path:

1. define platform vocabulary and registry first.
2. map construction `project.project` as carrier type `project`.
3. identify pre-project and company-level facts that cannot cleanly use `project_id`.
4. only then introduce a concrete platform model such as `sc.business.case` or `sc.business.carrier` if the evidence shows it is needed.

The first two steps are now in place as architecture contracts. The carrier-fit
audit and decision gate now add the next constraint: schema changes must follow
this order unless evidence proves otherwise:

1. registry metadata only.
2. optional scope fields.
3. projection extension.
4. policy scope extension.
5. concrete business model.
6. concrete carrier model.

The current high-pressure family is income contract and tender business, with
`tender.bid` as the pressure model. The recommended next implementation is
optional scope metadata design, not a required platform table.

The optional scope metadata contract records the first candidate on `tender.bid`.
It keeps `project_id` authoritative for the current construction workflow and
allows future business/carrier metadata to remain empty until runtime probes
prove the scope is safe.

## Platform Core Gap

The current platform core gap is real: without an industry module, the platform
must still answer which companies can use it and what platform capabilities are
enabled for those companies.

The first core fill is company access in `smart_core`: `sc.subscription.plan`,
`sc.subscription`, `sc.entitlement`, `sc.usage.counter`, and `sc.ops.job`.

The second core fill is `sc.business.scope.mixin` in `smart_core`. This moves
the cross-industry scope language into platform core while keeping construction
carrier semantics in the construction module.

This is deliberately smaller than adding `sc.business` as a table. The platform
now owns company usability and the vocabulary; it does not yet own the business
lifecycle.
