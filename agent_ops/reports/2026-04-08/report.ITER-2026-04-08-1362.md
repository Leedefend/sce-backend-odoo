# ITER-2026-04-08-1362 Report

## Batch
- Batch: `1/1`

## Summary of change
- Found initialization gap: `smart_construction_custom` `post_init_hook` previously only applied security policy and did not ensure Chinese translation pack was loaded.
- Implemented additive init fix in:
  - `addons/smart_construction_custom/hooks.py`
- New behavior:
  - ensure `zh_CN` language pack is installed via `base.language.install` (with overwrite)
  - activate `zh_CN`
  - set global params `lang=zh_CN`, `tz=Asia/Shanghai`
  - normalize all active internal users to `lang=zh_CN`, `tz=Asia/Shanghai`
  - then apply existing business full policy

## Verification result
- Upgraded module on `sc_test`:
  - `CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_custom make mod.upgrade MODULE=smart_construction_custom ENV=test DB_NAME=sc_test`
- Applied one-time backfill for current DB by invoking:
  - `base.language.install(...).lang_install()` for `zh_CN`
  - `hooks._apply_user_locale_baseline(env)`
- Runtime check for real user `wutao`:
  - user locale: `lang=zh_CN`, `tz=Asia/Shanghai`
  - native menu translation: `base.menu_administration` => `设置` (zh) / `Settings` (en)

## Root-cause conclusion
- Seeded customer users were already configured with `zh_CN`.
- Actual blocker was translation payload not loaded into translatable menu fields (`ir_ui_menu.name` only had `en_US`).
- Locale normalization alone cannot translate native menus; language pack installation is required.

## Risk analysis
- Conclusion: `PASS`
- Risk level: low (init-only additive behavior, no ACL/financial changes).

## Rollback suggestion
- `git restore addons/smart_construction_custom/hooks.py`
- Re-upgrade module if rollback is applied.

## Next suggestion
- Re-login `wutao` in native `/web` once to refresh session context and verify menu language.
