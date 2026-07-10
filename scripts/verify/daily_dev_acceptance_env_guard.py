#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path


EXPECTED = {
    "ENV": "dev",
    "ENV_FILE": ".env.dev",
    "DB_NAME": "sc_demo",
    "ACCEPTANCE_BASE_URL": "http://127.0.0.1:18081",
    "ACCEPTANCE_LOGIN": "wutao",
    "ACCEPTANCE_NAV_MIN_ACTIONS": "100",
    "ACCEPTANCE_NAV_MAX_ACTIONS": "115",
    "ACCEPTANCE_NAV_FORBIDDEN_LABELS": "用户核对菜单,用户数据验收,用户验收,直营项目系统菜单",
    "ACCEPTANCE_NAV_REQUIRED_PATHS": "系统菜单 / 基础资料 / 客户,系统菜单 / 基础资料 / 供应商,系统菜单 / 项目中心 / 项目台账,系统菜单 / 合同中心 / 合同管理 / 一般合同（公司）,系统菜单 / 施工管理 / 施工日志,系统菜单 / 物资与分包 / 材料管理 / 入库单,系统菜单 / 财务中心 / 付款管理 / 支付申请,系统菜单 / 财务中心 / 账户资金 / 资金日报表,系统菜单 / 人事行政 / 项目管理人员工资登记,系统菜单 / 资料证照 / 公司资料存档,系统菜单 / 税务中心 / 进项发票,系统菜单 / 配置中心 / 低代码系统配置 / 菜单配置",
    "ACCEPTANCE_NAV_REQUIRED_ACTIONS": "系统菜单 / 基础资料 / 客户=>786|系统菜单 / 基础资料 / 供应商=>787|系统菜单 / 项目中心 / 项目台账=>506|系统菜单 / 合同中心 / 合同管理 / 一般合同（公司）=>669|系统菜单 / 施工管理 / 施工日志=>701|系统菜单 / 物资与分包 / 材料管理 / 入库单=>988|系统菜单 / 财务中心 / 付款管理 / 支付申请=>780|系统菜单 / 财务中心 / 账户资金 / 资金日报表=>784|系统菜单 / 人事行政 / 项目管理人员工资登记=>862|系统菜单 / 资料证照 / 公司资料存档=>615|系统菜单 / 税务中心 / 进项发票=>756|系统菜单 / 配置中心 / 低代码系统配置 / 菜单配置=>841",
    "ACCEPTANCE_PROBE_OUTPUT": "artifacts/backend/dev_acceptance_release_probe.json",
    "FRONTEND_DIST_DIR": "./frontend/apps/web/dist-dev",
    "VITE_PLATFORM_ADMIN_DB": "sc_platform_core",
}

REQUIRED_NONEMPTY = (
    "ACCEPTANCE_PASSWORD",
)

FORBIDDEN_OVERRIDES = (
    "VITE_API_BASE_URL",
    "VITE_API_PROXY_TARGET",
    "VITE_ODOO_DB",
    "VITE_ODOO_DB_LOCKED",
    "VITE_APP_ENV",
    "VITE_BUILD_MODE",
    "VITE_BUILD_OUT_DIR",
    "VITE_DELIVERY_MODE",
    "VITE_FEATURE_FLAGS",
    "VITE_LITE_CONTRACT_PILOT",
    "VITE_LITE_CONTRACT_ROLLOUT",
    "VITE_TENANT",
)


def _norm_env_file(value: str) -> str:
    if not value:
        return value
    path = Path(value)
    if path.is_absolute():
        try:
            return path.resolve().name if path.resolve().parent == Path.cwd().resolve() else path.as_posix()
        except OSError:
            return path.as_posix()
    return path.as_posix()


def main() -> int:
    errors: list[str] = []
    observed = {
        "ENV": os.getenv("ENV", "").strip(),
        "ENV_FILE": _norm_env_file(os.getenv("ENV_FILE", "").strip()),
        "DB_NAME": os.getenv("DB_NAME", "").strip(),
        "ACCEPTANCE_BASE_URL": os.getenv("ACCEPTANCE_BASE_URL", "").strip().rstrip("/"),
        "ACCEPTANCE_LOGIN": os.getenv("ACCEPTANCE_LOGIN", "").strip(),
        "ACCEPTANCE_NAV_MIN_ACTIONS": os.getenv("ACCEPTANCE_NAV_MIN_ACTIONS", "").strip(),
        "ACCEPTANCE_NAV_MAX_ACTIONS": os.getenv("ACCEPTANCE_NAV_MAX_ACTIONS", "").strip(),
        "ACCEPTANCE_NAV_FORBIDDEN_LABELS": os.getenv("ACCEPTANCE_NAV_FORBIDDEN_LABELS", "").strip(),
        "ACCEPTANCE_NAV_REQUIRED_PATHS": os.getenv("ACCEPTANCE_NAV_REQUIRED_PATHS", "").strip(),
        "ACCEPTANCE_NAV_REQUIRED_ACTIONS": os.getenv("ACCEPTANCE_NAV_REQUIRED_ACTIONS", "").strip(),
        "ACCEPTANCE_PROBE_OUTPUT": os.getenv("ACCEPTANCE_PROBE_OUTPUT", "").strip(),
        "FRONTEND_DIST_DIR": os.getenv("FRONTEND_DIST_DIR", "").strip(),
        "VITE_PLATFORM_ADMIN_DB": os.getenv("VITE_PLATFORM_ADMIN_DB", "").strip(),
    }

    for key, expected in EXPECTED.items():
        if observed[key] != expected:
            errors.append(f"{key} must be {expected!r}, got {observed[key]!r}")

    for key in REQUIRED_NONEMPTY:
        if not os.getenv(key, "").strip():
            errors.append(f"{key} must be set for daily acceptance release")

    for key in FORBIDDEN_OVERRIDES:
        value = os.getenv(key, "").strip()
        if value:
            errors.append(f"{key} must not be overridden for daily acceptance release, got {value!r}")

    if errors:
        print("[daily_dev_acceptance_env_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 2

    print(
        "[daily_dev_acceptance_env_guard] PASS "
        "env=dev env_file=.env.dev db=sc_demo "
        "base_url=http://127.0.0.1:18081 "
        "login=wutao "
        "nav_actions=100..115 "
        "artifact=artifacts/backend/dev_acceptance_release_probe.json "
        "dist=./frontend/apps/web/dist-dev "
        "platform_admin_db=sc_platform_core"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
