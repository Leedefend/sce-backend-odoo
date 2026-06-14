# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_INIT = REPO_ROOT / "addons" / "smart_core" / "handlers" / "system_init.py"

START_MARKER = "delivery_nav = delivery_payload.get(\"nav\") if isinstance(delivery_payload.get(\"nav\"), list) else []"
END_MARKER = "default_route_payload = data.get(\"default_route\") if isinstance(data.get(\"default_route\"), dict) else {}"

FORBIDDEN_FINAL_NAV_POSTPROCESSORS = {
    "_unwrap_internal_nav_groups(",
    "_rehome_business_master_data_nav_groups(",
    "_dedupe_nav_siblings_by_identity(",
    "_sort_business_nav_groups(",
}

REQUIRED_BOUNDARY_MARKERS = {
    '"authority": "delivery_engine_v1"',
    '"semantic_post_processing": False',
}


def main() -> None:
    source = SYSTEM_INIT.read_text(encoding="utf-8")
    start = source.find(START_MARKER)
    end = source.find(END_MARKER, start)
    if start < 0 or end < 0:
        raise SystemExit("cannot locate system.init delivery nav finalization block")
    block = source[start:end]
    forbidden = sorted(token for token in FORBIDDEN_FINAL_NAV_POSTPROCESSORS if token in block)
    if forbidden:
        raise SystemExit("system.init delivery nav block still performs semantic post-processing: %s" % forbidden)
    missing = sorted(token for token in REQUIRED_BOUNDARY_MARKERS if token not in block)
    if missing:
        raise SystemExit("system.init delivery nav boundary metadata missing: %s" % missing)
    print("OK system.init menu boundary: DeliveryEngine owns product nav semantics")


if __name__ == "__main__":
    main()
