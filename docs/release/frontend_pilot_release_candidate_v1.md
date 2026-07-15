# Frontend pilot release candidate v1

Status: frozen release rehearsal candidate. Baseline `origin/main` is `42be4e6568034a420b037739e55fc6c5f6cb4855`; the exact candidate SHA is emitted by `make release.readiness.report`.

The candidate uses Odoo 17 (`17.0-20260513` in the rehearsal runtime), Python 3.12.3 for host release tooling, Node v24.16.0, pnpm 9.12.3 and PostgreSQL 15. Formal module versions are `smart_core=17.0.1.0`, `smart_construction_core=17.0.0.61`, and `smart_construction_custom=17.0.1.1`. `smart_construction_demo=17.0.0.2.0` must remain uninstalled outside acceptance.

The no-demo rehearsal candidate bundle hash from 2026-07-15 is `9fc20270e8c2ad0baf68667590a4746267ead0a8f7e9046e1fd6f46476bbabbc`; the separately database-locked acceptance bundle hash is `55ff4cc451e5a5594e1fdb9a4330eb09bca57a9bd124e5ce57603ab904ac8b99`. Both are production builds and no Vite development server participates. Runtime images are the repository Dockerfile output (`odoo17-odoo:latest` by current environment), `postgres:15`, `redis:7-alpine`, and `nginx:latest`. Image digests must be pinned by the deployment owner before pilot activation.

Frozen product evidence is 70 authoritative navigation leaves (finance 42, project member 9, PM 14, owner 5), J02–J11, and the existing `sc_frontend_acceptance` fixture version from this SHA. Release rehearsal uses `config/release/odoo.release-rehearsal.conf.template`, `docker-compose.release-rehearsal.yml`, and a separate no-demo database/filestore. No product feature, ACL, role, navigation, amount formula, or workflow change is permitted in this candidate.

Commands: `make release.rehearsal.prepare`, `make release.rehearsal.upgrade`, `make verify.release.rehearsal`, `make release.rehearsal.backup`, `make release.rehearsal.restore`, `make release.rehearsal.rollback`, `make release.production.acceptance`, and `make release.readiness.report`.
