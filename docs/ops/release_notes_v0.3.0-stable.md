---
capability_stage: P0
status: frozen
since: v0.3.0-stable
---
# Release Notes — v0.3.0-stable

## Highlights
- Introduced Prod Guard system with forbid/danger semantics
- Enforced explicit prod seed & restart SOP
- Added machine-verifiable prod guard probe (JSON output)

## Scope
This release hardens production operations and makes guard verification machine-readable for audits and CI.

## Verification
- `ENV=prod make verify.prod.guard`
- Release checklist: `docs/ops/release_checklist_v0.3.0-stable.md`
- Releases index: `docs/ops/releases/README.md`

## Tag
- v0.3.0-stable
