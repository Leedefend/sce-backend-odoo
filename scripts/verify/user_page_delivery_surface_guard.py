#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def main():
    errors = []
    page = read("frontend/apps/web/src/views/DeliveryView.vue")
    router = read("frontend/apps/web/src/router/index.ts")
    shell = read("frontend/apps/web/src/layouts/AppShell.vue")
    makefile = read("Makefile")

    required_page_terms = [
        "用户页面交付看板",
        "10 个交付模块",
        "关键旅程",
        "角色包",
        "验收证据",
        "projects.intake",
        "finance.payment_requests",
        "portal.dashboard",
    ]
    for term in required_page_terms:
        if term not in page:
            errors.append(f"DeliveryView missing {term}")

    checks = {
        "router exposes /delivery": "path: '/delivery'" in router and "DeliveryView.vue" in router,
        "shell exposes delivery board": "router.push('/delivery')" in shell and "交付看板" in shell,
        "browser acceptance target exists": "verify.user.page.delivery_surface.browser_acceptance" in makefile,
    }
    for label, ok in checks.items():
        if not ok:
            errors.append(label)

    if errors:
        print("[user_page_delivery_surface_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("[user_page_delivery_surface_guard] PASS")


if __name__ == "__main__":
    main()
