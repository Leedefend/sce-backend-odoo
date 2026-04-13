from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ParseResultV2:
    source: str
    structure: Dict[str, Any] = field(default_factory=dict)
    fields: Dict[str, Any] = field(default_factory=dict)
    modifiers: Dict[str, Any] = field(default_factory=dict)
    actions: Dict[str, Any] = field(default_factory=dict)
    widgets: Dict[str, Any] = field(default_factory=dict)
    layout: Dict[str, Any] = field(default_factory=dict)
    diagnostics: List[Dict[str, Any]] = field(default_factory=list)


class BaseParserV2:
    parser_name: str = "base"

    def parse(self, context: Dict[str, Any], source: Any) -> ParseResultV2:
        _ = context
        return ParseResultV2(source=str(source or ""))
