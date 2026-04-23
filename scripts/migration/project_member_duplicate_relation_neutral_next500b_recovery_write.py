"""Recovery launcher for the next500b project_member neutral carrier write."""

from __future__ import annotations

import os
from pathlib import Path


os.environ["PROJECT_MEMBER_NEUTRAL_RUN_ID"] = "ITER-2026-04-14-1975N"
os.environ["PROJECT_MEMBER_NEUTRAL_OUTPUT_TAG"] = "next500b"

SCRIPT_PATH = Path("scripts/migration/project_member_duplicate_relation_neutral_next500_write.py")
exec(compile(SCRIPT_PATH.read_text(encoding="utf-8"), str(SCRIPT_PATH), "exec"))
