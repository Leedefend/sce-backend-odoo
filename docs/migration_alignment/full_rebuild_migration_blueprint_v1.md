# 完整新库重建迁移蓝图 v1

任务：`ITER-2026-04-13-1850`

## 目标

在完整新库中可重复重建旧系统业务数据。

这不是一次性脚本导入，而是一条可重复流水线：

```text
source probe
→ normalized staging artifact
→ dry-run
→ small trial write
→ post-write review
→ rollback dry-run
→ bounded expand
→ production rebuild step
```

## 推荐重建顺序

1. 平台基础与字典基线
2. partner 主源：`T_Base_CooperatCompany`
3. partner 补充：`T_Base_SupplierInfo`
4. 项目骨架：`BASE_SYSTEM_PROJECT` + `T_System_XMGL`
5. 项目成员：`BASE_SYSTEM_PROJECT_USER`
6. 合同骨架：`T_ProjectContract_Out`
7. 合同相对方关联：强证据 + 人工确认映射
8. 回款/付款业务切片：基于合同和 partner readiness
9. 附件：`BASE_SYSTEM_FILE` / `T_BILL_FILE`
10. 菜单/功能：只作为旧系统行为参考，不直接导入

## 当前依赖判断

### Partner

主源使用 `T_Base_CooperatCompany`，因为：

- 与回款往来单位引用更强；
- 有统一社会信用代码和税号字段；
- 合同相对方证据主要落在 company。

`T_Base_SupplierInfo` 作为补充源，优先补银行账号、供应商分类和资质，不作为主 identity。

### Project

项目已有 130 条 create-only 骨架样本写入经验，但完整重建必须回到：

- `BASE_SYSTEM_PROJECT.ID`
- `OTHER_SYSTEM_ID`
- `OTHER_SYSTEM_CODE`
- 项目状态治理规则

并重新构建完整新库输入，不依赖当前演示库的偶然样本。

### Contract

合同写入必须等待：

- partner readiness；
- project readiness；
- 合同 legacy identity 已存在；
- 删除态和方向策略明确；
- 金额、税务、行项目暂缓或定义安全切片。

### Attachments

附件规模较大：

- `BASE_SYSTEM_FILE`: 126967
- `T_BILL_FILE`: 51964

附件必须在业务记录 identity 物化后再做，不能先导。

## 当前可执行下一步

继续围绕 369 个强证据 partner 候选推进：

1. no-DB rebuild importer 晋级；
2. 小样本 create-only 试写设计；
3. rollback dry-run 设计；
4. 写后只读复核。

真实导入仍需单独授权。

