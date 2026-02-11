#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations


def require_ok(status: int, payload: dict, label: str) -> None:
    if status >= 400 or not payload.get("ok"):
        raise RuntimeError(f"{label} failed: status={status} payload={payload}")
