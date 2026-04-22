# Scene Family Governance v1

## 1. Goal

Define family as the minimum governance unit for backend scenification.

## 2. Family Definition

A family should describe a bounded scene group with:

- family key
- scene inventory
- canonical scene entry
- native fallback set
- provider set
- capability entry set
- menu mapping set

## 3. Required Family Assets

Each governed family should have:

- registry entries
- provider bindings
- menu/action mappings
- fallback strategy
- failure coverage
- verify coverage

## 4. Family Closure Steps

1. freeze family inventory
2. decide canonical entry
3. remove duplicate same-meaning entries
4. align menu/action mapping
5. align provider completeness
6. add verify coverage

## 5. Family Release Conditions

- canonical entry is unique
- provider completeness is known
- fallback strategy is explicit
- failure types are observable
- verify passes

## 6. Current Governance Guidance

Operate family-by-family rather than scene-by-scene rescue work. A scene may be
updated in one batch, but closure judgement should still happen at family level.
