# Handler & Registry Residue Screen After 1061 (ITER-2026-04-05-1062)

## Screen Focus

- `addons/smart_construction_core/core_extension.py`
- `addons/smart_construction_core/handlers/**/*.py`
- `addons/smart_core/core/extension_loader.py`

## Key Evidence

1. `smart_construction_core` still owns a large registry injection surface via `smart_core_register(registry)` in `core_extension.py`.
2. `smart_core` loads extension modules dynamically through `extension_loader.py` and executes external `smart_core_register` hooks.
3. Registry keys in `core_extension.py` include mixed semantics:
   - platform/runtime style: `app.catalog`, `app.nav`, `app.open`, `usage.track`, `telemetry.track`
   - scene/runtime assembly style: `*.enter`, `*.block.fetch`
   - domain/business style: `project.*`, `cost.*`, `risk.*`
   - high-risk financial domain (frozen for this lane): `payment.*`, `settlement.*`

## Residue Classification

| residue type | evidence | boundary assessment | immediate action |
| --- | --- | --- | --- |
| registry ownership concentration | `core_extension.py` single hook injects many intents | medium | split-screen needed before any implement |
| platform-intent in scenario extension | `app.*`, `usage.*`, `telemetry.*` keys registered in construction extension | medium | candidate for next governance screen |
| scene/runtime semantics in scenario extension | `*.enter`, `*.block.fetch` families | medium | keep for now; require staged ownership map |
| financial intent registrations | `payment.*`, `settlement.*` | high (frozen) | out of current cleanup scope |

## Conclusion

- controller boundary cleanup is complete for this objective, but handler/registry boundary still has ownership concentration and semantic mixing.
- next low-risk step should be a dedicated **screen** that isolates non-financial platform-style intent keys (`app.*`, `usage.*`, `telemetry.*`) for possible ownership realignment.

## Suggested Next Batch

- open `1063` screen for "platform-intent keys inside construction core_extension" only;
- explicitly exclude `payment.*` and `settlement.*` from implementation scope due freeze rules.
