# -*- coding: utf-8 -*-
import base64
import csv
import io
import re

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import misc

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import xlrd
except ImportError:
    xlrd = None


class ProjectBoqImportWizard(models.TransientModel):
    _name = "project.boq.import.wizard"
    _description = "工程量清单导入"

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
    )
    file = fields.Binary(string="导入文件", required=True)
    filename = fields.Char("文件名")

    def action_import(self):
        self.ensure_one()
        if not self.file:
            raise UserError("请先上传导入文件。")

        rows = self._parse_file()
        if not rows:
            raise UserError(
                "未找到可导入的清单数据：\n"
                "请确认文件中至少有一行同时包含名称列（清单名称/项目名称/汇总内容等）"
                "并且数量/单价/金额至少有一个为数字。"
            )

        Boq = self.env["project.boq.line"]
        Boq.create(rows)

        return {
            "type": "ir.actions.act_window",
            "res_model": "project.boq.line",
            "view_mode": "tree,form",
            "domain": [("project_id", "=", self.project_id.id)],
            "context": {"default_project_id": self.project_id.id},
            "target": "current",
        }

    # --- helpers ---

    def _parse_file(self):
        """Parse CSV/XLS/XLSX into vals list for project.boq.line."""
        data = base64.b64decode(self.file)
        filename = (self.filename or "").lower()

        if filename.endswith((".xlsx", ".xls")):
            return self._parse_excel(data, filename)

        # 默认按 UTF-8 CSV 解析
        content = self._read_as_csv(data)
        return self._parse_csv_content(content)

    def _parse_csv_content(self, content):
        reader = csv.reader(io.StringIO(content))
        try:
            headers = [h.strip() for h in next(reader)]
        except StopIteration:
            raise UserError("导入文件没有数据，请检查。")
        col_map = self._prepare_col_map(headers)
        data_rows = list(reader)
        rows = self._build_rows_from_iter(data_rows, col_map, strict_numeric=True)
        if not rows:
            rows = self._build_rows_from_iter(data_rows, col_map, strict_numeric=False)
        return rows

    def _parse_excel(self, data, filename):
        col_map_cfg = self._col_map_cfg()
        rows_all = []

        if filename.endswith(".xlsx"):
            if not openpyxl:
                raise UserError("服务器缺少 openpyxl，无法解析 XLSX，请安装依赖或改用 CSV。")
            book = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            for sheet in book.worksheets:
                headers, start_row = self._find_header_in_sheet(
                    (list(row) for row in sheet.iter_rows(values_only=True, max_row=50))
                )
                if not headers:
                    continue
                section_type = self._guess_section_type(sheet.title or "")
                col_map = self._prepare_col_map(headers, col_map_cfg)
                data_rows = [
                    list(row)
                    for row in sheet.iter_rows(min_row=start_row + 2, values_only=True)
                ]
                rows = self._build_rows_from_iter(data_rows, col_map, section_type, strict_numeric=True)
                if not rows:
                    rows = self._build_rows_from_iter(data_rows, col_map, section_type, strict_numeric=False)
                rows_all.extend(rows)
            return rows_all

        if filename.endswith(".xls"):
            if not xlrd:
                raise UserError("服务器缺少 xlrd，无法解析 XLS，请安装依赖或改用 CSV。")
            book = xlrd.open_workbook(file_contents=data)
            for sheet in book.sheets():
                if sheet.nrows < 1:
                    continue
                headers, start_row = self._find_header_in_sheet(
                    ([sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(min(sheet.nrows, 50)))
                )
                if not headers:
                    continue
                section_type = self._guess_section_type(sheet.name or "")
                col_map = self._prepare_col_map(headers, col_map_cfg)
                data_rows = [
                    [sheet.cell_value(r, c) for c in range(sheet.ncols)]
                    for r in range(start_row + 1, sheet.nrows)
                ]
                rows = self._build_rows_from_iter(data_rows, col_map, section_type, strict_numeric=True)
                if not rows:
                    rows = self._build_rows_from_iter(data_rows, col_map, section_type, strict_numeric=False)
                rows_all.extend(rows)
            return rows_all

        # 回退：尝试按 UTF-8/GBK 解码 CSV
        return self._parse_csv_bytes(data)

    def _col_map_cfg(self):
        return {
            "code": ["清单编码", "编码", "code"],
            "name": ["清单名称", "名称", "name", "项目名称", "汇总内容"],
            "spec": ["规格", "规格型号", "项目特征", "项目特征描述"],
            "uom_id": ["单位", "uom"],
            "quantity": ["工程量", "数量", "qty"],
            "price": ["单价", "price"],
            # “金额（元）”多见于总标题，不直接当金额列匹配
            "amount": ["合价", "合计", "amount", "金额", "金额元"],
            "cost_item_id": ["成本项", "成本科目"],
            "remark": ["备注", "说明"],
        }

    def _prepare_col_map(self, headers, col_map_cfg=None):
        col_map_cfg = col_map_cfg or self._col_map_cfg()
        col_map = {}
        for idx, title in enumerate(headers):
            title_norm = self._normalize_header(title)
            for field, aliases in col_map_cfg.items():
                matched = False
                for alias in aliases:
                    alias_norm = self._normalize_header(alias)
                    if title_norm == alias_norm or title_norm.endswith(alias_norm) or alias_norm in title_norm:
                        matched = True
                        break
                if matched and field not in col_map:
                    col_map[field] = idx
                    break
        if "name" not in col_map:
            # 兜底：首列作为名称
            if headers:
                col_map["name"] = 0
            else:
                raise UserError("模板中至少需要包含 “清单名称” 列。")
        # 若识别到工程量列，按相对位置推断单价/合价（常见 F.1.1 结构：工程量右一列=单价，右二列=合价）
        qty_idx = col_map.get("quantity")
        if qty_idx is not None:
            if "price" not in col_map and qty_idx + 1 < len(headers):
                col_map["price"] = qty_idx + 1
            if "amount" not in col_map and qty_idx + 2 < len(headers):
                col_map["amount"] = qty_idx + 2
        return col_map

    def _find_header_in_sheet(self, row_iter):
        """Scan rows to find a plausible header row; return (headers, row_index)."""
        col_map_cfg = self._col_map_cfg()
        best_headers = []
        best_idx = 0
        for idx, row in enumerate(row_iter):
            headers = [str(v or "").strip() for v in row]
            if not any(headers):
                continue
            hits = 0
            for title in headers:
                title_norm = self._normalize_header(title)
                for aliases in col_map_cfg.values():
                    if any(alias in title_norm for alias in aliases):
                        hits += 1
                        break
            # 至少两列命中别名才认为是表头，避免误把说明行当表头
            if hits >= 2:
                return headers, idx
            if not best_headers:
                best_headers = headers
                best_idx = idx
        return best_headers, best_idx

    def _build_rows_from_iter(self, row_iter, col_map, section_type=None, strict_numeric=True):
        Uom = self.env["uom.uom"]
        Dict, dict_domain_key = self._get_dictionary_model()
        rows = []
        uom_cache = {}
        cost_item_cache = {}

        for row in row_iter:
            def get(field):
                idx = col_map.get(field)
                if idx is None or idx >= len(row):
                    return ""
                return row[idx] if not isinstance(row, dict) else row.get(idx)

            name = str(get("name") or "").strip()
            if not name:
                continue

            vals = {
                "project_id": self.project_id.id,
                "name": name,
            }
            if section_type:
                vals["section_type"] = section_type

            code = str(get("code") or "").strip()
            spec = str(get("spec") or "").strip()
            remark = str(get("remark") or "").strip()
            qty = get("quantity")
            price = get("price")
            amount_val = get("amount")

            if code:
                vals["code"] = code
            if spec:
                vals["spec"] = spec
            if remark:
                vals["remark"] = remark

            vals["quantity"] = self._to_float(qty)
            vals["price"] = self._to_float(price)
            vals["amount"] = self._to_float(amount_val)

            # 若数量/单价/合价均为0，则视为标题/小计行跳过
            if strict_numeric:
                if not any(
                    [
                        self._is_number(qty),
                        self._is_number(price),
                        self._is_number(amount_val),
                    ]
                ):
                    continue

            uom_name = str(get("uom_id") or "").strip()
            if uom_name:
                uom = uom_cache.get(uom_name)
                if uom is None:
                    uom = Uom.search([("name", "=", uom_name)], limit=1)
                    uom_cache[uom_name] = uom
                vals["uom_id"] = uom.id or False

            cost_item_name = str(get("cost_item_id") or "").strip()
            if cost_item_name and Dict:
                cost_item = cost_item_cache.get(cost_item_name)
                if cost_item is None:
                    if isinstance(dict_domain_key, (list, tuple)):
                        domain = list(dict_domain_key)
                    else:
                        domain = [(dict_domain_key, "=", "cost_item")]
                    domain.append(("name", "=", cost_item_name))
                    cost_item = Dict.search(domain, limit=1)
                    cost_item_cache[cost_item_name] = cost_item
                vals["cost_item_id"] = cost_item.id or False

            rows.append(vals)
        return rows

    def _read_as_csv(self, data_bytes):
        """Return CSV string from raw bytes."""
        return self._parse_csv_bytes(data_bytes)

    def _parse_csv_bytes(self, data_bytes):
        """Try utf-8, then gbk."""
        for encoding in ("utf-8", "gbk"):
            try:
                return data_bytes.decode(encoding)
            except Exception:
                continue
        raise UserError("无法解码导入文件，请确认使用 UTF-8 或 GBK 编码。")

    @staticmethod
    def _guess_section_type(sheet_title):
        title = (sheet_title or "").lower()
        mapping = {
            "build": "building",
            "建筑": "building",
            "机电": "installation",
            "安装": "installation",
            "elect": "installation",
            "装饰": "decoration",
            "decoration": "decoration",
            "景观": "landscape",
            "landscape": "landscape",
        }
        for key, val in mapping.items():
            if key in title:
                return val
        return False

    @staticmethod
    def _normalize_header(title):
        text = str(title or "").strip()
        text = re.sub(r"\s+", "", text)
        return text.lower()

    @staticmethod
    def _is_number(val):
        try:
            if isinstance(val, str):
                cleaned = ProjectBoqImportWizard._clean_number_str(val)
                if cleaned in ("", "-", "--"):
                    return False
                float(cleaned)
            else:
                float(val)
            return True
        except Exception:
            return False

    @staticmethod
    def _to_float(val):
        try:
            if isinstance(val, str):
                cleaned = ProjectBoqImportWizard._clean_number_str(val)
                return float(cleaned or 0.0)
            return float(val or 0.0)
        except Exception:
            return 0.0

    def _get_dictionary_model(self):
        """返回可用的字典模型及类型字段键。"""
        dict_model = "project.dictionary" if "project.dictionary" in self.env.registry else "sc.dictionary"
        if dict_model not in self.env.registry:
            return None, None
        Dict = self.env[dict_model]
        fields_map = Dict._fields
        if "type" in fields_map:
            return Dict, "type"
        if "type_id" in fields_map:
            return Dict, "type_id.code"
        return Dict, "type"

    @staticmethod
    def _clean_number_str(text):
        """Remove common thousand separators and spaces."""
        cleaned = str(text or "")
        cleaned = cleaned.replace(",", "").replace("，", "").replace(" ", "").strip()
        return cleaned
