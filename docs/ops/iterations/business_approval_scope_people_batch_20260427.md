# Batch-Business-Approval-Scope-People

## 1. 本轮变更
- 目标：允许业务配置管理员受控维护审批岗位人员，并暂时允许新增内部用户。
- 完成：
  - 新增 `sc.approval.scope` 审批岗位人员模型，固定维护 7 个审批岗位。
  - 新增 `sc.approval.scope.user.wizard` 新增审批人员向导。
  - 新增业务配置菜单 `审批岗位人员`。
  - 授权业务配置管理员读取用户、维护审批岗位人员、通过向导新增内部用户。
  - 写入仍限定到底层白名单审批岗位执行组，不开放原生用户/权限组配置页面。
- 未完成：后续可增加平台级参数，控制是否允许业务配置管理员新增人员。

## 2. 影响范围
- 模块：`addons/smart_construction_core`
- 启动链：否
- contract：否
- 路由：否

## 3. 风险
- P0：无。
- P1：当前“新增人员”默认创建内部用户并初始化密码 `123456`，后续需接入平台参数控制和密码策略提示。
- P2：业务配置管理员可读取用户列表，但不能写原生用户和原生权限组。

## 4. 验证
- `python3 -m py_compile addons/smart_construction_core/models/support/approval_scope.py`
- `python3 xml.etree.ElementTree parse for approval_scope_seed.xml, approval_scope_views.xml`
- `git diff --check`
- `make mod.upgrade MODULE=smart_construction_core`
- `make odoo.shell.exec` 回滚验证 `wutao` 可读取 7 个岗位、可调整岗位人员、可新增临时内部用户并加入财务审核人岗位。
- `make verify.business.oca_runtime_smoke`
- 结果：PASS。

## 5. 产物
- snapshot：N/A
- logs：命令输出已记录在本轮 Codex 会话。
- e2e：N/A

## 6. 回滚
- commit：回退本批提交。
- 方法：回退代码后执行 `make mod.upgrade MODULE=smart_construction_core`，移除审批岗位人员业务入口。

## 7. 下一批次
- 目标：继续真实用户业务办理矩阵与连续办理缺口判断。
- 前置条件：模拟生产库已完成模块升级和服务重启。
