# PROD-IMG-01 resumed rehearsal — product runtime blocker

Date: 2026-07-18 (Asia/Shanghai)

## Decision

`PROD-IMG-01` remains paused. No production deployment was attempted and no
production or daily-development database write was made.

The migration-safety and image-vulnerability blockers are closed, but the
production-static low-code menu journey found a product runtime exception:

```text
ReferenceError: treeDragEnabled is not defined
```

The exception is raised when the formal menu configuration tree starts a drag
interaction. `useMenuTreeEditor()` references `treeDragEnabled`,
`treeMenuById`, and `isRuntimeMenuGroup` without receiving or defining them.
The first undefined reference stops the journey. This requires a product-code
correction and must not be mixed into the release-tooling branch.

## Locked source and release branch

- current `origin/main`: `f465613835c15827cbb511d097c235928ba6083e`
- blocker product commit: `408e34bde4cfa0d1e364c0416c8621150aa92457`
- release branch after rebase: `feature/immutable-production-candidate-v1`
- prior local release checkpoint: `9053143a37857ca4a1f19e7bbbb2b6b795f420c2`
- product/runtime source differs from locked main: no

## Daily-development history source

The rehearsal does not use a local history database. It consumes the paired,
read-only export captured from the daily development server's `sc_demo`.

- source repository HEAD: `6095e2013d64c06a5ea936addd35858959d2a28f`
- database dump SHA256:
  `7f913edc6d5f99f99ac11196376a6bdeac41f413b1abec1f9e9c991d95023fc7`
- filestore archive SHA256:
  `72178da73096ffbb2fe59b6bb02690a84e131ef089afe283d87a374602da9eaf`
- filestore content/path SHA256:
  `7e235ce9c88b261da71e300a8b7504382a71c2b545fff768b9f4f8772219a947`
- source watermarks stable throughout capture: yes
- source database and filestore pair copied into release evidence: yes
- production write count: 0

The pair was restored only to the isolated
`sc_user_data_rehearsal_candidate` database and matching candidate filestore.

## Immutable candidate image

- candidate image: `sce-production-candidate:f465613835c1`
- image ID/digest:
  `sha256:bf847f76db084846c33a1e8023965e8fa766d8628db763915e16fd9c81077d7a`
- production frontend SHA256:
  `144fbd0b6607fde04836f83ccf657db7e9c378e058fb83ec8a17884a7a3668ae`
- runtime base:
  `odoo:17.0@sha256:f88f646a0f5fc0b225995ee28953d9ce7367cc731b1756765114691fb97d18e5`
- frontend builder:
  `node:22.17.0-bookworm-slim@sha256:b04ce4ae4e95b522112c2e5c52f781471a5cbc3b594527bcddedee9bc48c03a0`
- Node purpose: build-only
- runtime Node/lessc/rtlcss packages and executables: absent
- RTL boundary: unsupported, LTR-only
- image save/remove/load identity: equal
- host source/static mounts: 0

The fixed-digest frontend builder generates the sole static archive. The
runtime image copies that archive unchanged and binds its SHA256 into the image
label. The Ubuntu nginx default site is removed so the candidate configuration
is the only port-80 server.

## Security scan

- Trivy Critical: 0
- Trivy High: 0
- Trivy Secret: 0
- CycloneDX SBOM: generated

The six previous High results (CVE-2023-44487 and CVE-2026-45447 on
`nodejs`, `libnode72`, and `libnode-dev`) are absent because Node is confined
to the builder and all Node runtime packages are removed rather than ignored.

## Upgrade and fingerprints

The paired snapshot restored in 216 seconds. The four formal modules upgraded
successfully; an idempotent repeat completed in 139 seconds.

- `smart_core`: installed
- `smart_construction_core`: installed
- `smart_construction_portal`: installed
- `smart_construction_custom`: installed
- pending modules: 0
- `smart_construction_demo`: uninstalled before and after
- seed migration: completed without deleting records or XML-IDs
- known historical warnings: 5 before and after

Unchanged before/after:

- companies: 2
- users: 115
- partners: 8,491
- projects: 923
- contracts: 12,671
- settlements: 3,416
- payment requests: 34,897
- payment executions: 38,565
- ledgers: 12,194
- attachments: 609,258
- configuration contracts: 1,305
- configuration versions: 2,461
- all protected ID digests
- all core amount summaries
- all missing-relation counters
- filestore count, bytes, and digest

The only expected schema-level difference is
`low_code_change_sets: table absent -> 0 rows`, produced by the newly installed
technical model. It does not change a business fact.

After the browser blocker, the candidate runtime was stopped and the original
paired snapshot was restored again. The restored business fingerprint is
`aff52d3126c7b732f6a49d8dbcfddbe383943b4749294d9fbf8ba0d543bb75e8`,
exactly matching the original pre-upgrade fingerprint for counts, amounts, ID
digests, relations, filestore, warnings, and demo-module state.

## Production-static acceptance reached

- backend and nginx health: passed
- packaged SPA `/login`: passed after removing the Ubuntu default nginx site
- two low-code administrator accounts: passed
- ordinary historical user authorization: passed through change-set isolation
- LC-J11 through LC-J18: passed
- LC-E01 through LC-E06 evidence: passed
- LC-F01 through LC-F04: passed
- preview formal writes: 0
- atomic publish and rollback: passed
- explicit empty configuration reopen/clean/read-only behavior: passed
- candidate change-set report SHA256:
  `38c9586de220763ab55222e046c5c188c8171747d4cfe683544e83120a90c5ba`

The remaining full business, low-code, navigation, viewport, rollback, and RTO
matrix was stopped at the first genuine product runtime exception. No pass is
claimed for unexecuted gates.

## Product blocker evidence

- page: formal menu configuration editor
- action: pointer-down/start drag on a menu tree row
- compiled error: `ReferenceError: treeDragEnabled is not defined`
- source: `frontend/apps/web/src/views/menuConfig/useMenuTreeEditor.ts`
- first failing reference: `startTreeDrag()`
- browser report SHA256:
  `7d775b2b33ae1bb539cf72e4d77ac63e0a2d19c6014667830dcd59d368c1ead2`
- result: page journey timed out after the runtime exception

## Remaining external blocker

The live production baseline is still unavailable:

```text
BLOCKED_BY_PRODUCTION_READ_ONLY_CHANNEL
```

Old reports are not used as a live production baseline. This external blocker
continues to prevent final deployment approval even after the product runtime
bug is corrected.

```text
PROD-IMG-01=PAUSED
PRODUCTION_DEPLOYMENT=NOT_AUTHORIZED
```
