#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

VERIFY_DIR = Path(__file__).resolve().parent
COMMON_DIR = VERIFY_DIR.parent / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from scene_legacy_contract import (  # noqa: E402
    LEGACY_SCENES_SUNSET_DATE,
    LEGACY_SCENES_SUCCESSOR,
    require_deprecation_headers,
    require_deprecation_payload,
)

__all__ = [
    "LEGACY_SCENES_SUNSET_DATE",
    "LEGACY_SCENES_SUCCESSOR",
    "require_deprecation_headers",
    "require_deprecation_payload",
]
