# -*- coding: utf-8 -*-
# smart_core/app_config_engine/utils/view_utils.py
# 【职责】视图工具：
#   - extract_tree_columns_strict：从 <tree> 严格提取列（按 XML 顺序，仅可渲染）；
#   - normalize_cols_safely：将 columns 正常化/回退，过滤隐字段/one2many。
import logging
from lxml import etree

_logger = logging.getLogger(__name__)

# 在 list 视图里一般不直接渲染 one2many；防止 read 时返回大批量嵌套数据
TREE_EXCLUDE_TYPES = {'one2many'}
# 这些字段经常是内部逻辑/活动跟踪，不适合默认展示在列表中
TREE_EXCLUDE_NAMES = {'activity_ids', 'my_activity_date_deadline', 'task_properties'}

def extract_tree_columns_strict(arch_db: str, fields_map: dict):
    """
    从 <tree> arch 中严格提取列（按 XML 顺序），只保留可见、可渲染字段。
    返回：([{'name','label','type',...}, ...], default_order or None)
    设计要点：
    - 仅处理 <tree> 根节点；
    - 过滤 one2many 与隐列（invisible="1|true"）；
    - label 优先取 node.string，其次字段 string，最后回退为 name；
    - 返回 columns 为“富列定义”（含 widget/sortable 等），供前端或契约使用；
    - default_order 从 <tree default_order="..."> 读取。
    """
    if not arch_db:
        return [], None
    try:
        root = etree.fromstring(arch_db.encode('utf-8'))
    except Exception as e:
        _logger.warning("extract_tree_columns_strict parse error: %s", e)
        return [], None
    if root.tag != 'tree':
        return [], None

    default_order = root.get('default_order') or None
    cols = []
    for node in root.findall('.//field'):
        name = node.get('name')
        if not name or name in TREE_EXCLUDE_NAMES:
            continue
        f = fields_map.get(name)
        if not f:
            continue
        ftype = f.get('type')
        if ftype in TREE_EXCLUDE_TYPES:
            continue
        # 处理不可见：仅识别最常见的布尔不可见（复杂 modifiers 可后续扩展）
        invisible_attr = node.get('invisible')
        invisible = str(invisible_attr).lower() in ('1','true') if invisible_attr is not None else False
        if invisible:
            continue
        label = node.get('string') or f.get('string') or name
        # 粗粒度的排序能力提示：多数基础类型允许排序
        sortable = ftype in {'char','text','integer','float','monetary','many2one','selection','date','datetime','boolean'}
        cols.append({
            'name': name,
            'label': label,
            'type': ftype,
            'readonly': bool(f.get('readonly')),
            'required': bool(f.get('required')),
            'invisible': False,
            'optional': node.get('optional') or '',
            'widget': node.get('widget') or '',
            'sortable': sortable,
        })
    return cols, default_order

def normalize_cols_safely(cols, fields_map):
    """
    将 columns 统一为“字段名列表”并过滤无效项：
    - 若传入 cols 非空 → 按其顺序过滤出有效字段名（严格保持顺序）；
    - 否则给出“干净回退列”：业务常用字段优先 + 补齐 id；
    - 过滤 one2many/内部隐字段，保证列表可渲染与读性能。
    """
    if cols:
        # 兼容富列定义 dict → name；或直接是字符串
        valid = [c if isinstance(c, str) else c.get('name') for c in cols]
        valid = [c for c in valid if c in fields_map]
        if valid:
            return valid

    # 回退策略：业务字段优先（按经验常用），再补若干非系统字段，最后确保包含 id
    field_keys = list(fields_map.keys())
    business_fields = ['sequence','name','display_name','partner_id','company_id','date_start','date','user_id','tag_ids','stage_id']
    priority_fields = [f for f in business_fields if f in field_keys]
    other_fields = [k for k,v in fields_map.items()
                    if not k.startswith(('message_','activity_','__'))   # 过滤系统/活动字段
                    and k not in priority_fields
                    and v.get('type') not in TREE_EXCLUDE_TYPES
                    and k not in TREE_EXCLUDE_NAMES]
    fallback = priority_fields + other_fields[: max(0, 10 - len(priority_fields))]
    if fallback and 'id' not in fallback:
        fallback.append('id')
    _logger.info("normalize_cols_safely: fallback=%s", fallback)
    return fallback or ['id']
