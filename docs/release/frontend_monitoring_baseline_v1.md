# Frontend pilot monitoring baseline v1

`make verify.release.monitoring` provides the executable local baseline: runtime health must return HTTP 200 within 10 seconds and the latest verified backup must be no older than 24 hours. It writes `monitoring-check.json`.

| Signal | Source | Warning / critical | Owner | Response |
| --- | --- | --- | --- | --- |
| Login success | auth/API structured logs | <99.5% / <99% over 15m | Support/SRE | check identity, session and DB |
| system.init | intent latency/status | p95 >3s / failures >1% | SRE | inspect workers, DB and capability errors |
| API 5xx | proxy/Odoo logs | >0.5% / >1% over 10m | SRE | correlate route, rollback on core journey impact |
| unexpected 401/403 | intent status by role | 2x baseline / isolation incident | Security owner | freeze pilot and audit context |
| payment create/submit/approve | intent outcome | <99% / any data inconsistency | Product owner | stop affected operation and reconcile |
| company switch/My Work | frontend telemetry | >1% failures | Frontend owner | inspect context epoch and late responses |
| login/navigation/company/intent latency | browser/API timing | FE-B06 budget +10% | Frontend/SRE | trace duplicate/N+1 requests |
| DB/filestore capacity | PostgreSQL/filesystem | 70% / 85% | DBA/SRE | expand capacity and verify backup |
| backup age/checksum | backup manifest/check | 20h / 24h or mismatch | DBA | rerun backup; no pilot writes without valid copy |
| connections/workers/cron | PostgreSQL/Odoo health | 80% / exhaustion or repeated cron failure | SRE | shed load, diagnose, rollback if needed |

Until an external platform is selected, the infrastructure owner must schedule the executable check and documented log queries. Platform integration, on-call routing, real-domain TLS and retention are pre-activation conditions, not claims made by this rehearsal.
