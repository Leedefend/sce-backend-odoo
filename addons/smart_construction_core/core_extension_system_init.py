# -*- coding: utf-8 -*-
from typing import Any


def apply_system_init_profile_overrides(data: dict[str, Any], ext_facts: dict[str, Any]) -> dict[str, Any]:
    workspace_keyword_overrides = ext_facts.get("workspace_keyword_overrides")
    if not isinstance(workspace_keyword_overrides, dict):
        workspace_keyword_overrides = {}
    business_action_scene_labels = dict(
        workspace_keyword_overrides.get("business_action_scene_labels")
        if isinstance(workspace_keyword_overrides.get("business_action_scene_labels"), dict)
        else {}
    )
    business_action_scene_labels.update(
        {
            "finance.payment_requests": "支付申请",
            "project.management": "项目管理",
            "projects.dashboard": "项目管理",
            "risk.center": "风险中心",
            "workspace.risk": "风险中心",
        }
    )
    token_labels = list(
        workspace_keyword_overrides.get("business_action_title_token_labels")
        if isinstance(workspace_keyword_overrides.get("business_action_title_token_labels"), list)
        else []
    )
    token_labels.extend(
        [
            {"token": "支付", "label": "支付申请"},
            {"token": "项目", "label": "项目管理"},
            {"token": "风险", "label": "风险中心"},
        ]
    )
    token_sets = dict(
        workspace_keyword_overrides.get("token_sets")
        if isinstance(workspace_keyword_overrides.get("token_sets"), dict)
        else {}
    )
    token_sets.update(
        {
            "build_urgent_capability_tokens": [
                "risk",
                "approval",
                "payment",
                "settlement",
                "风险",
                "审批",
                "支付",
                "结算",
            ],
            "build_risk_semantic_tokens": [
                "risk",
                "alert",
                "warning",
                "exception",
                "overdue",
                "blocked",
                "critical",
                "urgent",
                "payment",
                "cost",
                "contract",
                "delay",
                "风险",
                "预警",
                "异常",
                "逾期",
                "阻塞",
                "严重",
                "紧急",
                "支付",
                "成本",
                "合同",
                "延期",
            ],
        }
    )
    source_scene_routes = dict(
        workspace_keyword_overrides.get("source_scene_routes")
        if isinstance(workspace_keyword_overrides.get("source_scene_routes"), dict)
        else {}
    )
    source_scene_routes.update(
        {
            "cost": "workspace.cost",
            "boq": "workspace.cost",
            "成本": "workspace.cost",
            "payment": "workspace.home",
            "finance": "workspace.home",
            "支付": "workspace.home",
            "财务": "workspace.home",
            "project": "workspace.list",
            "项目": "workspace.list",
        }
    )
    workspace_keyword_overrides["business_action_scene_labels"] = business_action_scene_labels
    workspace_keyword_overrides["business_action_title_token_labels"] = token_labels
    workspace_keyword_overrides["token_sets"] = token_sets
    workspace_keyword_overrides["source_scene_routes"] = source_scene_routes
    workspace_keyword_overrides["extension_collection_keys"] = [
        "today_actions",
        "tasks",
        "project_actions",
        "task_items",
        "payment_requests",
        "risk_actions",
        "risk",
        "project_tasks",
    ]
    workspace_keyword_overrides["preferred_business_sources"] = [
        "today_actions",
        "tasks",
        "project_actions",
        "task_items",
        "payment_requests",
        "risk_actions",
        "risk",
        "project_tasks",
    ]
    ext_facts["workspace_keyword_overrides"] = workspace_keyword_overrides
    page_profile_overrides = ext_facts.get("page_profile_overrides")
    if not isinstance(page_profile_overrides, dict):
        page_profile_overrides = {}
    page_texts = page_profile_overrides.get("page_texts") if isinstance(page_profile_overrides.get("page_texts"), dict) else {}
    login_texts = dict(page_texts.get("login") if isinstance(page_texts.get("login"), dict) else {})
    login_texts.update(
        {
            "brand_name": "智能施工企业管理平台",
            "brand_subtitle": "工程项目全生命周期管理系统",
            "brand_slogan": "让项目透明 · 让合同可控 · 让资金协同 · 让风险可预警",
            "capability_project": "项目全过程管理",
            "capability_contract_cost": "合同成本联动",
            "capability_fund": "资金支付协同",
            "capability_risk": "风险预警驾驶舱",
            "value_line_1": "让项目透明",
            "value_line_2": "让合同可控",
            "value_line_3": "让资金协同",
            "value_line_4": "让风险可预警",
        }
    )
    home_texts = dict(page_texts.get("home") if isinstance(page_texts.get("home"), dict) else {})
    home_texts.update(
        {
            "hero_lead": "围绕项目经营、风险与审批，优先处理今天最关键事项。",
            "todo_label_approval": "审核付款申请",
            "todo_label_contract": "查看合同异常",
            "todo_keywords_approval": "付款,支付,approval,审批",
            "todo_keywords_contract": "合同,contract",
            "action_enter_approval": "审核付款申请",
            "action_enter_contract": "查看合同异常",
            "action_enter_keywords_approval": "payment,付款,支付,approval,审批",
            "action_enter_keywords_contract": "contract,合同",
        }
    )
    my_work_texts = dict(page_texts.get("my_work") if isinstance(page_texts.get("my_work"), dict) else {})
    my_work_texts.update(
        {
            "action_view_project": "查看项目",
            "model_label_project_task": "项目任务",
            "model_label_project_project": "项目主数据",
        }
    )
    action_texts = dict(page_texts.get("action") if isinstance(page_texts.get("action"), dict) else {})
    action_texts.update(
        {
            "intent_title_contract": "合同执行：优先识别付款与变更风险",
            "intent_summary_contract": "先看执行率与付款状态，再进入异常合同处理。",
            "intent_action_contract_todo": "处理合同待办",
            "empty_title_contract": "当前暂无合同记录",
            "empty_hint_contract": "可前往“我的工作”查看合同待办，或进入风险驾驶舱追踪履约风险。",
            "primary_action_contract": "处理合同待办",
            "intent_title_project": "项目视角：先判断是否可控",
            "intent_action_project_todo": "查看项目待办",
            "empty_title_project": "当前暂无项目记录",
            "empty_hint_project": "建议进入“我的工作”处理项目待办，或去风险驾驶舱查看全局状态。",
            "primary_action_project": "查看项目待办",
            "empty_reason_wbs": "当前尚未生成执行结构数据，可先在项目立项或工程结构中创建后再查看。",
            "intent_title_cost": "成本执行：先回答是否超支",
            "intent_summary_cost": "优先关注超支金额与超支项，再下钻到具体偏差来源。",
            "intent_action_cost_todo": "处理成本待办",
            "empty_title_cost": "当前暂无成本记录",
            "empty_hint_cost": "可前往“我的工作”处理成本待办，或进入风险驾驶舱继续巡检。",
            "primary_action_cost": "处理超支待办",
            "surface_kind_keywords_contract": "contract,合同",
            "surface_kind_keywords_cost": "cost,成本",
            "surface_kind_keywords_project": "project,项目",
            "columns_contract_bucket_amount": "amount_total,contract_amount,金额,合同额",
            "columns_contract_bucket_payment": "paid,payment,付款,支付",
            "columns_contract_bucket_identity": "title,name,合同",
            "columns_cost_bucket_overrun": "over,overrun,超支,偏差",
            "columns_cost_bucket_identity": "title,name,项目",
            "columns_project_bucket_identity": "title,name,项目",
            "columns_project_bucket_payment": "payment,付款",
            "columns_project_bucket_cost": "cost,成本",
        }
    )
    record_texts = dict(page_texts.get("record") if isinstance(page_texts.get("record"), dict) else {})
    record_texts.update(
        {
            "summary_status_stage": "项目执行阶段",
            "next_action_contract": "查看合同",
            "next_action_cost": "查看成本",
            "fallback_details_title": "项目详情",
            "project_pay_prefix": "付款比 ",
            "project_pay_unset": "付款比未配置",
        }
    )
    page_texts.update({"login": login_texts, "home": home_texts, "my_work": my_work_texts, "action": action_texts, "record": record_texts})
    page_profile_overrides["page_texts"] = page_texts
    ext_facts["page_profile_overrides"] = page_profile_overrides
    data["ext_facts"] = ext_facts
    return data

