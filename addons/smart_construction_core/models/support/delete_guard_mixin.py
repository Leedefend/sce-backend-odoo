# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import api, models
from odoo.exceptions import UserError


class ScDeleteGuardMixin(models.AbstractModel):
    _name = "sc.delete.guard.mixin"
    _description = "通用删除保护"

    _sc_delete_guard_blocker_models = ()
    _sc_delete_guard_ignore_models = ()
    _sc_delete_guard_include_models = ()

    @api.model
    def _sc_delete_guard_table_exists(self, table_name):
        table_name = str(table_name or "").strip()
        if not table_name:
            return False
        self.env.cr.execute("SELECT to_regclass(%s)", (table_name,))
        return bool(self.env.cr.fetchone()[0])

    @api.model
    def _sc_delete_guard_field_rows(self):
        rows = self.env["ir.model.fields"].sudo().search(
            [
                ("relation", "=", self._name),
                ("store", "=", True),
                ("ttype", "=", "many2one"),
            ]
        )
        allowed = set(self._sc_delete_guard_blocker_models or ())
        ignored = set(self._sc_delete_guard_ignore_models or ())
        included = set(self._sc_delete_guard_include_models or ())
        out = []
        seen = set()
        for field in rows:
            model_name = str(field.model or "").strip()
            field_name = str(field.name or "").strip()
            on_delete = str(field.on_delete or "").strip().lower()
            if not model_name or not field_name:
                continue
            if on_delete in {"cascade", "set null"} and model_name not in included:
                continue
            if allowed and model_name not in allowed:
                continue
            if model_name in ignored:
                continue
            key = (model_name, field_name)
            if key in seen:
                continue
            seen.add(key)
            out.append((model_name, field_name))
        return out

    @api.model
    def _sc_delete_guard_dependency_summary(self, record_ids):
        record_ids = [int(record_id) for record_id in (record_ids or []) if int(record_id or 0) > 0]
        if not record_ids:
            return {}
        summary = defaultdict(list)
        aggregated = defaultdict(dict)
        for model_name, field_name in self._sc_delete_guard_field_rows():
            if model_name not in self.env:
                continue
            Model = self.env[model_name].sudo().with_context(active_test=False)
            if not self._sc_delete_guard_table_exists(getattr(Model, "_table", "")):
                continue
            label = str(getattr(Model, "_description", "") or model_name).strip() or model_name
            for record_id in record_ids:
                domain = [(field_name, "=", record_id)]
                if model_name == self._name:
                    domain.append(("id", "!=", record_id))
                count = int(Model.search_count(domain) or 0)
                if count <= 0:
                    continue
                bucket = aggregated[record_id].setdefault(
                    model_name,
                    {"model": model_name, "field": field_name, "label": label, "count": 0},
                )
                bucket["count"] += count
        for record_id, by_model in aggregated.items():
            summary[record_id] = list(by_model.values())
        return summary

    def _sc_delete_guard_record_kind_label(self):
        return str(self._description or self._name or "记录").strip() or "记录"

    def _sc_raise_delete_blockers(self, *, action_label="删除"):
        summary = self._sc_delete_guard_dependency_summary(self.ids)
        if not summary:
            return
        lines = []
        for record in self:
            blockers = sorted(
                summary.get(record.id, []),
                key=lambda item: (-int(item.get("count", 0)), str(item.get("label", "")), str(item.get("field", ""))),
            )
            if not blockers:
                continue
            joined = "、".join(
                f"{item['label']}({int(item['count'])})"
                for item in blockers[:8]
            )
            lines.append(f"{self._sc_delete_guard_record_kind_label()}[{record.display_name}] 仍有关联业务数据：{joined}")
        if lines:
            raise UserError(f"无法{action_label}。\n" + "\n".join(lines))
