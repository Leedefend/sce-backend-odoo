# Smart Construction Demo 数据闭环

本 demo 覆盖项目→合同→物资计划→采购单→付款申请的最小闭环。

## 安装/升级

```
make upgrade MODULE=smart_construction_demo
```

## 自动生成

- Demo 项目、支出合同、付款申请
- Demo 物资计划：自动补 2 行（钢筋/混凝土），状态已批准
- Demo 采购单：按供应商自动生成 2 张 PO（各含一行），带计划关联

## 手动演示

1. 打开物资计划 `sc_demo_material_plan_001` 查看明细及状态
2. 打开采购单列表，按 `物资计划` 过滤可见 2 张 PO
3. 付款申请 `sc_demo_payment_request_001` 可用于演示额度/审批流程
