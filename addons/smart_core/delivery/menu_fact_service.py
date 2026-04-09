# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MenuFactSnapshot:
    flat: list[dict]
    tree: list[dict]


class MenuFactService:
    """Facts-only scanner for ir.ui.menu."""

    ACTION_MODELS = {
        "ir.actions.act_window",
        "ir.actions.server",
        "ir.actions.client",
        "ir.actions.act_url",
    }

    def __init__(self, env):
        self.env = env

    def export_visible_menu_facts(self) -> MenuFactSnapshot:
        menu_model = self.env["ir.ui.menu"]
        visible_ids = self._visible_menu_ids(menu_model)
        if not visible_ids:
            return MenuFactSnapshot(flat=[], tree=[])

        menus = menu_model.browse(sorted(visible_ids)).exists()
        raw_action_map = self._read_action_raw_map(visible_ids)
        group_xmlids = self._read_group_xmlids(menus)

        by_id: dict[int, dict] = {}
        for menu in menus:
            menu_id = int(menu.id)
            parent_id = int(menu.parent_id.id) if menu.parent_id else None
            groups = []
            for group in menu.groups_id:
                xmlid = group_xmlids.get(int(group.id))
                groups.append(
                    {
                        "id": int(group.id),
                        "xmlid": xmlid or "",
                        "name": str(group.display_name or group.name or ""),
                    }
                )
            groups.sort(key=lambda item: (item["xmlid"] or f"id:{item['id']}"))

            child_ids = [
                int(child.id)
                for child in menu.child_id.sorted(lambda row: (row.sequence or 10, row.id))
                if int(child.id) in visible_ids
            ]
            action_raw = str(raw_action_map.get(menu_id) or "").strip()
            by_id[menu_id] = {
                "menu_id": menu_id,
                "name": str(menu.name or ""),
                "parent_id": parent_id,
                "complete_name": str(menu.complete_name or ""),
                "sequence": int(menu.sequence or 0),
                "action_raw": action_raw,
                "has_action": bool(action_raw),
                "groups": groups,
                "web_icon": str(menu.web_icon or ""),
                "child_ids": child_ids,
            }

        self._attach_action_facts(by_id)

        flat = sorted(
            by_id.values(),
            key=lambda row: (
                row["complete_name"],
                row["sequence"],
                row["menu_id"],
            ),
        )
        tree = self._build_tree(by_id)
        return MenuFactSnapshot(flat=flat, tree=tree)

    def _visible_menu_ids(self, menu_model) -> set[int]:
        try:
            return {int(menu_id) for menu_id in menu_model._visible_menu_ids()}
        except Exception:
            records = menu_model.search([], order="sequence,id")
            return {int(record.id) for record in records}

    def _read_action_raw_map(self, visible_ids: set[int]) -> dict[int, str]:
        query = """
            SELECT id, action
            FROM ir_ui_menu
            WHERE id = ANY(%s)
        """
        self.env.cr.execute(query, (list(visible_ids),))
        rows = self.env.cr.fetchall()
        return {int(menu_id): str(action or "") for menu_id, action in rows}

    def _read_group_xmlids(self, menus) -> dict[int, str]:
        group_ids = list({int(group.id) for menu in menus for group in menu.groups_id})
        if not group_ids:
            return {}
        model_data = self.env["ir.model.data"].sudo().search(
            [
                ("model", "=", "res.groups"),
                ("res_id", "in", group_ids),
            ]
        )
        mapping: dict[int, str] = {}
        for row in model_data:
            mapping[int(row.res_id)] = f"{row.module}.{row.name}"
        return mapping

    def _build_tree(self, by_id: dict[int, dict]) -> list[dict]:
        children_by_parent: dict[int | None, list[int]] = {}
        for row in by_id.values():
            parent_id = row["parent_id"]
            if parent_id not in by_id:
                parent_id = None
            children_by_parent.setdefault(parent_id, []).append(row["menu_id"])

        for parent_id, rows in children_by_parent.items():
            rows.sort(key=lambda menu_id: (by_id[menu_id]["sequence"], menu_id))

        def _node(menu_id: int) -> dict:
            base = by_id[menu_id]
            return {
                "menu_id": base["menu_id"],
                "name": base["name"],
                "parent_id": base["parent_id"],
                "complete_name": base["complete_name"],
                "sequence": base["sequence"],
                "action_raw": base["action_raw"],
                "action_type": base["action_type"],
                "action_id": base["action_id"],
                "action_model": base["action_model"],
                "action_exists": base["action_exists"],
                "action_meta": base["action_meta"],
                "action_parse_error": base["action_parse_error"],
                "has_action": base["has_action"],
                "groups": base["groups"],
                "web_icon": base["web_icon"],
                "child_ids": base["child_ids"],
                "children": [_node(child_id) for child_id in children_by_parent.get(menu_id, [])],
            }

        return [_node(menu_id) for menu_id in children_by_parent.get(None, [])]

    def _attach_action_facts(self, by_id: dict[int, dict]) -> None:
        bindings: dict[int, dict] = {}
        ids_by_model: dict[str, set[int]] = {}

        for menu_id, row in by_id.items():
            parsed = self._parse_action_raw(str(row.get("action_raw") or ""))
            bindings[menu_id] = parsed
            action_model = parsed["action_model"]
            action_id = parsed["action_id"]
            if action_model and isinstance(action_id, int) and action_id > 0:
                ids_by_model.setdefault(action_model, set()).add(action_id)

        action_facts = self._read_action_facts(ids_by_model)

        for menu_id, row in by_id.items():
            parsed = bindings[menu_id]
            action_model = parsed["action_model"]
            action_id = parsed["action_id"]
            key = (action_model, action_id)
            raw_fact = action_facts.get(key)
            row["action_type"] = parsed["action_type"]
            row["action_id"] = action_id
            row["action_model"] = action_model
            row["action_exists"] = bool(raw_fact and raw_fact.get("action_exists"))
            row["action_meta"] = raw_fact.get("action_meta") if raw_fact else {}
            row["action_parse_error"] = parsed["action_parse_error"]
            if action_model and action_model not in self.ACTION_MODELS and not row["action_parse_error"]:
                row["action_parse_error"] = "unsupported_action_model"
            if row["has_action"] and action_model in self.ACTION_MODELS and not row["action_exists"] and not row["action_parse_error"]:
                row["action_parse_error"] = "action_not_found"

    def _parse_action_raw(self, action_raw: str) -> dict:
        value = str(action_raw or "").strip()
        if not value:
            return {
                "action_type": "",
                "action_id": None,
                "action_model": "",
                "action_parse_error": "",
            }
        if "," not in value:
            return {
                "action_type": "",
                "action_id": None,
                "action_model": "",
                "action_parse_error": "invalid_action_raw",
            }
        model_name, action_id_raw = value.split(",", 1)
        model_name = str(model_name or "").strip()
        try:
            action_id = int(str(action_id_raw or "").strip())
        except Exception:
            return {
                "action_type": model_name,
                "action_id": None,
                "action_model": model_name,
                "action_parse_error": "invalid_action_id",
            }
        if action_id <= 0:
            return {
                "action_type": model_name,
                "action_id": None,
                "action_model": model_name,
                "action_parse_error": "invalid_action_id",
            }
        return {
            "action_type": model_name,
            "action_id": action_id,
            "action_model": model_name,
            "action_parse_error": "",
        }

    def _read_action_facts(self, ids_by_model: dict[str, set[int]]) -> dict[tuple[str, int | None], dict]:
        out: dict[tuple[str, int | None], dict] = {}
        for model_name, action_ids in ids_by_model.items():
            ids = sorted({int(item) for item in action_ids if isinstance(item, int) and item > 0})
            if not ids:
                continue
            if model_name not in self.ACTION_MODELS:
                for action_id in ids:
                    out[(model_name, action_id)] = {
                        "action_exists": False,
                        "action_meta": {},
                    }
                continue
            records = self.env[model_name].sudo().browse(ids).exists()
            existing = {int(record.id): record for record in records}
            for action_id in ids:
                record = existing.get(action_id)
                if not record:
                    out[(model_name, action_id)] = {
                        "action_exists": False,
                        "action_meta": {},
                    }
                    continue
                out[(model_name, action_id)] = {
                    "action_exists": True,
                    "action_meta": self._build_action_meta(model_name, record),
                }
        return out

    def _build_action_meta(self, model_name: str, record) -> dict:
        if model_name != "ir.actions.act_window":
            return {}
        view_id = int(record.view_id.id) if getattr(record, "view_id", None) else None
        return {
            "res_model": str(record.res_model or ""),
            "view_mode": str(record.view_mode or ""),
            "view_id": view_id,
            "domain": str(record.domain or ""),
            "context": str(record.context or ""),
        }

    def audit_menu_facts(self, flat: list[dict]) -> dict:
        rows = [row for row in (flat or []) if isinstance(row, dict)]
        by_id = {
            int(row.get("menu_id")): row
            for row in rows
            if isinstance(row.get("menu_id"), int)
        }

        orphan_menus: list[dict] = []
        empty_menus: list[dict] = []
        invalid_action_menus: list[dict] = []
        mixed_menus: list[dict] = []
        sequence_missing: list[dict] = []
        sequence_duplicate: list[dict] = []

        sibling_sequence_index: dict[int | None, dict[int, list[int]]] = {}

        for row in rows:
            menu_id = row.get("menu_id")
            parent_id = row.get("parent_id")
            child_ids = row.get("child_ids") if isinstance(row.get("child_ids"), list) else []
            action_raw = str(row.get("action_raw") or "").strip()
            parse_error = str(row.get("action_parse_error") or "").strip()
            action_exists = bool(row.get("action_exists"))
            sequence = row.get("sequence")

            if isinstance(parent_id, int) and parent_id not in by_id:
                orphan_menus.append(self._menu_ref(row, reason="parent_not_found"))

            if not action_raw and not child_ids:
                empty_menus.append(self._menu_ref(row, reason="no_action_no_children"))

            if action_raw and (parse_error or not action_exists):
                reason = parse_error or "action_not_found"
                invalid_action_menus.append(self._menu_ref(row, reason=reason))

            if action_raw and child_ids:
                mixed_menus.append(self._menu_ref(row, reason="has_action_and_children"))

            if not isinstance(sequence, int):
                sequence_missing.append(self._menu_ref(row, reason="sequence_missing_or_invalid"))
            bucket = sibling_sequence_index.setdefault(parent_id if isinstance(parent_id, int) else None, {})
            if isinstance(sequence, int):
                bucket.setdefault(sequence, []).append(int(menu_id) if isinstance(menu_id, int) else -1)

        for parent_id, seq_map in sibling_sequence_index.items():
            for sequence, menu_ids in seq_map.items():
                valid_ids = [menu_id for menu_id in menu_ids if isinstance(menu_id, int) and menu_id > 0]
                if len(valid_ids) <= 1:
                    continue
                sequence_duplicate.append(
                    {
                        "parent_id": parent_id,
                        "sequence": sequence,
                        "menu_ids": sorted(valid_ids),
                    }
                )

        directory_menu_count = sum(
            1
            for row in rows
            if not str(row.get("action_raw") or "").strip()
        )
        action_menu_count = sum(
            1
            for row in rows
            if str(row.get("action_raw") or "").strip()
        )

        return {
            "summary": {
                "menu_total": len(rows),
                "directory_menu_count": directory_menu_count,
                "action_menu_count": action_menu_count,
                "anomaly_menu_count": len(
                    {
                        item["menu_id"]
                        for item in (orphan_menus + empty_menus + invalid_action_menus + mixed_menus)
                        if isinstance(item.get("menu_id"), int)
                    }
                ),
            },
            "anomalies": {
                "orphan_menus": orphan_menus,
                "empty_menus": empty_menus,
                "invalid_action_menus": invalid_action_menus,
                "mixed_menus": mixed_menus,
                "sequence_risk": {
                    "missing_or_invalid": sequence_missing,
                    "duplicate": sequence_duplicate,
                },
            },
        }

    def _menu_ref(self, row: dict, reason: str) -> dict:
        return {
            "menu_id": row.get("menu_id"),
            "name": row.get("name"),
            "parent_id": row.get("parent_id"),
            "complete_name": row.get("complete_name"),
            "action_raw": row.get("action_raw"),
            "reason": reason,
        }
