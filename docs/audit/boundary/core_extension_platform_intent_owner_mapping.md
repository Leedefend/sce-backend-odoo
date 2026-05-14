# Core Extension Platform Intent Owner Mapping (ITER-2026-04-05-1064)

## Scope

- source: `addons/smart_construction_core/core_extension.py`
- keys: `app.*`, `usage.*`, `telemetry.*` (non-financial only)

## Mapping Matrix

| intent key | current handler owner | suggested owner target | migration difficulty | reason |
| --- | --- | --- | --- | --- |
| `usage.track` | `smart_core.handlers.usage_track.UsageTrackHandler` | `smart_core` platform telemetry/usage lane | done | construction file is compatibility shim only |
| `telemetry.track` | `smart_construction_core.handlers.telemetry_track.TelemetryTrackHandler` | `smart_core` platform telemetry lane | L | narrow event-write semantics, low domain coupling |
| `usage.report` | `smart_core.handlers.usage_report.UsageReportHandler` | `smart_core` platform telemetry/usage lane | done | construction file is compatibility shim only |
| `usage.export.csv` | `smart_core.handlers.usage_export_csv.UsageExportCsvHandler` | `smart_core` platform telemetry/usage lane | done | construction file is compatibility shim only |
| `app.catalog` | `smart_core.handlers.app_shell.AppCatalogHandler` | `smart_core` app shell catalog lane | done | construction extension no longer contributes app shell intent |
| `app.nav` | `smart_core.handlers.app_shell.AppNavHandler` | `smart_core` app shell navigation lane | done | construction extension no longer contributes app shell intent |
| `app.open` | `smart_core.handlers.app_shell.AppOpenHandler` | `smart_core` app shell open/orchestration lane | done | construction extension no longer contributes app shell intent |

## Screening Conclusion

- all seven keys are platform-style semantics but currently injected by scenario extension hook.
- recommended migration order (low-risk first):
  1. `telemetry.track`
  2. `usage.track` (done)
  3. `usage.report` + `usage.export.csv` (done)
  4. `app.catalog` (done)
  5. `app.nav` (done)
  6. `app.open` (done)

## Next Suggested Batch

- next open implement batch should start from `telemetry.track`; `usage.*` and
  `app.*` are already owned by smart_core, with construction usage shims kept
  for import compatibility.
