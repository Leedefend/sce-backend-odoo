# -*- coding: utf-8 -*-
# smart_core/app_config_engine/services/assemblers/client_url_report.py
# 【职责】装配非数据页契约：客户端动作、URL 跳转、报表下载、诊断页
from odoo import _

class ClientUrlReportAssembler:

    def __init__(self, env):
        self.env = env

    def assemble_client_contract(self, payload, action):
        """
        客户端动作契约（前端根据 xml_id/tag 渲染）。
        - 不涉及模型数据；
        - with_data=True 时，若未来要补补充数据，可在这里扩展。
        """
        title = action.get('xml_id') or action.get('tag') or '客户端动作'
        return ({
            'head': {
                'title': title,
                'view_modes': ['client'],
                'default_view': 'client',
                'breadcrumbs': payload.get('breadcrumbs') or [],
                'context': payload.get('context') or {},
            },
            'views': {
                'client': {
                    'xml_id': action.get('xml_id'),
                    'tag': action.get('tag'),
                }
            },
            'data': {'type': 'client'}
        }, {'actions': 'v1', 'contract': 'v2'})

    def assemble_url_contract(self, payload, action):
        """
        URL 动作契约：前端收到后直接跳转到外部链接。
        """
        url = action.get('url', '') if action else ''
        target = action.get('target', 'new') if action else 'new'
        return ({
            "head": {"title": action.get('name', 'URL动作') if action else 'URL动作',
                     "view_type": "url_redirect"},
            "data": {"type": "url_redirect", "url": url, "target": target}
        }, {"url": "v1", "contract": "v2"})

    def assemble_report_contract(self, payload, action):
        """
        报表动作契约：返回报表标识，供前端拉起下载/预览。
        """
        report_name = action.get('report_name', '') if action else ''
        report_type = action.get('report_type', 'qweb-pdf') if action else 'qweb-pdf'
        return ({
            "head": {"title": action.get('name', '报表') if action else '报表',
                     "view_type": "report"},
            "data": {"type": "report",
                     "report_name": report_name,
                     "report_type": report_type,
                     "action_id": action.get('id') if action else None}
        }, {"report": "v1", "contract": "v2"})

    def assemble_diagnostic_contract(self, payload, action=None, issue="未知问题"):
        """
        诊断页面契约：用于提示动作配置问题（缺模型/物化失败/不支持类型等）。
        """
        action_info = {
            "action_id": action.get('id') if action else None,
            "action_type": action.get('type') if action else None,
            "action_name": action.get('name') if action else None,
            "action_xml_id": action.get('xml_id') if action else None,
            "issue": issue,
        }
        return ({
            "head": {"title": f"配置问题: {action.get('name', '未知动作') if action else '未知动作'}",
                     "model": None, "view_type": "diagnostic"},
            "ui": {"i18n": {
                "error_title": "动作配置错误",
                "error_message": issue,
                "suggestion": "请联系系统管理员检查动作配置"
            }},
            "data": {"type": "diagnostic", "info": action_info}
        }, {"diagnostic": True, "contract": "v2"})
