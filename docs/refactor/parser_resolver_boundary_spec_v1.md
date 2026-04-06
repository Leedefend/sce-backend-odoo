# Parser Resolver Boundary Spec v1

## 1. Purpose

Define strict boundaries for parser/resolver components so they remain
interpretation services and do not absorb capability/runtime/frontend ownership.

## 2. Resolver Scope

Resolver should:

- interpret native objects and config models into normalized structures
- expose deterministic parse results for downstream projection
- provide explicit parse diagnostics for governance and lint

Resolver should not:

- own capability registry governance decisions
- execute runtime business orchestration
- render frontend final payloads
- mutate native truth ownership

## 3. Input Sources

- Native objects (`ir.ui.menu`, `ir.actions.*`, `ir.model`, `ir.ui.view`)
- Config models (app/action/view/permission/workflow configs)

## 4. Output Contract

- Normalized parse rows only.
- No direct frontend shape.
- No implicit cross-layer side effects.

## 5. Ownership Boundaries

- Native truth ownership stays in Odoo native models.
- Capability ownership stays in platform capability registry.
- Intent ownership stays in runtime intent protocol.

## 6. Stop Rules (禁止)

- 禁止 parser 直接写 capability registry storage.
- 禁止 resolver 直接拼装 workspace/app/frontend 终态结构。
- 禁止 parser 在解释阶段执行业务模型副作用。
- 禁止通过行业模块桥接接管平台解析主权。

## 7. Integration Pattern

```text
Native / Config Input
  -> Resolver Output (normalized row)
  -> Native-to-Capability Projection
  -> Capability Registry
  -> Intent Binding
  -> Contract / Orchestration
```

## 8. Validation Baseline

- parser output schema lint
- projection schema lint
- capability ownership guard
- runtime intent binding guard

