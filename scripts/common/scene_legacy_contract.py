#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations


LEGACY_SCENES_SUNSET_DATE = "2026-04-30"
LEGACY_SCENES_SUCCESSOR = "/api/v1/intent"


def require_deprecation_payload(payload: dict, *, label: str) -> None:
    dep = payload.get("deprecation") if isinstance(payload.get("deprecation"), dict) else {}
    if (dep.get("status") or "").strip().lower() != "deprecated":
        raise RuntimeError(f"{label} missing deprecation.status=deprecated")
    if not str(dep.get("replacement") or "").strip():
        raise RuntimeError(f"{label} missing deprecation.replacement")
    sunset_date = str(dep.get("sunset_date") or "").strip()
    if sunset_date != LEGACY_SCENES_SUNSET_DATE:
        raise RuntimeError(f"{label} invalid deprecation.sunset_date: {sunset_date}")


def require_deprecation_headers(headers: dict, *, label: str) -> None:
    dep_header = str(headers.get("Deprecation") or headers.get("deprecation") or "").strip().lower()
    if dep_header != "true":
        raise RuntimeError(f"{label} missing Deprecation header=true")
    sunset_header = str(headers.get("Sunset") or headers.get("sunset") or "").strip()
    if not sunset_header:
        raise RuntimeError(f"{label} missing Sunset header")
    if "GMT" not in sunset_header:
        raise RuntimeError(f"{label} Sunset header must be GMT: {sunset_header}")
    link_header = str(headers.get("Link") or headers.get("link") or "").strip()
    if "successor-version" not in link_header or LEGACY_SCENES_SUCCESSOR not in link_header:
        raise RuntimeError(f"{label} missing Link successor-version header")
