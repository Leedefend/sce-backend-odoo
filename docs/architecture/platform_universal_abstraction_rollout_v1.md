# Platform Universal Abstraction Rollout v1

Status: draft rollout plan

This plan describes how to land the universal framework without destabilizing the current construction backend.

## Current Grounding

The platform kernel is now registered:

```text
platform -> company -> business -> carrier -> fact -> projection
```

The current construction binding is also registered:

```text
carrier_type=project -> project.project
```

This means the platform has an abstraction point for cross-industry business carriers, while the construction backend can keep using `project.project` as its main carrier.

## What To Do Next

Do not add `sc.business` or `sc.business.carrier` immediately.

First run an evidence audit across existing models:

1. Which facts are truly company-level and should not require project?
2. Which facts are pre-carrier or pre-project, such as tender/opportunity?
3. Which facts currently require `project_id` only because the system had no business/carrier abstraction?
4. Which projections would need business-level aggregation before project-level aggregation?
5. Which policies/capabilities should scope by company/business/carrier instead of only project?

Only after this audit should a concrete model be introduced.

## Staged Landing

| stage | goal | expected output |
| --- | --- | --- |
| 1 | freeze vocabulary | universal abstraction registry and construction carrier binding |
| 2 | audit current model fit | list of models that are company-level, pre-carrier, carrier-primary, or derived |
| 3 | decide model need | decision whether platform needs `business`, `business.carrier`, both, or only metadata |
| 4 | add non-invasive fields | optional business/carrier references where evidence proves need |
| 5 | update projections | business-level and carrier-level aggregation registry |
| 6 | migrate workflows | only after read-side and compatibility evidence is stable |

## Candidate Platform Models

These are candidates, not immediate implementation decisions:

| model candidate | purpose | risk |
| --- | --- | --- |
| `sc.business.case` | explicit company-managed business matter before/around carrier | may duplicate project if introduced too early |
| `sc.business.carrier` | generic carrier reference layer that maps business to industry object | may become an unnecessary indirection if all current facts are project-primary |
| `sc.business.fact.mixin` revision | universal fields for company/business/carrier/fact/provenance | may disturb existing industry workflows if applied too broadly |
| registry-only carrier contract | declare carrier metadata without new tables | may be enough for now, but weaker for cross-carrier reports |

## Decision Gate

Introduce a concrete platform business model only if at least one of these is true:

- multiple current fact families need to exist before project creation.
- one business can be carried by multiple projects.
- one project can carry multiple independent businesses that need separate income/expense lifecycle.
- reports need business-level aggregation that cannot be derived cleanly from project alone.
- non-construction industry binding cannot reuse the project carrier without semantic distortion.

If none are true, keep the framework as registry and carrier metadata first.

## Immediate Next Audit

The carrier-fit audit has been landed as:

```text
docs/architecture/platform_universal_carrier_fit_audit_v1.md
```

It classifies the current backend models by universal carrier fit and keeps the
decision gate conservative: do not introduce `sc.business` or
`sc.business.carrier` as tables before a family-level carrier-fit registry proves
which workflows need them.

Completed audit task:

```text
classify current backend models by universal carrier fit
```

The next concrete task should be:

```text
create a carrier-fit registry for model families
```

The registry has been introduced at:

```text
docs/architecture/platform_universal_carrier_fit_registry_v1.json
```

The implementation decision gate has been introduced at:

```text
docs/architecture/platform_universal_scope_decision_gate_v1.json
```

This gate requires backend scope changes to move through registry metadata,
optional scope fields, projection extension, or policy scope extension before a
concrete platform business/carrier model is allowed.

Registry categories:

- platform/company-level
- company identity
- business-level, no carrier yet
- pre-carrier/pre-project
- carrier-primary through `project.project`
- carrier-optional through `project.project`
- derived projection
- legacy evidence
- technical bridge

That registry will decide whether the next code change is a new model, a field
addition, or only registry metadata.
