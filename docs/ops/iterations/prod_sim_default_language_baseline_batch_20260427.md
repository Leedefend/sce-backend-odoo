# Prod Sim Default Language Baseline Batch - 2026-04-27

## Scope

- Layer Target: `Deployment initialization / UI language baseline`
- Module: `smart_construction_custom`
- Reason: the native Odoo create control still displayed `New` because real internal users in `sc_prod_sim` were initialized with `en_US`.

## Facts Before Fix

- `zh_CN` was installed and active.
- `admin` was `zh_CN`, but most real internal users were still `en_US`.
- `wutao` was `en_US`, so native Web controls such as `New` rendered in English after login.
- The issue was not a project form button string; it was a production-sim initialization gap.

## Changes

- Extended `sc.platform.initialization.apply_baseline()` to:
  - ensure `zh_CN` is active
  - normalize every internal user (`share=False`) to `lang=zh_CN`
  - normalize every internal user's timezone to `Asia/Shanghai`
  - record baseline params:
    - `sc.platform.default_lang=zh_CN`
    - `sc.platform.default_tz=Asia/Shanghai`
    - `sc.platform.internal_user_preferences_count`

External portal users are not changed by this baseline.

## Verification

- `python3 -m py_compile addons/smart_construction_custom/models/platform_initialization.py`
- `git diff --check`
- `make mod.upgrade MODULE=smart_construction_custom`
- Database facts after upgrade:
  - `INTERNAL_USER_PREF_COUNT=112`
  - `INTERNAL_USER_PREF_BAD_COUNT=0`
  - `wutao.lang=zh_CN`
  - `wutao.tz=Asia/Shanghai`
- `make restart`
- `E2E_LOGIN=wutao E2E_PASSWORD=123456 make verify.menu.navigation_snapshot.container`
  - `PASS checked=139 scenes=16 trace=64f0c94b146a`

## Result

PASS. The simulated production database now has a repeatable language baseline for real internal users, so native Odoo controls are expected to render through the Chinese UI after users re-login.
