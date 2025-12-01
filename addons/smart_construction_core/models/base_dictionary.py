# -*- coding: utf-8 -*-
from odoo import models, fields


class ScDictionary(models.Model):
    """
    全局业务字典:
      - project_type  项目类型
      - cost_item     成本项
      - uom           计量单位
      - doc_type      工程资料大类
      - doc_subtype   工程资料细类
      - expense_type  费用类别
      - contract_type     合同方向（收入/支出）
      - contract_category 合同类别（施工、监理、材料采购等）
    """
    _name = 'sc.dictionary'
    _description = 'Smart Construction Dictionary'
    _order = 'type, sequence, name'

    name = fields.Char('名称', required=True)
    code = fields.Char('编码', help='可选业务编码')

    type = fields.Selection([
        ('project_type', '项目类型'),
        ('project_category', '项目类别'),
        ('cost_item', '成本项'),
        ('uom', '计量单位'),
        ('doc_type', '工程资料大类'),
        ('doc_subtype', '工程资料细类'),
        ('expense_type', '费用类别'),
        ('contract_type', '合同方向'),
        ('contract_category', '合同类别'),
    ], string='字典类型', required=True, index=True)

    sequence = fields.Integer('排序', default=10)
    active = fields.Boolean('启用', default=True)

    _sql_constraints = [
        (
            'sc_dict_code_type_uniq',
            'unique(code, type)',
            '同一字典类型下，编码不能重复。',
        ),
    ]
