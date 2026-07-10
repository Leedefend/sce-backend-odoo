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
    "ACCEPTANCE_NAV_REQUIRED_PATHS": "智慧施工管理平台 / 基础资料 / 客户,智慧施工管理平台 / 基础资料 / 供应商,智慧施工管理平台 / 项目中心 / 项目管理 / 项目台账,智慧施工管理平台 / 合同中心 / 支出合同台账 / 一般合同（公司）,智慧施工管理平台 / 施工管理 / 施工日志,智慧施工管理平台 / 物资与分包 / 材料管理 / 入库单,智慧施工管理平台 / 财务中心 / 收付款办理 / 支付申请,智慧施工管理平台 / 财务中心 / 资金往来办理 / 资金日报表,智慧施工管理平台 / 人事行政 / 项目管理人员工资登记,智慧施工管理平台 / 资料证照 / 公司资料存档,智慧施工管理平台 / 税务中心 / 进项发票,智慧施工管理平台 / 配置中心 / 低代码系统配置 / 菜单配置",
    "ACCEPTANCE_NAV_REQUIRED_ACTIONS": "智慧施工管理平台 / 基础资料 / 客户=>786|智慧施工管理平台 / 基础资料 / 供应商=>787|智慧施工管理平台 / 项目中心 / 项目管理 / 项目台账=>506|智慧施工管理平台 / 合同中心 / 支出合同台账 / 一般合同（公司）=>669|智慧施工管理平台 / 施工管理 / 施工日志=>701|智慧施工管理平台 / 物资与分包 / 材料管理 / 入库单=>983|智慧施工管理平台 / 财务中心 / 收付款办理 / 支付申请=>780|智慧施工管理平台 / 财务中心 / 资金往来办理 / 资金日报表=>784|智慧施工管理平台 / 人事行政 / 项目管理人员工资登记=>862|智慧施工管理平台 / 资料证照 / 公司资料存档=>615|智慧施工管理平台 / 税务中心 / 进项发票=>756|智慧施工管理平台 / 配置中心 / 低代码系统配置 / 菜单配置=>841",
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
