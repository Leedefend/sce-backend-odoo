# Scene Authority Hierarchy v1

## 1. Goal

Define the single authority source for scene identity, scene content, canonical
entry, and compatibility interpretation.

## 2. Core Principles

- scene identity must have one authoritative owner
- scene content must have a clear owner
- canonical entry may only be defined by authority layers
- compatibility facts must not redefine identity
- frontend must not infer authority

## 3. Authority Matrix

| Topic | Primary authority | Secondary source | Forbidden authority |
|---|---|---|---|
| scene identity | scene registry | none | provider / capability / frontend |
| scene content | provider | merge policy | frontend inference |
| canonical entry | registry policy | menu compatibility fact | capability reverse-inference |
| landing/default route | registry + entry policy | runtime bootstrap | frontend self-selection |
| native fallback | registry + interpreter | native action fact | page-level guessing |
| permission verdict | business/permission service | provider consume | frontend recalculation |

## 4. Component Roles

### 4.1 Scene Registry

Owns:

- `scene_key`
- `family`
- `route`
- `menu_xmlid`
- `action_xmlid`
- `model`
- `view_type`
- `canonical_entry_kind`
- `native_fallback_kind`
- `provider_key`
- `status`
- `owner_module`
- `delivery_tier`

Does not own:

- runtime data fetch
- page content assembly
- business verdicts

### 4.2 Provider

Owns:

- runtime content
- guidance
- next action / next scene hints
- block-level contextual payload

Does not own:

- scene identity
- canonical entry
- authority rebinding

### 4.3 Merge / Policy / Runtime Orchestration

Owns:

- merge policy
- diagnostics
- degrade strategy
- runtime override within declared policy boundaries

Does not own:

- scene identity
- canonical entry identity
- native authority facts

### 4.4 Native Menu / Action / Profile / Capability

Roles:

- source fact
- compatibility fact
- supplemental fact

Not allowed to:

- redefine registry identity
- override canonical entry by drift
- become implicit authority through historical usage

## 5. Authority Violations

An authority violation exists when:

- the same scene_key is defined differently by multiple sources
- provider output contradicts registry identity
- capability/default payload silently changes canonical entry semantics
- native action/menu is treated as the scene identity source

## 6. Governance Requirements

- every new scene must start with registry authority
- provider absence may degrade to fallback, but may not bypass registry
- family closure must remove same-meaning duplicate work entries
- no runtime path may backfill identity through frontend assumptions alone
