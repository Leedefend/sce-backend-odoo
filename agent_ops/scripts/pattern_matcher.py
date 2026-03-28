#!/usr/bin/env python3
from __future__ import annotations

import fnmatch
import re


def match_paths(files: list[str], patterns: list[str]) -> list[dict[str, str]]:
    matched: list[dict[str, str]] = []
    for file_path in files:
        for pattern in patterns:
            if fnmatch.fnmatch(file_path, pattern):
                matched.append({"path": file_path, "pattern": pattern})
    return matched


def match_patterns(diff_text: str, regex_list: list[str]) -> list[str]:
    matched: list[str] = []
    for pattern in regex_list:
        if re.search(pattern, diff_text, flags=re.MULTILINE):
            matched.append(pattern)
    return matched
