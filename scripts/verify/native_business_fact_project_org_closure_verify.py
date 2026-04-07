#!/usr/bin/env python3
import ast
from pathlib import Path


PROJECT_CORE = Path('addons/smart_construction_core/models/core/project_core.py')
PROJECT_MEMBER = Path('addons/smart_construction_core/models/core/project_member.py')
PROJECT_VIEW = Path('addons/smart_construction_core/views/core/project_views.xml')


def _literal(value_node):
    if isinstance(value_node, ast.Constant):
        return value_node.value
    if isinstance(value_node, ast.Str):
        return value_node.s
    return None


def _find_model_class(module_ast, model_name=None, inherit_name=None):
    for node in module_ast.body:
        if not isinstance(node, ast.ClassDef):
            continue
        attrs = {}
        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and stmt.targets and isinstance(stmt.targets[0], ast.Name):
                attrs[stmt.targets[0].id] = stmt.value
        if model_name and _literal(attrs.get('_name')) == model_name:
            return node
        if inherit_name and _literal(attrs.get('_inherit')) == inherit_name:
            return node
    return None


def _field_keywords(class_node):
    result = {}
    for stmt in class_node.body:
        if not (isinstance(stmt, ast.Assign) and stmt.targets and isinstance(stmt.targets[0], ast.Name)):
            continue
        target = stmt.targets[0].id
        call = stmt.value
        if not isinstance(call, ast.Call):
            continue
        func = call.func
        if not isinstance(func, ast.Attribute) or not isinstance(func.value, ast.Name):
            continue
        if func.value.id != 'fields':
            continue
        result[target] = {
            'field_type': func.attr,
            'keywords': {kw.arg: _literal(kw.value) for kw in call.keywords if kw.arg},
            'first_arg': _literal(call.args[0]) if call.args else None,
        }
    return result


def main():
    core_source = PROJECT_CORE.read_text(encoding='utf-8')
    core_tree = ast.parse(core_source)

    project_cls = _find_model_class(core_tree, inherit_name='project.project')
    if not project_cls:
        raise SystemExit('[native_business_fact_project_org_closure_verify] FAIL missing project.project inherit class')

    project_fields = _field_keywords(project_cls)
    key_role_fields = [
        'project_manager_user_id',
        'technical_lead_user_id',
        'business_lead_user_id',
        'cost_lead_user_id',
        'finance_contact_user_id',
    ]
    missing_roles = [field for field in key_role_fields if field not in project_fields]
    if missing_roles:
        raise SystemExit(
            '[native_business_fact_project_org_closure_verify] FAIL missing project key role fields: '
            + ','.join(missing_roles)
        )

    related_role_fields = [
        field
        for field in ('project_manager_user_id', 'business_lead_user_id', 'cost_lead_user_id')
        if project_fields[field]['keywords'].get('related')
    ]
    if related_role_fields:
        raise SystemExit(
            '[native_business_fact_project_org_closure_verify] FAIL role fields still related aliases: '
            + ','.join(related_role_fields)
        )

    member_tree = core_tree
    if PROJECT_MEMBER.exists():
        member_tree = ast.parse(PROJECT_MEMBER.read_text(encoding='utf-8'))

    member_cls = _find_model_class(member_tree, model_name='project.responsibility') or _find_model_class(
        member_tree, model_name='sc.project.member'
    )
    if not member_cls:
        raise SystemExit('[native_business_fact_project_org_closure_verify] FAIL missing project member carrier model')

    member_fields = _field_keywords(member_cls)
    required_member_fields = [
        'project_id',
        'user_id',
        'department_id',
        'post_id',
        'project_role_code',
        'is_primary',
        'active',
        'date_start',
        'date_end',
        'note',
    ]
    missing_member = [field for field in required_member_fields if field not in member_fields]
    if missing_member:
        raise SystemExit(
            '[native_business_fact_project_org_closure_verify] FAIL missing member fields: '
            + ','.join(missing_member)
        )

    pmembers = project_fields.get('project_member_ids')
    if not pmembers or pmembers['field_type'] != 'One2many':
        raise SystemExit('[native_business_fact_project_org_closure_verify] FAIL missing project_member_ids one2many')

    model_ref = pmembers['first_arg']
    if model_ref not in ('project.responsibility', 'sc.project.member'):
        raise SystemExit(
            '[native_business_fact_project_org_closure_verify] FAIL unexpected project_member_ids model: '
            + str(model_ref)
        )

    view_xml = PROJECT_VIEW.read_text(encoding='utf-8')
    for field_name in key_role_fields + ['project_member_ids']:
        if f'name="{field_name}"' not in view_xml:
            raise SystemExit(
                '[native_business_fact_project_org_closure_verify] FAIL native view missing field: '
                + field_name
            )

    print(
        '[native_business_fact_project_org_closure_verify] PASS '
        + f'key_roles={len(key_role_fields)} member_fields={len(required_member_fields)} member_model={model_ref}'
    )


if __name__ == '__main__':
    main()
