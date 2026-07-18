# PROD-BLOCKER-01 migration and image safety evidence

Status: blocker-scope validation evidence. This document is not production
deployment authorization.

## Migration safety boundary

Database names are not ownership facts. The `17.0.0.2.0` and `17.0.0.2.1`
`smart_construction_seed` post-migrations are non-destructive inventories:
they retain every `smart_construction_demo` XML-ID and referenced record and
write only a technical review marker. Demo ownership cleanup is an independent,
explicit, dry-run-only operation bound to a source fingerprint and approver.

The daily-development source is captured read-only from compose project
`sc-backend-odoo-dev`, database `sc_demo`. Database and filestore watermarks
must remain stable before and after capture. Sensitive rows, dumps, and
filestore content are excluded from repository evidence.

## Original six High findings

The failed candidate scan reported the following Ubuntu packages from the
official Odoo base-image layer
`sha256:5a074bdfd6fcea12d6a953c1179ba9b35445c16e2bf868cfe35e10dc4bf4f4a6`.
Ubuntu supplied no fixed version for these Node 12 packages in that image.

| CVE | OS package | Installed version | Fixed version | Runtime reachability before remediation | Source / introducing layer | Remediation |
| --- | --- | --- | --- | --- | --- | --- |
| CVE-2023-44487 | libnode-dev | 12.22.9~dfsg-1ubuntu3.6 | unavailable | headers only; not directly executed | official Odoo Ubuntu layer | remove from runtime image |
| CVE-2026-45447 | libnode-dev | 12.22.9~dfsg-1ubuntu3.6 | unavailable | headers only; not directly executed | official Odoo Ubuntu layer | remove from runtime image |
| CVE-2023-44487 | libnode72 | 12.22.9~dfsg-1ubuntu3.6 | unavailable | reachable through Node/rtlcss invocation | official Odoo Ubuntu layer | remove from runtime image |
| CVE-2026-45447 | libnode72 | 12.22.9~dfsg-1ubuntu3.6 | unavailable | reachable through Node/rtlcss invocation | official Odoo Ubuntu layer | remove from runtime image |
| CVE-2023-44487 | nodejs | 12.22.9~dfsg-1ubuntu3.6 | unavailable | executable present and callable by asset/RTL tooling | official Odoo Ubuntu layer | remove from runtime image |
| CVE-2026-45447 | nodejs | 12.22.9~dfsg-1ubuntu3.6 | unavailable | executable present and callable by asset/RTL tooling | official Odoo Ubuntu layer | remove from runtime image |

The remediation does not ignore findings. Frontend compilation runs in a
separate, digest-pinned Node `22.17.0` builder. The runtime purges Node 12,
npm, less, rtlcss, Node libraries, development headers, and automatically
installed `node-*` packages. Odoo startup, clean asset-cache rebuild,
authenticated backend access, packaged frontend static files, and PDF report
generation are validated without a Node executable in the runtime.

## RTL product boundary

The released product supports LTR locales only. Runtime RTL compilation is not
supported. If RTL becomes a product requirement, it must be introduced through
a separately reviewed, supported toolchain and real asset acceptance; the
legacy Node 12/rtlcss stack must not be restored.

## External boundary

The production read-only channel is outside this branch. Until a fresh
production baseline is collected, deployment approval remains blocked by
`BLOCKED_BY_PRODUCTION_READ_ONLY_CHANNEL` even if this blocker PR is accepted.
