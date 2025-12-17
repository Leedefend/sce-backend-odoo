# 权限映射矩阵（Capability → API）

**版本**：v1.0  
**目标**：把 capability groups 的语义精确映射到 API 操作能力，避免“菜单=权限”的错觉。

---

## 1) 约定

- read：允许 `GET/LIST`（默认），不授予 UI 菜单入口
- user：允许业务写入（create/update/submit 等）
- manager：允许审批/关键动作（approve/reject 等）+ user 的全部能力

---

## 2) 样例矩阵（财务中心：付款申请）

| Operation | API | 最小能力组 | 说明 |
|---|---|---|---|
| payment_request.list | GET /payment_requests | finance_read | 列表读取 |
| payment_request.get | GET /payment_requests/{id} | finance_read | 详情读取 |
| payment_request.create | POST /payment_requests | finance_user | 创建 |
| payment_request.update | PATCH /payment_requests/{id} | finance_user | 草稿编辑（受状态机限制） |
| payment_request.submit | POST /payment_requests/{id}/actions/submit | finance_user | 提交审批 |
| payment_request.approve | POST /payment_requests/{id}/actions/approve | finance_manager | 审批通过 |
| payment_request.reject | POST /payment_requests/{id}/actions/reject | finance_manager | 审批驳回 |
| payment_request.cancel | POST /payment_requests/{id}/actions/cancel | finance_user/manager | 取消（规则约束） |

---

## 3) 五中心统一映射规则（模板）

对每个中心（project/cost/contract/material/finance）都按下面模板列矩阵：

- 读：`*_read`
- 写：`*_user`
- 审批/关键动作：`*_manager`

> 注意：如果某能力需要跨域读取（例如财务关联合同），应通过 **ACL/记录规则** 放行读取能力，而不是开放合同中心菜单入口。
