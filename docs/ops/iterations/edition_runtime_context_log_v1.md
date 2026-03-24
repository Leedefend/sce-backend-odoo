# Edition Runtime Context Log v1

## 2026-03-24

- batch: `Edition Runtime Routing v1`
- branch: `codex/next-round`
- intent:
  - unify edition runtime context priority
  - expose requested/effective edition in `system.init`
  - persist edition runtime context in frontend session
  - support route/query edition injection and subsequent runtime pass-through
- non-goals:
  - reopen FR-1 to FR-5
  - change released navigation semantics
  - change standard release meaning
- gate:
  - `verify.release.edition_runtime.v1`
