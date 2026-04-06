# Core Extension Platform Intent Owner Mapping (ITER-2026-04-05-1064)

## Scope

- source: `addons/smart_construction_core/core_extension.py`
- keys: `app.*`, `usage.*`, `telemetry.*` (non-financial only)

## Mapping Matrix

| intent key | current handler owner | suggested owner target | migration difficulty | reason |
| --- | --- | --- | --- | --- |
| `usage.track` | `smart_construction_core.handlers.usage_track.UsageTrackHandler` | `smart_core` platform telemetry/usage lane | M | touches usage persistence and policy checks but no financial coupling |
| `telemetry.track` | `smart_construction_core.handlers.telemetry_track.TelemetryTrackHandler` | `smart_core` platform telemetry lane | L | narrow event-write semantics, low domain coupling |
| `usage.report` | `smart_construction_core.handlers.usage_report.UsageReportHandler` | `smart_core` platform telemetry/usage lane | M | report shape needs compatibility baseline for existing consumers |
| `usage.export.csv` | `smart_construction_core.handlers.usage_export_csv.UsageExportCsvHandler` | `smart_core` platform telemetry/usage lane | M | export contract and content schema need stable backward compatibility |
| `app.catalog` | `smart_construction_core.handlers.app_catalog.AppCatalogHandler` | `smart_core` app shell catalog lane | M | tied to app catalog semantics and sorting policy; moderate contract sensitivity |
| `app.nav` | `smart_construction_core.handlers.app_nav.AppNavHandler` | `smart_core` app shell navigation lane | M | navigation payload and fallback strategy impact runtime entry behavior |
| `app.open` | `smart_construction_core.handlers.app_open.AppOpenHandler` | `smart_core` app shell open/orchestration lane | H | contains branching/fallback orchestration with higher behavior coupling |

## Screening Conclusion

- all seven keys are platform-style semantics but currently injected by scenario extension hook.
- recommended migration order (low-risk first):
  1. `telemetry.track`
  2. `usage.track`
  3. `usage.report` + `usage.export.csv`
  4. `app.catalog`
  5. `app.nav`
  6. `app.open`

## Next Suggested Batch

- open a dedicated `implement` batch for first slice (`telemetry.track` + `usage.track`) only,
  with strict exclusion of financial keys (`payment.*`, `settlement.*`) and no cross-slice mixing.
