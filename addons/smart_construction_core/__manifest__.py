# -*- coding: utf-8 -*-
# pyright: reportUnusedExpression=false
{
    'name': 'Smart Construction Core',
    'version': '17.0.0.1',
    'summary': 'Core module for construction enterprise management (Architecture 2.0)',
    'author': 'Leedefend',
    'depends': [
        'project',
        'purchase',
        'stock',
        'account',
        'mail',
        'uom',
        'product',
        'web',
    ],
    'data': [
        # 基础数据
        #'data/sequence.xml',
        'data/dictionary_demo.xml',
        'data/cost_demo.xml',
        'data/project_stage_data.xml',

        # 安全
        'security/sc_groups.xml',
        'security/sc_model_records.xml',
        'security/ir.model.access.csv',

        # 视图
        'views/dictionary_views.xml',
        'views/cost_domain_views.xml',
        'views/project_boq_import_views.xml',
        'views/project_task_from_boq_views.xml',
        'views/project_structure_views.xml',
        'actions/project_structure_actions.xml',
        'views/project_views.xml',
        'views/boq_views.xml',
        'views/task_boq_views.xml',
        'views/work_breakdown_views.xml',
        'views/tender_views.xml',
        'views/document_views.xml',
        'views/project_dashboard_kanban.xml',
        'views/contract_views.xml',
        'views/purchase_extend_views.xml',
        'views/account_extend_views.xml',
        'views/product_extend_views.xml',
        'views/menu.xml',
    ],
    'demo': [
        # 如需演示数据再启用
        # 'data/cost_domain_demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
