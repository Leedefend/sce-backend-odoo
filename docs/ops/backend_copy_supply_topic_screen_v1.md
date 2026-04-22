# Backend Copy Supply Topic Screen v1

## Scope

This screen is a bounded follow-up to the completed frontend semantic fallback
cleanup line and the immediate backend page-copy supplement line on
`2026-04-19`.

The purpose is not to implement new copy supply immediately. The purpose is to
freeze the next backend topics so that later implementation batches can stay
small, layer-correct, and verifiable.

## Current Baseline

Already completed:

- frontend semantic fallback cleanup across `HomeView`, `MyWorkView`,
  `ListPage`, `WorkbenchView`, `SceneView`, `CapabilityMatrixView`,
  `ReleaseOperatorView`, and action runtime helpers
- backend page contract copy supplement for:
  - `scene`
  - `capability_matrix`
  - `release_operator`
- frontend consumer switch for:
  - `CapabilityMatrixView`
  - `ReleaseOperatorView`

Meaning:

- frontend now exposes missing backend copy more faithfully
- remaining wording work should move to backend-owned semantic supply

## Topic Split

### Topic A: Page Contract Text Completion

Layer:
- `scene-orchestration semantic supply`

Primary owner:
- `addons/smart_core/core/page_contracts_builder.py`

Use when:
- missing wording belongs to page shell / page section / empty-state / action
  label / filter copy
- the wording is generic to a page contract and not tied to a single runtime
  record instance

Current candidates:

- `workbench`
- `my_work`
- `action`
- any remaining `home` text keys still intentionally left as backend gaps

Not in scope:

- record-instance diagnostics
- business-fact explanation
- handler-returned action result copy

Entry condition:

- the frontend consumer already uses `usePageContract(...)`
- the missing text can be expressed as stable page text keys

Stop condition:

- the wording depends on runtime business facts rather than page shell semantics

### Topic B: Scene Diagnostics Copy Completion

Layer:
- `scene-orchestration semantic supply`

Primary owner:
- `addons/smart_core/core/page_contracts_builder.py`
- bounded scene contract / diagnostics builders if page texts are insufficient

Use when:
- missing wording describes runtime diagnostics such as:
  - scene idle with no render target
  - readonly / restricted / empty runtime status
  - missing required count
  - transition count
  - diagnostics alignment warnings

Current candidates:

- residual `SceneView` diagnostics wording
- any diagnostics now still rendered as raw code/value because backend has not
  yet supplied a better semantic label

Not in scope:

- page shell chrome
- generic action button labels
- business document copy

Entry condition:

- the wording is attached to `scene_contract_v1.diagnostics` or scene runtime
  diagnostic state

Stop condition:

- the wording would require inventing business facts not present in diagnostics

### Topic C: Runtime Surface Handler Copy Completion

Layer:
- `scene-orchestration semantic supply`

Primary owner:
- bounded handler/service surfaces in `addons/smart_core/delivery/**` or
  `addons/smart_core/handlers/**`

Use when:
- the page is not driven primarily by `page contract texts`
- the page consumes a dedicated runtime surface payload and still lacks:
  - title
  - description
  - section hint
  - empty-state message

Current candidates:

- `release.operator.surface`
- any future dedicated runtime surface similar to `capability matrix`

Not in scope:

- page contract shell text that can be solved in Topic A
- action result copy already covered by previous execute-button batch

Entry condition:

- the missing copy is specific to a surface payload rather than a generic page
  contract

Stop condition:

- the same wording can be expressed more cleanly in page contract texts alone

## Priority

Recommended execution order:

1. Topic A: Page Contract Text Completion
2. Topic B: Scene Diagnostics Copy Completion
3. Topic C: Runtime Surface Handler Copy Completion

Reason:

- Topic A unlocks the broadest frontend coverage with the lowest risk
- Topic B is still bounded but closer to runtime truth
- Topic C is the narrowest and should be used only where page texts are not the
  correct source

## Suggested Next Task Lines

Recommended next concrete task:

- `BE-PAGE-CONTRACT-TEXT-COMPLETION-IMPLEMENT`

Initial target set:

- `workbench`
- `my_work`
- `action`

After that:

- `BE-SCENE-DIAGNOSTICS-COPY-COMPLETION-IMPLEMENT`

Only after those two:

- `BE-RUNTIME-SURFACE-COPY-COMPLETION-IMPLEMENT`

## Guardrails

- frontend must remain a consumer, not the final owner of wording
- scene diagnostics copy must not fabricate missing business facts
- runtime surface copy must stay bounded to the exact handler/service payload
- no schema-breaking removals in existing page texts
- no cross-topic mixing inside one implementation batch
