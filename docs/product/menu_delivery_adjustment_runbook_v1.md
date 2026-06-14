# 自定义前端菜单调整运行手册 v1

本文档记录施工产品自定义前端菜单的真实生效链路。以后调整菜单时，按本文档逐层处理和验证，避免只改一层导致前端看起来没有变化。

## 结论

自定义前端登录后显示的菜单不是直接读取 Odoo 原生 `ir.ui.menu`。

真实链路是：

1. `ir.ui.menu` / `ir.actions.*`
   - Odoo 原生菜单与动作。
   - 决定菜单是否有动作、动作模型、用户组可见性。
2. `app.menu.config`
   - 原生菜单投影缓存。
   - `system.init` 会通过 `NavDispatcher` 读取它作为 native nav。
3. `sc.product.policy.menu_groups`
   - 产品发布菜单事实。
   - 决定自定义前端产品菜单名称、业务域、合并策略、业务类型、`visible_menu_path`。
4. `DeliveryEngine` / `MenuService`
   - 把产品策略和 native nav 合成为 `delivery_engine_v1.nav`。
   - 产品策略是发布面权威来源；native nav 用于授权和补充。
5. `system.init`
   - 只做运行时安全过滤和契约透传。
   - 允许处理：发布门禁、显式开启的用户验收投影、显式开启的用户菜单配置覆盖。
   - 不允许默认处理：业务菜单改名、搬家、解包、去重合并、业务排序。
   - 最终写入 `release_navigation_v1.nav` 和顶层 `nav`。
6. 自定义前端
   - 登录后调用 `/api/v1/intent` 的 `system.init`。
   - 优先消费 `release_navigation_v1.nav`，其次 `delivery_engine_v1.nav`，最后才是旧 `result.nav`。

## 职责边界

### `ir.ui.menu` / `ir.actions.*`

负责 Odoo 原生事实：

- 菜单和动作是否存在。
- action 模型是否正确。
- 原生用户组和模型权限是否允许用户访问。

不负责自定义前端产品菜单的最终分组、显示名称和业务合并策略。

### `app.menu.config`

负责把原生菜单投影成 native nav，供 DeliveryEngine 校验授权和补齐动作信息。

不负责产品发布菜单语义。

### `sc.product.policy`

负责产品发布事实：

- 哪些菜单进入产品发布面。
- 前端显示名和 `visible_menu_path`。
- 业务域、业务类型、合并策略、默认分类、允许分类。
- 合并入口的 `integration_target`。

新增、移动、拆分、合并业务入口，优先改这里。

### `DeliveryEngine` / `MenuService`

负责把产品发布事实编译成最终产品导航：

- 按 `visible_menu_path` 生成前端层级。
- 用 native nav 做授权校验和 action 补齐。
- 生成合并入口、业务类型元数据、入口目标。
- 输出可直接给前端使用的 `delivery_engine_v1.nav`。

这里是产品菜单语义的最后加工层。

### `system.init`

负责登录初始化契约：

- 生成 `edition_runtime_v1`、`release_navigation_v1`、`nav_meta` 等响应结构。
- 在发布门禁启用时过滤未发布入口。
- 在 `smart_core.nav.user_data_acceptance_only` 显式启用时投影用户验收菜单。
- 在 `smart_core.nav.user_menu_config.enabled` 显式启用时应用用户菜单配置覆盖。

默认不得再对产品菜单做语义后处理。禁止在这里新增菜单搬家、解包、去重合并、业务排序规则。

### `system.init` 边界守护

每次调整菜单链路后运行：

```bash
python3 scripts/verify/system_init_menu_boundary_guard.py
```

该脚本会检查 `system.init` 的 DeliveryEngine 发布块没有重新引入以下后处理：

- `_unwrap_internal_nav_groups`
- `_rehome_business_master_data_nav_groups`
- `_dedupe_nav_siblings_by_identity`
- `_sort_business_nav_groups`

## 菜单调整必须同步的内容

### 1. 原生菜单层

当新增或移动真实菜单时，先确认：

- `ir.ui.menu` 的父级正确。
- `ir.ui.menu.action` 存在。
- action 的 `res_model` 正确。
- 菜单 `groups_id` 覆盖目标用户。
- 目标用户对 action 模型有 read 权限。

验证示例：

```bash
docker compose exec -T odoo odoo shell -c /var/lib/odoo/odoo.conf -d sc_demo --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo <<'PY'
user = env['res.users'].sudo().search([('login','=','wutao')], limit=1)
xmlid = 'smart_construction_core.menu_sc_deduction_bill'
menu = env.ref(xmlid, raise_if_not_found=False)
print(menu.id, menu.complete_name, menu.action, getattr(menu.action, 'res_model', ''))
print('group_overlap', bool(set(menu.groups_id.ids) & set(user.groups_id.ids)) if menu.groups_id else 'no groups')
model = getattr(menu.action, 'res_model', '')
print('read_access', env(user=user)[model].check_access_rights('read', raise_exception=False) if model in env else 'model missing')
PY
```

### 2. 产品策略层

自定义前端的发布菜单主要由 `sc.product.policy.menu_groups` 决定。

关键字段：

- `label`: 前端显示名。
- `visible_menu_path`: 前端菜单路径，使用 `空格/空格` 分隔层级，例如 `智慧施工管理平台 / 财务中心 / 非现金业务管理 / 扣款登记`。
- `product_domain` / `product_domain_label`: 业务域。
- `entry_intent`: 办理、查询、分析、配置等。
- `disposition_policy`:
  - `keep_list_form`: 保持独立列表/表单入口。
  - `merge_by_category`: 多个业务类型合并为一个入口，通过业务类型区分新建/筛选。
- `integration_target`: 合并入口的模型和显示名，例如 `sc.expense.claim 费用/保证金申请`。
- `default_business_category_code`: 默认业务类型。
- `allowed_business_category_codes`: 入口允许办理的业务类型。

注意：

- 只改 `ir.ui.menu` 名称或父级，不一定会改变自定义前端。
- 只改 `visible_menu_path`，如果 `integration_target` 仍是旧名，合并入口仍会显示旧名。
- 菜单名里含 `/` 时，路径必须用 `空格/空格` 分隔，不能用裸 `/`。

### 3. 同步逻辑层

当前施工产品策略由：

- `addons/smart_construction_core/models/support/product_policy_sync.py`

同步入口：

- `_sync_user_confirmed_locked_construction_product_policies`
- `_apply_finance_cash_noncash_product_menu_overrides`

费用/扣款/保证金当前约定：

- 非现金业务管理
  - `扣款登记`
  - 业务类型：`finance.deduction.bill`
  - `disposition_policy = keep_list_form`
- 费用/保证金现金办理
  - `费用/保证金申请`
  - 业务类型：`finance.expense.reimbursement`, `finance.expense.project`, `finance.deposit.*`
  - `disposition_policy = merge_by_category`
  - `integration_target = sc.expense.claim 费用/保证金申请`
  - `扣款实缴登记`
  - 业务类型：`finance.deduction.paid`
  - `扣款实缴退回`
  - 业务类型：`finance.deduction.refund`

业务概念边界：

- `扣款登记` 是非现金业务事实登记：公司先扣税费、管理费等，再列支到项目或承包人责任。
- `扣款实缴登记`、`扣款实缴退回` 是现金流办理。
- 费用报销、项目费用、保证金支付/退回是现金相关办理。

## 每次调整后的执行步骤

### 1. 语法检查

```bash
python3 -m py_compile addons/smart_core/delivery/menu_service.py addons/smart_core/handlers/system_init.py addons/smart_construction_core/models/support/product_policy_sync.py scripts/verify/system_init_menu_boundary_guard.py
python3 scripts/verify/system_init_menu_boundary_guard.py
```

### 2. 升级模块，重建产品策略

```bash
docker compose exec -T odoo odoo -c /var/lib/odoo/odoo.conf -d sc_demo -u smart_construction_core --stop-after-init --no-http --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo
```

### 3. 重启 Odoo，加载 Python 代码

```bash
docker compose restart odoo
```

### 4. 等服务就绪

```bash
for i in $(seq 1 30); do
  if curl -fsS http://localhost:8070/web/login >/dev/null; then
    echo ready
    exit 0
  fi
  sleep 2
done
echo not-ready
exit 1
```

## 必须验证的三层结果

### 1. 验证产品策略

```bash
docker compose exec -T odoo odoo shell -c /var/lib/odoo/odoo.conf -d sc_demo --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo <<'PY'
import json
policy = env['sc.product.policy'].sudo().search([('product_key','=','construction.standard')], limit=1)
old = []
for group in policy.menu_groups or []:
    if group.get('group_label') != '财务中心':
        continue
    for menu in group.get('menus') or []:
        if not isinstance(menu, dict):
            continue
        target = str(menu.get('integration_target') or '')
        if '费用/扣款/保证金办理' in target:
            old.append(menu)
        if any(token in json.dumps(menu, ensure_ascii=False) for token in ('扣款', '费用/保证金', 'finance.deduction')):
            print(json.dumps({
                k: menu.get(k)
                for k in [
                    'label',
                    'menu_xmlid',
                    'visible_menu_path',
                    'default_business_category_code',
                    'integration_target',
                    'product_domain_label',
                    'allowed_business_category_codes',
                    'disposition_policy',
                ]
            }, ensure_ascii=False))
print('OLD_TARGET_COUNT', len(old))
PY
```

预期：

- `OLD_TARGET_COUNT 0`
- `扣款登记` 只允许 `finance.deduction.bill`
- `扣款实缴登记` 只允许 `finance.deduction.paid`
- `扣款实缴退回` 只允许 `finance.deduction.refund`
- 费用/保证金现金入口的 `integration_target` 是 `sc.expense.claim 费用/保证金申请`

### 2. 验证 DeliveryEngine

这一步验证后端发布菜单构建逻辑，但还不是浏览器最终响应。

```bash
docker compose exec -T odoo odoo shell -c /var/lib/odoo/odoo.conf -d sc_demo --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo <<'PY'
from odoo.addons.smart_core.delivery.delivery_engine import DeliveryEngine

user = env['res.users'].sudo().search([('login','=','wutao')], limit=1)
uenv = env(user=user)
native = uenv['app.menu.config'].get_menu_contract(model_name=None, filter_runtime=True, scene='web', filters={
    'leaf_only': False,
    'hide_without_action': False,
    'only_act_window': False,
    'hide_unreadable_model': False,
    'model_whitelist': [],
    'max_depth': 0,
    'prune_single_chain': False,
}).get('nav') or []
payload = DeliveryEngine(uenv).build(data={'role_surface': {}}, product_key='', edition_key='standard', base_product_key='', native_nav=native)

def label(node):
    return node.get('label') or node.get('title') or node.get('name') or ''

def find(nodes, path):
    for node in nodes or []:
        if label(node) == path[0]:
            return node if len(path) == 1 else find(node.get('children') or [], path[1:])
    return None

for path in [
    ['系统菜单','财务中心','非现金业务管理','扣款登记'],
    ['系统菜单','财务中心','费用/保证金现金办理','费用/保证金申请'],
    ['系统菜单','财务中心','费用/保证金现金办理','扣款实缴登记'],
    ['系统菜单','财务中心','费用/保证金现金办理','扣款实缴退回'],
]:
    node = find(payload.get('nav') or [], path)
    print('PATH', ' / '.join(path), bool(node), (node or {}).get('menu_id'), ((node or {}).get('meta') or {}).get('allowed_business_category_codes'))
print('OLD_TOP_LEVEL_EXISTS', bool(find(payload.get('nav') or [], ['系统菜单','财务中心','费用/扣款/保证金办理'])))
PY
```

### 3. 验证真实 HTTP `system.init`

这是浏览器实际消费的最终契约，必须以它为准。

```bash
TOKEN=$(docker compose exec -T odoo odoo shell -c /var/lib/odoo/odoo.conf -d sc_demo --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo <<'PY' | awk '/^eyJ/{print}' | tail -n 1
import os, time, uuid, jwt
from odoo.addons.smart_core.security.auth import DEFAULT_SECRET_KEY, ALGORITHM
secret = os.getenv('SC_JWT_SECRET') or os.getenv('JWT_SECRET') or env['ir.config_parameter'].sudo().get_param('sc.jwt.secret') or DEFAULT_SECRET_KEY
user = env['res.users'].sudo().search([('login','=','wutao')], limit=1)
now = int(time.time())
payload = {
    'user_id': user.id,
    'iat': now,
    'exp': now + 8 * 60 * 60,
    'jti': uuid.uuid4().hex,
    'token_version': int(getattr(user, 'token_version', 0) or 0),
    'db': 'sc_demo',
}
print(jwt.encode(payload, secret, algorithm=ALGORITHM))
PY
)

curl -sS -X POST 'http://localhost:18081/api/v1/intent?db=sc_demo' \
  -H 'Content-Type: application/json' \
  -H 'X-Odoo-DB: sc_demo' \
  -H "Authorization: Bearer $TOKEN" \
  --data '{"intent":"system.init","params":{"scene":"web","with_preload":false,"scene_ready_mode":"registry","with":["workspace_home"],"root_xmlid":"smart_construction_core.menu_sc_root"}}' \
  > /tmp/wutao-system-init.json

python3 - <<'PY'
import json
body = (json.load(open('/tmp/wutao-system-init.json')).get('data') or {})
nav = ((body.get('release_navigation_v1') or {}).get('nav') or body.get('nav') or [])

def label(node):
    return node.get('label') or node.get('title') or node.get('name') or ''

def find(nodes, path):
    for node in nodes or []:
        if label(node) == path[0]:
            return node if len(path) == 1 else find(node.get('children') or [], path[1:])
    return None

def labels(node):
    return [label(child) for child in (node or {}).get('children') or []]

for path in [
    ['系统菜单','财务中心','非现金业务管理','扣款登记'],
    ['系统菜单','财务中心','费用/保证金现金办理','费用/保证金申请'],
    ['系统菜单','财务中心','费用/保证金现金办理','扣款实缴登记'],
    ['系统菜单','财务中心','费用/保证金现金办理','扣款实缴退回'],
]:
    node = find(nav, path)
    print('PATH', ' / '.join(path), bool(node), (node or {}).get('menu_id'), ((node or {}).get('meta') or {}).get('allowed_business_category_codes'))

print('OLD_TOP_LEVEL_EXISTS', bool(find(nav, ['系统菜单','财务中心','费用/扣款/保证金办理'])))
print('finance children', labels(find(nav, ['系统菜单','财务中心'])))
print('cash children', labels(find(nav, ['系统菜单','财务中心','费用/保证金现金办理'])))
print('noncash children', labels(find(nav, ['系统菜单','财务中心','非现金业务管理'])))
PY
```

预期：

- `OLD_TOP_LEVEL_EXISTS False`
- `cash children ['费用/保证金申请', '扣款实缴登记', '扣款实缴退回']`
- `noncash children ['扣款登记']`

## 前端刷新规则

前端不会从 `localStorage` 恢复菜单树，但当前页面如果已经处于 `initStatus=ready`，不会自动重新跑 `system.init`。

调整菜单后，验证时必须：

- 重新登录，或
- 浏览器强制刷新页面，或
- 清理当前 session 后重新进入。

如果只在已经打开的页面里观察，看到旧菜单不代表后端未生效。

## 常见问题

### 只改 Odoo 原生菜单，为什么自定义前端没变？

因为自定义前端优先消费产品发布导航。原生菜单主要用于授权和动作事实，不是最终显示结构。

### 新菜单出现了，但旧菜单还在，为什么？

通常是 `sc.product.policy.menu_groups` 里仍有旧 `integration_target` 或旧 `visible_menu_path`。合并入口的显示名来自 `integration_target`，不是只来自原生菜单名。

### 路径里有 `/` 怎么办？

`visible_menu_path` 的层级分隔必须写成 `空格/空格`。

正确：

```text
智慧施工管理平台 / 财务中心 / 费用/保证金现金办理 / 扣款实缴登记
```

错误：

```text
智慧施工管理平台/财务中心/费用/保证金现金办理/扣款实缴登记
```

错误写法会把 `费用/保证金现金办理` 拆成 `费用` 和 `保证金现金办理` 两级。
