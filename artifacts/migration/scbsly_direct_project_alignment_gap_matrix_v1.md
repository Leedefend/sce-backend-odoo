# SCBSLY Direct Project Alignment Gap Matrix v1

Status: `PASS`
Source: `artifacts/migration/scbsly_direct_project_new_system_alignment_probe_v1.json`

| Bucket | Count | Labels |
| --- | ---: | --- |
| pass | 34 | 施工合同、分包合同、租赁合同、供货合同、劳务合同、机械合同（合同）、材料计划、报价单、入库、材料结算单、库存统计表（新）、方单、零星用工、劳务结算、分包方单、分包结算单、机械台班记录、机械结算单、租入、还租、租赁结算单、项目费用报销单、管理人员工资表、油卡登记、充值登记、加油登记、支付申请、工程进度收款、往来单位付款、工程结算单、进项上报、总包进项上报、成本统计表（数据）、施工日志（新） |
| data_scope_count_mismatch | 0 |  |
| missing_user_visible_menu_route | 0 |  |
| missing_server_carrier | 0 |  |
| missing_or_unmapped_menu | 0 |  |
| field_surface_gap | 0 |  |
| other_alignment_gap | 0 |  |

## Rows

| 分类 | 菜单 | Bucket | 匹配菜单 | menu | action | model | 旧数 | 新数 | 字段 |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| 合同类单据 | 施工合同 | pass | 施工合同 | 681 | 910 | sc.legacy.direct.acceptance.fact | 182 | 182 | 12 |
| 合同类单据 | 分包合同 | pass | 分包合同 | 682 | 911 | sc.legacy.direct.acceptance.fact | 86 | 86 | 12 |
| 合同类单据 | 租赁合同 | pass | 租赁合同 | 683 | 912 | sc.legacy.direct.acceptance.fact | 221 | 221 | 12 |
| 合同类单据 | 供货合同 | pass | 供货合同 | 684 | 913 | sc.legacy.direct.acceptance.fact | 848 | 848 | 12 |
| 合同类单据 | 劳务合同 | pass | 劳务合同 | 685 | 914 | sc.legacy.direct.acceptance.fact | 187 | 187 | 12 |
| 合同类单据 | 机械合同（合同） | pass | 机械合同（合同） | 686 | 915 | sc.legacy.direct.acceptance.fact | 221 | 221 | 12 |
| 材料管理类单据 | 材料计划 | pass | 材料计划 | 687 | 916 | sc.legacy.direct.acceptance.fact | 686 | 686 | 12 |
| 材料管理类单据 | 报价单 | pass | 报价单 | 688 | 917 | sc.legacy.direct.acceptance.fact | 126 | 126 | 12 |
| 材料管理类单据 | 入库 | pass | 入库 | 689 | 918 | sc.legacy.direct.acceptance.fact | 13171 | 13171 | 12 |
| 材料管理类单据 | 材料结算单 | pass | 材料结算单 | 690 | 919 | sc.legacy.direct.acceptance.fact | 1214 | 1214 | 12 |
| 材料管理类单据 | 库存统计表（新） | pass | 库存统计表（新） | 691 | 791 | sc.material.stock.summary |  | 0 | 24 |
| 劳务管理类单据 | 方单 | pass | 方单 | 692 | 920 | sc.legacy.direct.acceptance.fact | 252 | 252 | 12 |
| 劳务管理类单据 | 零星用工 | pass | 零星用工 | 693 | 921 | sc.legacy.direct.acceptance.fact | 8769 | 8769 | 12 |
| 劳务管理类单据 | 劳务结算 | pass | 劳务结算 | 694 | 922 | sc.legacy.direct.acceptance.fact | 576 | 576 | 12 |
| 分包管理类单据 | 分包方单 | pass | 分包方单 | 695 | 923 | sc.legacy.direct.acceptance.fact | 721 | 721 | 12 |
| 分包管理类单据 | 分包结算单 | pass | 分包结算单 | 696 | 924 | sc.legacy.direct.acceptance.fact | 88 | 88 | 12 |
| 机械与租赁管理类单据 | 机械台班记录 | pass | 机械台班记录 | 697 | 925 | sc.legacy.direct.acceptance.fact | 17495 | 17495 | 12 |
| 机械与租赁管理类单据 | 机械结算单 | pass | 机械结算单 | 698 | 926 | sc.legacy.direct.acceptance.fact | 669 | 669 | 12 |
| 机械与租赁管理类单据 | 租入 | pass | 租入 | 699 | 907 | sc.material.rental.order | 0 | 0 | 44 |
| 机械与租赁管理类单据 | 还租 | pass | 还租 | 700 | 908 | sc.material.rental.order | 37 | 37 | 44 |
| 机械与租赁管理类单据 | 租赁结算单 | pass | 租赁结算单 | 701 | 927 | sc.legacy.direct.acceptance.fact | 669 | 669 | 12 |
| 费用与资金管理类单据 | 项目费用报销单 | pass | 项目费用报销单 | 702 | 928 | sc.legacy.direct.acceptance.fact | 5802 | 5802 | 12 |
| 费用与资金管理类单据 | 管理人员工资表 | pass | 管理人员工资表 | 703 | 929 | sc.legacy.direct.acceptance.fact | 233 | 233 | 12 |
| 费用与资金管理类单据 | 油卡登记 | pass | 油卡登记 | 704 | 904 | sc.legacy.fuel.card.fact | 8 | 8 | 11 |
| 费用与资金管理类单据 | 充值登记 | pass | 充值登记 | 705 | 905 | sc.legacy.fuel.card.recharge.fact | 32 | 32 | 12 |
| 费用与资金管理类单据 | 加油登记 | pass | 加油登记 | 706 | 906 | sc.legacy.fuel.card.refuel.fact | 500 | 500 | 14 |
| 费用与资金管理类单据 | 支付申请 | pass | 支付申请 | 707 | 930 | sc.legacy.direct.acceptance.fact | 2595 | 2595 | 12 |
| 费用与资金管理类单据 | 工程进度收款 | pass | 工程进度收款 | 708 | 909 | sc.legacy.engineering.progress.receipt | 639 | 639 | 15 |
| 费用与资金管理类单据 | 往来单位付款 | pass | 往来单位付款 | 709 | 931 | sc.legacy.direct.acceptance.fact | 10342 | 10342 | 12 |
| 费用与资金管理类单据 | 工程结算单 | pass | 工程结算单 | 710 | 932 | sc.legacy.direct.acceptance.fact | 37 | 37 | 12 |
| 费用与资金管理类单据 | 进项上报 | pass | 进项税额上报 | 711 | 933 | sc.legacy.direct.acceptance.fact | 6389 | 6389 | 12 |
| 费用与资金管理类单据 | 总包进项上报 | pass | 总包进项上报 | 712 | 934 | sc.legacy.direct.acceptance.fact | 383 | 383 | 12 |
| 费用与资金管理类单据 | 成本统计表（数据） | pass | 成本统计表（数据） | 713 | 792 | sc.comprehensive.cost.summary |  | 818 | 24 |
| 项目管理类单据 | 施工日志（新） | pass | 施工日志（新） | 714 | 935 | sc.legacy.direct.acceptance.fact | 3233 | 3233 | 12 |
