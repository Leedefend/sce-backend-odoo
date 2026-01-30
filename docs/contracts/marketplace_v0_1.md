# Marketplace Readiness v0.1

## Overview

Marketplace readiness defines how delivery packs are published, cataloged,
installed, and upgraded in a local registry.

## Models

### sc.pack.registry
- `pack_id`, `name`, `pack_version`
- `vendor`, `channel`
- `pack_type` (platform/industry/customer)
- `industry_code`
- `depends_on_ids`
- `pack_hash`, `signed_by`
- `published_at`, `published_by`
- `payload_json`

### sc.pack.installation
- `pack_id`
- `installed_version`
- `installed_at`, `installed_by`
- `status`
- `last_diff_json`
- `source_hash`

## APIs

### Publish
`POST /api/packs/publish`

Input: delivery pack payload (v0.2)  
Output: registry record created/updated

### Catalog
`GET /api/packs/catalog`

Filters: `pack_type`, `industry_code`, `channel`, `vendor`

### Install / Upgrade
`POST /api/packs/install`  
`POST /api/packs/upgrade`

Required:
- `pack_id`
- `mode` (merge|replace)
- `dry_run` / `confirm`
- `strict` (optional)

Dependency rules:
- packs with `depends_on_ids` must be installed first

## Strict Mode

When `strict=true`:
- missing group xmlids, menu/action xmlids, or capability keys fail import
- import returns `MAPPING_ERROR` with issues list
