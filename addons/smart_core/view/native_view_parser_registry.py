from __future__ import annotations

from typing import Dict, Type

from .form_parser import FormViewParser
from .kanban_parser import KanbanViewParser
from .search_parser import SearchViewParser
from .tree_parser import TreeViewParser


_DEFAULT_ALIASES = {
    "list": "tree",
}

_PARSER_REGISTRY: Dict[str, Type] = {
    "form": FormViewParser,
    "kanban": KanbanViewParser,
    "search": SearchViewParser,
    "tree": TreeViewParser,
}


def normalize_view_type(view_type) -> str:
    key = str(view_type or "").strip().lower()
    if not key:
        return "form"
    return _DEFAULT_ALIASES.get(key, key)


def register_parser(view_type: str, parser_cls: Type) -> None:
    key = normalize_view_type(view_type)
    if not key:
        raise ValueError("view_type is required")
    _PARSER_REGISTRY[key] = parser_cls


def get_parser_class(view_type: str):
    return _PARSER_REGISTRY.get(normalize_view_type(view_type))


def list_registered_view_types() -> list[str]:
    return sorted(_PARSER_REGISTRY.keys())
