#!/usr/bin/env python3
"""Aggregate the product-language guards used by frontend release targets."""

from __future__ import annotations

import business_config_user_language_guard


def main() -> int:
    injected = "普通路径不应显示：契约快照"
    if not any(phrase in injected for phrase in business_config_user_language_guard.BANNED_PHRASES):
        print("[frontend_product_language_guard] FAIL negative self-test accepted banned product wording")
        return 1
    status = business_config_user_language_guard.main()
    if status:
        return status
    print("[frontend_product_language_guard] PASS negative_self_test=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
