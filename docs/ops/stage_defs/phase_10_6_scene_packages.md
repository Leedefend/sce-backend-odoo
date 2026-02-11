# Phase 10.6 — Scene as Product Package

## Goals
- Package scene contract as immutable JSON for cross-instance reuse.
- Support package lifecycle: export, dry-run import, import with strategy.
- Keep governance/audit trace for package actions.
- Provide Portal operation page `/admin/scene-packages`.

## Package Contract v1
Schema file:
- `docs/contract/packages/scenes/scene_package_v1.schema.json`

Required fields:
- `package_name`
- `package_version`
- `schema_version`
- `scene_version`
- `scenes[]`
- `profiles`
- `defaults`
- `policies`
- `compatibility.min_core_version`
- `compatibility.supported_schema_versions[]`
- `checksum`

Rules:
- Package payload is immutable.
- `checksum` is SHA-256 over package content excluding `checksum` key.
- Import creates runtime instance copy via config storage (`sc.scene.package.imported_scenes`).

## Runtime Intents
- `scene.package.list`
- `scene.package.export`
- `scene.package.dry_run_import`
- `scene.package.import`

## Installed Package Registry
- Model: `sc.scene.package.installation`
- Purpose: factual installation ledger, independent from upgrade inference.
- Key fields:
  - `package_name`: package identity
  - `installed_version`: package semver (`package_version`)
  - `channel`: target channel when installed
  - `installed_at` / `last_upgrade_at`
  - `source` (`import`/`export`)
  - `checksum`
  - `active`

Version terms:
- `package_version`: distributable package semver
- `scene_version`: scene content version
- `schema_version`: package contract structure version

Import strategies:
- `skip_existing`
- `override_existing`
- `rename_on_conflict`

Governance logging:
- `package_export`
- `package_import`

## Portal Usage
Route:
- `/admin/scene-packages`

Capabilities:
- Installed package list
- Export package (name/version/channel/reason)
- Dry-run import with conflict/addition report
- Confirmed import with required reason

## Verify Commands
- `make scene.package.export PACKAGE_NAME=<name> PACKAGE_VERSION=<version> SCENE_CHANNEL=stable`
- `make verify.portal.scene_package_dry_run_smoke.container`
- `make verify.portal.scene_package_import_smoke.container`
- `make verify.portal.scene_observability_smoke.container`
- Strict evidence mode:
  - `make verify.portal.scene_observability_preflight.container`
  - `make verify.portal.scene_package_import_strict.container`
  - `make verify.portal.scene_observability_strict.container`
- `make verify.portal.scene_package_ui_smoke.container`

## Gate Integration
Included in:
- `make verify.portal.ui.v0_8.semantic.container`

Mandatory in gate:
- `verify.portal.scene_package_dry_run_smoke.container`
- `verify.portal.scene_package_import_smoke.container`

Optional (non-gate by default):
- `verify.portal.scene_package_ui_smoke.container`

## Artifacts
- Export:
  - `artifacts/codex/portal-scene-package-export-v10_6/<timestamp>/`
- Dry-run:
  - `artifacts/codex/portal-scene-package-dry-run-v10_6/<timestamp>/`
- Import:
  - `artifacts/codex/portal-scene-package-import-v10_6/<timestamp>/`
- Portal UI smoke:
  - `artifacts/codex/portal-scene-package-ui-v10_6/<timestamp>/`
