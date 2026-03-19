## 🔥 本次变更摘要 (Summary)

<!-- 用一句话说明本次 PR 做了什么 -->

## ✨ 详细变更内容 (Details)

- [ ] 新增模型 / 字段：
- [ ] 新增视图 / 动作：
- [ ] 新增业务流程 / 服务器动作：
- [ ] 代码重构 / 优化：
- [ ] 文档更新：

## 📦 交付冲刺状态（可选粘贴）

> 用于交付冲刺 PR 的快速状态同步，可按需保留/删减。

- `N+2` 兼容退场：`live_no_allowed_actions` 已移除，统一使用 `live_no_executable_actions`
- 审批聚合链：`verify.portal.payment_request_approval_all_smoke.container` 通过
- 字段消费巡检：`verify.portal.payment_request_approval_field_consumer_audit` 通过（`unexpected_deprecated_refs=0`）
- 执行模式：`PAYMENT_APPROVAL_NEED_UPGRADE=0`（重启生效，不强制升级）

## 🧪 测试步骤 (How to Test)

1. 升级模块：
   ```bash
   make upgrade MODULE=smart_construction_core
2.进入 Odoo 测试：

打开菜单：xxxxx

执行：xxxxx

预期结果：xxxxx

📌 关联 Issue

关闭以下 Issue：

Closes #ISSUE_ID

✔️ 合并前检查清单 (Checklist)

 代码可读性良好

 无无用代码 / 注释

 [ ] 若触及基线冻结区，已在 PR 描述说明例外原因并附回滚方案

 [ ] 若为业务增量迭代，已附 preflight 证据（`verify.business.increment.preflight`）
 [ ] 若使用业务增量 profile，已在 PR 描述注明（`BUSINESS_INCREMENT_PROFILE=...`）
 [ ] 若触及侧边栏/场景路由，已附菜单场景覆盖证据：
      - `make verify.menu.scene_resolve.container DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo`
      - `make verify.menu.scene_resolve.summary`
      - 证据中需包含：
        - `menu_scene_resolve_effective_total`
        - `menu_scene_resolve_coverage`
        - `menu_scene_resolve_enforce_prefixes`

 权限（ir.model.access）设置正确

 XML 通过 Odoo 解析

 manifest 更新正确

 已测试主要流程


---

# 🟩 **第二部分：Issue 模板（Issue Templates）**

GitHub 支持多个 Issue 模板，我们创建三个：

目录：



.github/ISSUE_TEMPLATE/
feature_request.md
bug_report.md
task.md


---

## 1）Feature Request（功能需求）

`feature_request.md`

```markdown
---
name: "💡 功能需求 / Feature Request"
about: 描述你想实现的新功能
labels: enhancement
---

## ✨ 功能背景
<!-- 为什么需要这个功能？当前有什么问题？ -->

## 🎯 目标行为
<!-- 功能要解决什么问题？最终效果是什么？ -->

## 📐 功能范围
- [ ] 模型改动
- [ ] 视图改动
- [ ] 新业务流程
- [ ] 接口 / RPC
- [ ] AI 自动化集成

## 🧩 验收标准 (Acceptance Criteria)
1. xxxx
2. xxxx
3. xxxx
