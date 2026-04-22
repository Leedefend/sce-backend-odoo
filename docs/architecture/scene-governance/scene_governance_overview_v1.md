# Backend Scene Governance Overview v1

## 1. Background

The repository already has working backend scenification, but the operating
chain historically accumulated multiple overlapping sources:

- scene registry
- providers
- capability entry payloads
- menu/action facts
- runtime bootstrap assembly

That means the system can run, but without explicit governance it tends to
drift in three places:

- scene authority
- canonical entry semantics
- compatibility/fallback interpretation

## 2. Current Stage Judgment

### 2.1 What Already Exists

- scene-ready contract delivery already exists
- scene registry / provider / menu interpreter / runtime bootstrap already run
- frontend already consumes scene-ready delivery rather than raw native facts
- authority, canonical-entry, menu-mapping, and task-family compat-gap guards
  already exist in first form

### 2.2 What Was Missing Before This Package

- one formal directory for backend scene governance
- one overview that explains why normalization is now the priority
- one stable vocabulary for authority, family, failure, and verify rules
- one structured asset area for inventories/matrices/codes

## 3. Why Governance Is Needed Now

The system has already crossed from "few scenes, many guesses" into:

> many scenes, many compat paths, and multiple runtime delivery surfaces

At this stage the main risk is no longer inability to add features. The main
risk is semantic drift:

- registry and capability payload say different things
- canonical entry is inferred instead of frozen
- menu/action compatibility starts acting like identity authority
- runtime chain remains correct only by historical memory

## 4. Current-Round Governance Goal

This governance set exists to freeze:

- authority hierarchy
- entry semantics
- system.init runtime chain boundaries
- family-level governance model
- failure model
- verify guard specification

## 5. What This Round Does Not Do

- does not physically split `system_init.py`
- does not migrate every scene in one pass
- does not add a new abstraction layer over the current runtime chain
- does not change frontend primary consumption mode

## 6. Output of This Governance Package

This package provides:

- 1 overview document
- 3 primary governance specs
- 2 supporting governance specs
- 1 verify spec
- 3 structured asset templates

## 7. Execution Principles

- freeze rules before deeper refactor
- govern by family rather than by isolated scene
- lock verify before broad migration
- keep frontend as semantic consumer rather than semantic guesser
