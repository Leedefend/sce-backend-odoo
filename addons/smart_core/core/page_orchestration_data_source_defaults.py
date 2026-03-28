# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import Any, Dict


def to_text(value: Any) -> str:
    return str(value or "").strip()


def build_section_data_source_key(section_key: str) -> str:
    token = re.sub(r"[^a-z0-9_]+", "_", to_text(section_key).lower())
    token = re.sub(r"_+", "_", token).strip("_")
    if not token:
        token = "section"
    return f"ds_section_{token}"


def build_base_data_sources() -> Dict[str, Dict[str, Any]]:
    return {
        "ds_sections": {"source_type": "static", "provider": "page_contract.sections", "section_keys": ["_all"]},
    }


def build_section_data_source(page_key: str, section_key: str, section_tag: str) -> Dict[str, Any]:
    return {
        "source_type": "scene_context",
        "provider": "page_contract.section",
        "page_key": to_text(page_key),
        "section_key": to_text(section_key),
        "section_tag": to_text(section_tag).lower() or "section",
        "section_keys": [to_text(section_key)],
    }
