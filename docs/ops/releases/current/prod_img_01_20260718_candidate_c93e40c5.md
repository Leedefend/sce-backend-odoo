# PROD-IMG-01 candidate c93e40c5 — independent gates complete

Date: 2026-07-18 (Asia/Shanghai)

## Decision

The immutable candidate, security scan, authorized daily-development history
upgrade, production-static menu correction, standard dump/restore, and paired
rollback gates passed. No production deployment was attempted.

Final deployment approval remains blocked because no live production read-only
channel is available. The historical production report is retained only as
history and is not treated as current production state.

```text
PROD-IMG-01=BLOCKED_BY_PRODUCTION_READ_ONLY_CHANNEL
PRODUCTION_DEPLOYMENT=NOT_AUTHORIZED
```

## Source and product correction

- locked product source: `c93e40c5e2613c0b9389492f185365c1d498e7d2`
- product PR: `#1103`
- product commit: `c36befb663ca736bb55d11f695da88271c62d33e`
- merge commit: `c93e40c5e2613c0b9389492f185365c1d498e7d2`
- release branch HEAD at rehearsal start: `fd48ebb7c`
- previous failed candidate digest reused: no

The correction injects `treeDragEnabled`, `treeMenuById`, and
`isRuntimeMenuGroup` into `useMenuTreeEditor()` instead of referencing missing
component-closure names. A runtime behavior guard now covers a normal menu,
disabled drag, and runtime navigation groups. PR quality gate and the single
final `make ci` passed.

## Immutable image

- image: `sce-production-candidate:c93e40c5e261`
- image ID/digest:
  `sha256:e865bdfbc617d602efd91fd78de0199a8fbe58453a87e6568f2a6177460065fa`
- frontend build SHA256:
  `f3186fee40a9a6ec60abe3a0fdef43109bc7fef566663d3fc295899406a91db0`
- image archive SHA256:
  `59b7a5ebaa5be2cacbc8c4b0ebb17f06f9c7e9798209a0ea4ebb8df4f96846b5`
- Odoo: `17.0-20260630`
- Python: `3.10.12`
- Node: `22.17.0`, build-only
- pnpm: `9.12.3`, build-only
- runtime Node/lessc/rtlcss: absent
- host source/static mounts: 0
- save/remove/load image identity: equal

The runtime base and frontend builder remain pinned by digest. The release
acceptance scripts are explicitly excluded from the product-source comparison;
all actual frontend workspace and build inputs remain locked to the product
source SHA.

## Security

- CycloneDX SBOM: generated
- Trivy Critical: 0
- Trivy High: 0
- Trivy Secret: 0
- result: passed

No vulnerability ignore or severity downgrade is used.

## Authorized history source

The source is the paired read-only export from the daily development server,
not a local development database.

- source database: `sc_demo`
- source repository HEAD: `6095e2013d64c06a5ea936addd35858959d2a28f`
- database dump SHA256:
  `7f913edc6d5f99f99ac11196376a6bdeac41f413b1abec1f9e9c991d95023fc7`
- filestore archive SHA256:
  `72178da73096ffbb2fe59b6bb02690a84e131ef089afe283d87a374602da9eaf`
- filestore content/path SHA256:
  `7e235ce9c88b261da71e300a8b7504382a71c2b545fff768b9f4f8772219a947`
- capture watermarks stable: yes
- production database writes: 0

## Upgrade and data fingerprints

- paired restore: passed, 210 seconds
- formal module upgrade: passed, 151 seconds
- `smart_core`: installed
- `smart_construction_core`: installed
- `smart_construction_portal`: installed
- `smart_construction_custom`: installed
- pending modules: 0
- `smart_construction_demo`: uninstalled before and after
- known historical warnings: 5 before and after

All business counts, protected ID digests, amount summaries, missing-relation
counters, and filestore facts are unchanged. The only expected technical shape
change is:

```text
low_code_change_sets: table absent -> 0 rows
```

No historical business record, XML-ID ownership fact, user, company, project,
partner, follower, approval reference, attachment, or amount fact drifted.

## Production-static targeted acceptance

The candidate image served its packaged production frontend; no Vite server or
host static override was used.

- candidate login: passed
- formal menu configuration editor: passed
- normal configurable menu enters drag state: passed
- runtime navigation group remains non-draggable: passed
- `ReferenceError`: 0
- page errors: 0
- console errors: 0
- drop performed: no
- save performed: no

The prior candidate's completed LC-J11–J18, LC-E01–E06, LC-F01–F04,
safe-open, preview-zero-write, atomic publish, rollback, and explicit-empty
evidence remains applicable because #1103 changes only the missing menu-drag
runtime dependencies. The previously blocked menu journey is now directly
retested against this image.

## Dump, restore, and rollback

- upgraded database standard `pg_dump`: passed
- restore into a new isolated database: passed
- restored database pending modules: 0
- second standard `pg_dump`: passed
- dump/restore verification: 286 seconds
- temporary verification database: removed
- paired DB+filestore rollback: passed, 203 seconds
- pre-upgrade fingerprint:
  `aff52d3126c7b732f6a49d8dbcfddbe383943b4749294d9fbf8ba0d543bb75e8`
- rollback fingerprint:
  `aff52d3126c7b732f6a49d8dbcfddbe383943b4749294d9fbf8ba0d543bb75e8`
- protected rollback dimensions changed: 0
- candidate containers after rehearsal: stopped

## Remaining blocker

The production collector still has no running production connection and cannot
refresh backend SHA, frontend hash, running digest, runtime versions, module
state, database/filestore fingerprint, TLS, ports, selector, backup pairing, or
health. Its old collector SHA and configured image are not live evidence.

Until an authorized read-only channel is provided, RPO/RTO and the final
production-to-candidate delta cannot be approved. This report is therefore a
complete independent candidate evidence checkpoint, not deployment approval.
