# Backend Business Model Audit Findings v1

Status: draft architecture finding

This finding summarizes the backend business model audit after the model inventory, family registry, business-object hierarchy, and ownership specs were added.

## Core Answer

The backend model target is not to process one customer's historical data.

The target is to support construction-enterprise management:

```text
company manages business
business splits into income and expense
project is the typical construction execution carrier
```

Customer-specific historical data is still important, but it belongs in replay, evidence, mapping, and acceptance layers. It must not define the core industry model hierarchy.

## What The Model Layer Solves

| layer | problem solved | current verdict |
| --- | --- | --- |
| platform | company, users, roles, capability, scene, pack, approval, dictionary, audit, compatibility hooks | reasonable and mostly clear |
| industry | construction business facts: contract, tender, payment, receipt, invoice, tax, treasury, material, labor, equipment, subcontract, progress, quality, safety, diary, cost | reasonable, with overlap risks now declared |
| project carrier | execution container where income, expense, progress, cost, quality, safety, and treasury meet | reasonable; project is central but not root |
| projection | management visibility: summaries, ledgers, cockpit, workbench, reports | reasonable if kept rebuildable |
| legacy/customer | source-fidelity history and migration evidence | reasonable only as replay/evidence, not workflow ownership |

## Is The Current Shape Reasonable?

Yes, directionally.

The model count is not the issue. The current backend has 263 detected model classes, not "only 10 models". The 10 count is only the strict formal legacy-to-runtime fact set.

The shape is reasonable because:

- native Odoo remains the root for company, partner, project, product, account, stock, purchase, users, groups, settings, and approval hooks.
- custom models are used where construction has first-class business documents that native Odoo does not own.
- legacy models are separated from formal runtime documents.
- projections are recognized as derived management views rather than primary facts.

The shape is not fully clean yet because several families grew through product iteration, migration repair, and visible-surface patches. The audit now makes those risks explicit instead of silently accepting them.

## Responsibility Clarity

The responsibility model is now clear enough to govern future iteration, but not yet fully refactored.

Clear boundaries:

- native identity and transaction roots stay native.
- industry source-of-truth documents own construction-specific facts.
- projection/read models are rebuildable and should not receive primary workflow writes.
- legacy carriers preserve source evidence and should not become normal user workflow tables.
- platform governance controls capability, scene, approval, installability, validation, and audit.

Declared overlap risks:

- contract ownership split
- treasury account/reconciliation/ledger split
- product/material catalog split
- payment request/execution split
- projection refresh ownership

These overlap areas are acceptable only under the ownership specs in `backend_business_model_ownership_specs_v1.json`.

## Native Vs Custom Boundary

Use native models when the problem is identity, accounting, stock, purchase, project root, users, groups, company, or approval infrastructure.

Use custom industry models when the problem is a reusable construction business document or workflow.

Use projection models when the problem is management visibility over upstream facts.

Use legacy/customer models only when the problem is preserving old-system evidence, replaying historical facts, or documenting migration acceptance.

Do not add core model fields for one customer's vocabulary, one source table accident, or one acceptance repair unless the concept is promoted through the family registry and ownership specs.

## Enforcement Now In Place

`make verify.backend_business_fact.model_standard` now checks:

- all strict formal runtime facts are registered.
- formal fact standard gaps are either fixed or declared.
- registry scripts/probes exist.
- family registry entries have valid solution layer, responsibility, business object, target problem, and representative models.
- ownership specs have valid fact sources, support models, projections, boundary rules, and decisions.
- every detected backend model class is mapped to one model family.

Current enforced coverage:

- model classes: 263
- model families: 19
- unclassified models: 0
- ownership specs: 5
- formal fact models: 10
- undeclared standard gaps: 0

## Next Refactor Sequence

Do not start with broad model deletion or merging.

Start with ownership convergence in the overlap areas:

1. Contract: declare whether each field belongs to income commitment, expense commitment, general/procurement commitment, or reconciliation.
2. Treasury: keep account master, reconciliation document, and ledger separate.
3. Material: keep product identity native and material catalog as construction surface.
4. Payment: keep request/approval, claim, and actual execution separate.
5. Projection: replace append-only projection scripts with a typed refresh registry.

Only after those boundaries hold should we extract mixins or merge duplicated implementation patterns.

## Final Verdict

The current model architecture is directionally reasonable and now governable.

It is not yet fully clean because overlapping families still need code-level convergence. But the audit has moved the system from implicit accumulated patches to explicit architecture contracts:

- business-object hierarchy
- model family registry
- formal fact registry
- ownership specs
- static enforcement

That is enough to continue backend iteration without letting customer-specific historical repair redefine the product model.
