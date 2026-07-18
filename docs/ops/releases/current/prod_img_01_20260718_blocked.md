# PROD-IMG-01 immutable candidate rehearsal — blocked evidence

Date: 2026-07-18 (Asia/Shanghai)

## Decision

`PROD-IMG-01` is not ready for production deployment approval. No production
deployment was attempted and no production database write was made.

The isolated history upgrade is blocked by the existing
`smart_construction_seed` 17.0.0.2.1 post-migration. The migration deletes a
record owned by `ir.model.data` and then reads fields from the now-deleted ORM
record while formatting its audit action. Odoo raises `MissingError` for
`ir.model.data(297487)` and exits with status 255.

This is product migration code. It was not changed on the release-tooling
branch.

## Locked source and immutable image

- locked source and `origin/main`: `7010bed829e0a7f34fdea45073a2a4e5034d6ab7`
- release-tooling branch: `feature/immutable-production-candidate-v1`
- candidate image: `sce-production-candidate:7010bed829e0`
- image ID/digest: `sha256:2e5948552651bd0b488d1cde5cc00fcfa1e194c49ae93a19cad1ed0dfbc2d598`
- production frontend SHA256: `144fbd0b6607fde04836f83ccf657db7e9c378e058fb83ec8a17884a7a3668ae`
- immutability proof: save, remove tag, reload, and image-ID equality passed
- image runtime versions: Odoo 17.0-20260630, Python 3.10.12

The image contains the Odoo backend, formal addons, Python dependencies,
production frontend static build, nginx configuration, and startup
configuration. The candidate compose file does not mount host source or host
frontend static content.

## Production read-only baseline

The configured local production compose project had no running containers and
no repository-managed remote production endpoint was available. The read-only
probe therefore recorded `runtime_available=false`; production SHA, image
digest, frontend hash, module state, TLS, ports, database selector, backup age,
and live health remain unavailable. Production write count was zero.

This is a second independent readiness blocker because the required live
production-to-candidate delta cannot be established from the present
environment.

## SBOM and security scan

The final image has a CycloneDX SBOM and completed Trivy vulnerability plus
secret scanning. Result: Critical=0, High=6, Secret=0. The High=0 release gate
is therefore not met.

All six High findings are the two unfixed Ubuntu findings CVE-2023-44487 and
CVE-2026-45447 repeated for `nodejs`, `libnode72`, and `libnode-dev` version
12.22.9~dfsg-1ubuntu3.6 inherited from the official Odoo 17 base image. The
packages support Odoo's runtime `lessc`/`rtlcss` asset toolchain, so they were
not removed or ignored without a separately validated replacement. No secret
finding was present.

Evidence checksums:

- image manifest: `c81214fda7ee5eb3495e5974d14deb2f995ef7c687521cdb92145f0ca194e30c`
- CycloneDX SBOM: `fef3279f201f15f908dcb6090a53008ef5e23d86a5a9e7f48df6af392947b604`
- Trivy JSON: `07055052d83ed9e0e958c7bad1cc767fafe18b50f06331e9e02fe25c8c728a87`
- security summary: `f91ae970e8d11405c92969f5e4cd8ad266bb32457bb82241690eef968eae3e2b`
- paired history-backup manifest: `3d1e2c7307df9fc7594a1f0b785d35040f2e16dd77707948b98098829bfc407c`

## Authorized history source and fingerprints

The isolated database `sc_user_data_rehearsal` was restored from the paired
2026-06-02 snapshot:

- database dump SHA256: `78986f7f9be994f06351230cb781b14e7bbe5f5a0c19bbd8aff37696c04d4159`
- filestore archive SHA256: `846731f56a83d2d5f740b3e9ed3137e9768f12ddc3ac6ca961d9213684783617`
- standard `pg_dump`: passed after restore
- pre-upgrade paired backup: passed
- source and restored-candidate business fingerprint:
  `b5e684b76958df8d2baaaa36b5868df187e1d4b25e7d622748765d6129b483f8`
- known historical warnings: 4 before the attempt and 4 after it
- filestore: 529 files, 8,831,122 bytes,
  `ac0d62b9fc68b9bf8aee4d44e74a01852ff3338c15e3b43f9e349628b2e1ee3a`

The failed Odoo run committed some earlier module upgrades before the seed
migration failed. Business counts, business ID digests, amounts, relations,
and filestore did not drift, but technical config contracts and versions did.
The candidate was therefore discarded and restored again from the paired
backup. Its final fingerprint exactly matches the source fingerprint above.

The source snapshot also has `smart_construction_demo=installed`. The existing
user-data boundary workflow only deactivates reviewed demo users and assumes
the module is already uninstalled; it does not safely uninstall the module.
No ad-hoc module uninstall or catalog deletion was performed.

## Upgrade and daily-development result

The candidate used the formal addon path including
`/mnt/addons_external/oca_server_ux`. Its formal upgrade reached
`smart_construction_seed` and failed in
`migrations/17.0.0.2.1/post-migration.py` after 674 seconds.

The separately authorized daily development database `sc_demo` upgrade of
`smart_core`, `smart_construction_core`, `smart_construction_portal`, and
`smart_construction_custom` passed. The migration deliberately bypasses the
cleanup for database names matching `sc_demo`, so that success does not clear
the production-shaped history blocker.

## Deferred gates

Production-static runtime acceptance, J02-J13, navigation matrices, low-code
LC-J/LC-E/LC-F, LC-DEBT-01 probe, backup recovery with the actual old production
image, RPO/RTO, final `make ci`, PR creation, and merge were not claimed. They
require a successfully upgraded history candidate and the unavailable live
production baseline.

The full CI command remains unconsumed; the rule that it run exactly once after
all technical acceptance is preserved.

Release script shell syntax, Python compilation, candidate Compose rendering,
`git diff --check`, repository secret/credential guards, generated-report
guards, frontend lint, and strict frontend typecheck passed through
`make ci.local.quick`. The candidate containers were stopped after evidence
collection; their named volumes were not deleted.

Uncommitted release-tooling diff stat at the blocked handoff is 16 files,
1,107 insertions, and 1 deletion. No product addon or frontend source file is
modified. No PR was opened and no branch was pushed because the release
acceptance is incomplete.
