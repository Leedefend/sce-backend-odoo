# Login Page Design Notes (Round 1)

## Page Goal

- Upgrade the login page from a generic backend form into an official SCEMS entrance.
- Improve product identity and enterprise feel without changing the authentication core.

## First Impression Target

- Users immediately recognize a construction enterprise management platform.
- The tone is stable, professional, and trustworthy.
- Login feedback is explicit, with clear error guidance.

## Copywriting

- Title: `登录系统`
- Product name: `智能施工企业管理平台`
- Subtitle: `面向施工企业的项目、合同、成本、资金与风险协同平台`
- Slogan: `让项目透明、风险可见、决策有据`
- Fields: `账号` / `密码`
- Button: `登录` / `系统正在登录，请稍候…`
- Errors:
  - `账号或密码错误，请重新输入`
  - `网络异常，请稍后重试`
  - `登录失败，请稍后重试`

## Visual Keywords

- Stable
- Enterprise-grade
- Construction management context
- Low-saturation gradient background
- Lightweight hierarchy (chips and subtle highlights)

## Scope Delivered

- Added brand header (product name, subtitle, slogan).
- Added capability strip (project, contract/cost, finance, risk).
- Localized labels and placeholders.
- Improved input/button interaction states.
- Added user-facing error normalization (no raw technical messages).
- Refined card/background hierarchy and responsive behavior.

## Round 2 Refinements

- Enlarged login card width and padding for stronger entrance presence.
- Moved `SCEMS v1.0` badge into brand area to tighten visual ownership.
- Added low-contrast engineering grid layer to reduce left-side emptiness.
- Shortened capability labels and switched to compact grid presentation.
- Rebalanced hierarchy between product name and action title.

## Round 3 Entrance Layout Upgrade (Brand + Login)

- Upgraded to a dual-zone structure: left brand narrative + right login action area.
- Moved capability communication to the brand zone instead of stacking it inside login card.
- Kept login card action-focused (version, login title, credentials, submit button).
- Added low-contrast engineering grid background to strengthen domain identity.
- Added footer copyright text for a formal product-entry impression.

## Out of Scope

- No change to login API, token/session, router guard, app init, backend auth logic.
- No heavy animation, illustration-first layout, or consumer-style visuals.
- No new authentication methods (SMS/SSO/MFA).

## Next Iterations

- Tenant-level branding theme support.
- Contextual help entry (ops contact / handbook).
- Finer error-code mapping based on backend error structure.
