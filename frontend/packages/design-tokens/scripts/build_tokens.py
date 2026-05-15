#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "tokens"
PLATFORMS = ROOT / "platform"
DIST_WEB = ROOT / "dist" / "web"
DIST_SHARED = ROOT / "dist" / "shared"
REF_PATTERN = re.compile(r"\{([a-zA-Z0-9_.]+)\}")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten(prefix: str, obj: dict[str, Any], out: dict[str, Any]) -> None:
    for k, v in obj.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            flatten(key, v, out)
        else:
            out[key] = v


def to_css_var_key(token_key: str) -> str:
    return "--sc-" + token_key.replace(".", "-").replace("_", "-")


def _lookup_ref_key(ref: str) -> str:
    if ref.startswith(("base.", "semantic.", "component.", "platform.")):
        return ref
    return f"base.{ref}"


def resolve_refs(tokens: dict[str, Any], *, strict: bool = True) -> dict[str, Any]:
    resolved = dict(tokens)

    def _resolve_token(token_key: str, stack: list[str]) -> Any:
        if token_key in stack:
            raise ValueError(f"circular reference detected: {' -> '.join(stack + [token_key])}")
        if token_key not in resolved:
            raise KeyError(f"missing token key: {token_key}")
        value = resolved[token_key]
        return _resolve_value(value, stack + [token_key])

    def _resolve_value(v: Any, stack: list[str]) -> Any:
        if not isinstance(v, str):
            return v
        matches = list(REF_PATTERN.finditer(v))
        if not matches:
            return v

        # whole-token reference -> preserve referenced type (number/bool/string)
        if len(matches) == 1 and matches[0].span() == (0, len(v)):
            ref = matches[0].group(1)
            lookup = _lookup_ref_key(ref)
            if lookup not in resolved:
                if strict:
                    raise KeyError(f"missing token reference: {ref} (lookup={lookup})")
                return v
            return _resolve_token(lookup, stack)

        # inline reference in string -> cast replacement to string
        def _replace(m: re.Match[str]) -> str:
            ref = m.group(1)
            lookup = _lookup_ref_key(ref)
            if lookup not in resolved:
                if strict:
                    raise KeyError(f"missing token reference: {ref} (lookup={lookup})")
                return m.group(0)
            rv = _resolve_token(lookup, stack)
            return str(rv)

        return REF_PATTERN.sub(_replace, v)

    out: dict[str, Any] = {}
    for key in list(resolved.keys()):
        out[key] = _resolve_token(key, [])
    return out


def to_css_vars(mapping: dict[str, Any], selector: str = ":root") -> str:
    lines = [f"{selector} {{"]
    for key in sorted(mapping.keys()):
        lines.append(f"  {to_css_var_key(key)}: {mapping[key]};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def validate_flat_tokens(flat: dict[str, Any]) -> None:
    required_keys = (
        "semantic.surface.page",
        "semantic.border.default",
        "semantic.focus.ring",
        "semantic.state.danger_bg",
        "semantic.text.primary",
        "component.button.height_md",
        "component.input.height_md",
        "component.toolbar.gap",
    )
    for key in required_keys:
        if key not in flat:
            raise ValueError(f"required token missing: {key}")


def build_variant(*, semantic_file: str, platform: str | None, strict: bool) -> dict[str, Any]:
    base = load_json(TOKENS / "base.json")
    semantic = load_json(TOKENS / semantic_file)
    component = load_json(TOKENS / "component.json")
    merged: dict[str, Any] = {"base": base, "semantic": semantic, "component": component}
    if platform:
        merged["platform"] = load_json(PLATFORMS / f"{platform}.json")

    flat: dict[str, Any] = {}
    flatten("", merged, flat)
    resolved = resolve_refs(flat, strict=strict)
    validate_flat_tokens(resolved)
    return resolved


def write_outputs(light_web: dict[str, Any], dark_web: dict[str, Any], mobile_light: dict[str, Any], mini_light: dict[str, Any]) -> None:
    DIST_WEB.mkdir(parents=True, exist_ok=True)
    DIST_SHARED.mkdir(parents=True, exist_ok=True)

    (DIST_WEB / "tokens.light.css").write_text(to_css_vars(light_web, selector=":root"), encoding="utf-8")
    (DIST_WEB / "tokens.dark.css").write_text(to_css_vars(dark_web, selector=":root[data-sc-theme=\"dark\"]"), encoding="utf-8")
    (DIST_WEB / "tokens.css").write_text(to_css_vars(light_web, selector=":root"), encoding="utf-8")

    ts_payload = {
        "light": light_web,
        "dark": dark_web,
        "mobile_light": mobile_light,
        "mini_light": mini_light,
    }
    ts = "export const tokenVariants = " + json.dumps(ts_payload, ensure_ascii=False, indent=2) + " as const;\n"
    ts += "export const tokens = tokenVariants.light;\n"
    (DIST_SHARED / "tokens.ts").write_text(ts, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build design tokens for multi-platform outputs.")
    parser.add_argument("--no-strict", action="store_true", help="Do not fail on unresolved token references.")
    args = parser.parse_args()
    strict = not args.no_strict

    light_web = build_variant(semantic_file="semantic.light.json", platform="web", strict=strict)
    dark_web = build_variant(semantic_file="semantic.dark.json", platform="web", strict=strict)
    mobile_light = build_variant(semantic_file="semantic.light.json", platform="mobile", strict=strict)
    mini_light = build_variant(semantic_file="semantic.light.json", platform="mini", strict=strict)

    write_outputs(light_web, dark_web, mobile_light, mini_light)

    print("[design-tokens] generated:", DIST_WEB / "tokens.css")
    print("[design-tokens] generated:", DIST_WEB / "tokens.light.css")
    print("[design-tokens] generated:", DIST_WEB / "tokens.dark.css")
    print("[design-tokens] generated:", DIST_SHARED / "tokens.ts")


if __name__ == "__main__":
    main()
