# Documentation Bilingual Consistency Checklist v1

Scope: paired Chinese/English architecture docs under `docs/architecture`.

## Quick Checks
- File pairing: Chinese `.md` and English `.en.md` exist with same basename.
- Structure alignment: section hierarchy/order are aligned (minor language differences allowed).
- Link alignment: CN links to EN counterpart, EN links to CN counterpart.
- Terminology alignment: fixed usage for `group_key`, `scene`, `intent`, `reason_code`.
- Example alignment: config keys, field names, and paths remain identical.
- Version alignment: version markers (for example `v1`) are consistent.
- Update alignment: when one side changes, update the other side in the same PR.

## Currently Included Glossary Docs
- `docs/architecture/nav_group_terms_v1.md`
- `docs/architecture/nav_group_terms_v1.en.md`

## Recommended Timing
- Run once before commit.
- Re-check during PR review.
