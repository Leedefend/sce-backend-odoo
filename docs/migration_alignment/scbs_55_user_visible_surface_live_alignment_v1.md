# SCBS 55 用户可见面 Live 对齐基准 v1

## 来源

- 老系统：`https://www.builderp.cn/SCBS` 当前用户真实可见菜单。
- 整理分支：`chore/user-visible-surface-systematic-alignment`。
- 账号 Token 仅用于本地临时抓取，未写入仓库。
- 本文档只沉淀菜单、ConfigId、字段和表来源，不沉淀账号或密码。

## 抓取结果

- 总入口：`55`
- `captured`：`42`
- `custom_or_non_lowcode_link`：`3`
- `menu_without_link`：`2`
- `report_config_id_captured`：`8`

## 使用规则

1. 新系统任何用户可见面字段调整，先在本矩阵中确认老系统真实字段、主表、从表和 ConfigId。
2. 低代码列表字段以 `visible_columns` 为第一口径；隐藏列只作来源线索，不直接作为用户可见列。
3. 从表展开字段保留 `$表名` 后缀，例如 `JSLX$C_JXXP_YJSKDJ_CB`，迁移和投影必须回到对应从表事实，不得用主表字段猜测回填。
4. `custom_or_non_lowcode_link`、`report_config_id_captured`、`menu_without_link` 需要单独补运行页或报表 schema 抓取。

## 入口矩阵

| # | 分组 | 入口 | 状态 | 老系统路径 | ConfigId | 主表 | 从表 | 可见列 |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 基础资料 | 供应商/合作单位 | `captured` | 项目/综合/供应商/合作单位 | `164a6642d18a4be6bcf08115f09714da` | `T_Base_CooperatCompany` | `` | 单据状态(DJZTText); 推送结果(TSJG); 项目名称(XMMC); 单位编号(DJBH); 合作类型(HZLX); 单位名称(DWMC); 开户银行(KHYH); 账号(KHZH); 统一社会信用代码(TYSHXYDM); 主税率(ZSLV); 录入人(LRR); 录入时间(LRSJ) |
| 2 | 基础资料 | 往来单位 | `captured` | 项目/综合/往来单位 | `6a04d6b9e23b4834aabc83efc34836ef` | `T_Base_CooperatCompany` | `` | 单据状态(DJZTText); 项目名称(XMMC); 单位名称(DWMC); 收款金额(SKJE); 付款金额(FKJE); 开户姓名(KHXM$T_Base_CooperatCompany_Account); 开户账号(KHZH$T_Base_CooperatCompany_Account); 开户银行(KHYH$T_Base_CooperatCompany_Account); 录入人(LRR); 录入时间(LRSJ); 银行账号(D_SCBSJS_YHZH) |
| 3 | 合同 | 施工合同 | `captured` | 项目/综合/施工合同/施工合同 | `164b665cc3674384aeaa89f3122895cf` | `T_ProjectContract_Out` | `T_ProjectContract_Out_CB,T_ProjectContract_Out_CB_BZJ` | 单据状态(DJZTText); 单据编号(DJBH); 合同订立日期(f_HTDLRQ); 原件是否归档(D_SCBSJS_SFGD); 发包人(FBF); 项目名称(f_XMMC); 合同标题(HTBT); 工程类别(HTLX); 合同编号(HTBH); 合同金额(GCYSZJ); 结算金额(D_SCBSJS_JSJE); 累计开票(LJKP); 累计收款(LJSK); 未收款(WSK); 未收款比例(WSKBL); 挂靠人(GKR); 工程地址(f_GCDZ); 工程内容(f_GCNR); 录入人(LRR... |
| 4 | 办公资料 | 公司资料存档 | `captured` | 项目/施工/施工资料/公司资料存档 | `bc29a73e0fb04ec0b28820a48b71f928` | `SGZL_RZRJ` | `SGZL_RZRJ_CB` | 单据状态(DJZTText); 项目名称(f_GCMC); 资料类型(ZLMC$SGZL_RZRJ_CB); 资料说明(ZLSM$SGZL_RZRJ_CB); 录入人(LRR); 备注(BZ); 录入时间(LRSJ) |
| 5 | 人事行政 | 请假/休假审批单 | `captured` | 办公/行政/行政单/请假/休假审批单 | `64cf93d039844656a51a1ae97efc985f` | `BGGL_HBZJ_XZD_QJXJSPB` | `` | 单据状态(DJZTText); 单据编号(DJBH); 项目名称(XMMC); 申请人姓名(SQRXM); 所在部门(SZBM); 请假天数(QJTS); 请假类型(QJLX); 请假时间(QJSJ); 销假时间(XJSJ); 备注(BZ); 请假时长(QJSC); 录入人(LRR); 录入时间(LRSJ) |
| 6 | 人事行政 | 印章使用审批表 | `captured` | 办公/行政/行政单/印章使用审批表 | `6125bb6b25014e8fa4ad8592b335823c` | `BGGL_XZD_YZSYSPB` | `` | 单据状态(DJZTText); 单据编号(DJBH); 用印时间(YYSJ); 用印部门(YYBM); 用印申请人(YYSQR); 用印部门负责人签字(YYBMFZRQZ); 用印种类(YYZL); 用印文本名称及文号(YYWBMCJWH); 经办人签字(JBRQZ); 领导签字(LDQZ); 份数(FS); 备注(BZ); 归还时间(GHSJ); 合同金额(HTJE); 合同编号(HTBH); 所属公司(SSGS); 使用印章公司(D_JCLY_SYYZGS); 是否外带(D_JCLY_SFWD); 附件(... |
| 7 | 组织人员 | 组织机构 | `custom_or_non_lowcode_link` | 办公/人事/组织/组织机构 | `` | `` | `` |  |
| 8 | 组织人员 | 公司人员名册（配置） | `captured` | 办公/人事/人事/公司人员名册（配置） | `7c0f74c092344e31ad517c7f1e445267` | `BASE_SYSTEM_USER` | `` | 操作(PERSON_NAME); 姓名(PERSON_NAME); 用户名(USERNAME); 部门(BM); 职务(ZW); 岗位(GW); 电话号码(PHONE_NUMBER); 性别(SEX); 账号类型(ZHLX); 是否测试账号(SFCSZH); 证件类型(ZJLX); 证件号(ZJH); 居住地址(JZDZ); 是否购买社保(SFGMSB); 是否购买社保(ORDER_NUM); 员工工号(YGGH); 出生日期(CSRQ); 政治面貌(ZZMM); 民族(MZ); 籍贯(JG); 毕业院校(B... |
| 9 | 人事行政 | 社保人员登记 | `captured` | 办公/人事/社保/社保人员登记 | `1500c6c0d29a4ee3a3fa9b7cd72010f2` | `D_SCBSJS_BGGL_XZ_SBRY` | `` | 单据编号(DJBH); 单据日期(DJRQ); 姓名(XM); 人员类型(RYLX); 身份证号码(SFZHM); 联系方式(LXFS); 证书费用(ZSFY); 个人证书(GRZS); 社保基数(SBJS); 社保购买单位(ZS); 人员状态(RYZT); 备注(BZ); 录入人(LRR); 录入时间(LRSJ) |
| 10 | 人事行政 | 社保登记 | `captured` | 办公/人事/社保/社保登记 | `85fbd6ab11b14dcf8df3606e0fda15d2` | `BGGL_XZ_JXDJ_ZB` | `BGGL_XZ_JXDJ` | 单据状态(DJZTText); 单据编号(DJBH); 社保购买单位(SSGS$BGGL_XZ_JXDJ); 姓名(RY$BGGL_XZ_JXDJ); 类型(D_SCBSJS_RYLX$BGGL_XZ_JXDJ); 购买人数(D_SCBSJS_GMRS); 年度(ND); 月份(YF); 缴费金额(JXGZ$BGGL_XZ_JXDJ); 联系方式(D_SCBSJS_LXFS$BGGL_XZ_JXDJ); 备注(JL$BGGL_XZ_JXDJ); 登记人(LRR); 登记时间(LRSJ) |
| 11 | 人事行政 | 工资登记 | `captured` | 办公/人事/薪资/工资登记 | `e71b618040b342c7942cc663e5f0913f` | `BGGL_XZ_GZ` | `BGGL_XZ_GZ_CB` | 单据状态(DJZTText); 单据编号(DJBH); 标题(BT); 年份(NF); 月份(YF); 部门(BM$BGGL_XZ_GZ_CB); 姓名(XM$BGGL_XZ_GZ_CB); 发放单位(D_SCBSJS_FFDW$BGGL_XZ_GZ_CB); 应发工资(HJ$BGGL_XZ_GZ_CB); 实发工资(SFGZ$BGGL_XZ_GZ_CB); 备注(BZ$BGGL_XZ_GZ_CB); 发放人数(FFRS); 附件(f_FJ); 财务支出登记状态(SFDJ); 录入人(LRR); 录入时间(L... |
| 12 | 人事行政 | 补助 | `captured` | 办公/人事/薪资/补助 | `754087d59eb64349b61dd58620789300` | `BGGL_XZ_BZ` | `BGGL_XZ_BZ_CB` | 状态(DJZTText); 项目名称(XMMC); 单据编号(DJBH); 补助事由(D_SCBSJS_BZSX$BGGL_XZ_BZ_CB); 年度(ND$BGGL_XZ_BZ_CB); 月份(YF$BGGL_XZ_BZ_CB); 补助人(BZR$BGGL_XZ_BZ_CB); 部门(BMGW$BGGL_XZ_BZ_CB); 补助金额(BZJE$BGGL_XZ_BZ_CB); 录入人(LRR); 录入时间(LRSJ) |
| 13 | 人事行政 | 奖金 | `captured` | 办公/人事/薪资/奖金 | `f6500cf34fc3462abd8218a48b592733` | `BGGL_XZ_JJ` | `BGGL_XZ_JJ_CB` | 年度(ND); 月份(YF); 部门岗位(BMGW); 奖金金额(JE); 奖金事由(SY); 附件(f_FJ); 录入人(LRR); 录入时间(LRSJ) |
| 14 | 证照资料 | 证照登记 | `custom_or_non_lowcode_link` | 办公/人事/证照/证照登记 | `` | `` | `` |  |
| 15 | 证照资料 | 借阅申请 | `captured` | 办公/人事/证照/借阅申请 | `9858b51a528249d4b4672397fdd31e7b` | `ZJGL_ZSJYGL` | `ZJGL_ZSJYGL_CB` | 单据状态(DJZTText); 单据编号(DJBH); 借阅项目名称(JYXMMC); 证件名称(ZJMC); 申请日期(SQRQ); 借阅部门或项目部名称(JYBMMC); 借阅人(JYR); 联系方式(LXFS); 借阅形式(JYXS); 借阅日期(JYRQ); 负责人(FZRMC); 归还申请日期(GHSQRQ); 申请归还时间(SQGHSJ); 是否归还(SFGH); 确认归还时间(QRGHSJ); 归还日期(GHRQ); 附件(f_FJ); 录入人(LRR); 录入时间(LRSJ); 备注(BZ);... |
| 16 | 投标 | 投标报名管理 | `captured` | 办公/招投标/投标报名/投标报名管理 | `8dd24ed099044f49a4ae0a910600005c` | `P_ZTB_GCBMGL` | `` | 单据状态(DJZTText); 推送结果(TSJG); 单据编号(DJBH); 开标时间(KBSJ); 项目名称(f_GCMC); 登记时间(f_BMSJ); 录入人(f_LRR) |
| 17 | 投标 | 投标报名费申请 | `captured` | 办公/招投标/投标报名/投标报名费申请 | `26e3462907ac40e9ae51971776fb86a4` | `BGGL_ZTBJHT_TBBM_TBBMFSQ` | `` | 单据状态(DJZTText); 项目名称(XMMC); 单据编号(DJBH); 申请人(SQR); 申请日期(SQRQ); 收款账号(SKZH); 开户行(KHH); 金额(JE); 备注(BZ); 收款人(SKR); 付款方式(FKFS); 附件(f_FJ); 录入人(LRR); 录入时间(LRSJ) |
| 18 | 资金保证金 | 自筹保证金 | `captured` | 办公/保证金/自筹保证金/自筹保证金 | `74fcd2b29acb4101aee0da39851971f4` | `ZJGL_BZJGL_Branch_SBZJDJ` | `` | 状态(DJZTText); 单据编号(DJBH); 投标项目名称(TBXMMC); 项目名称(XMMC); 所属公司(SSGS); 金额(JE); 已退保证金金额(YTBZJJE); 转款单位(DW); 汇款方式(HKFS); 保证金类型(BZJLX); 收款账户(SKZH); 收款账户名称(SKZHMC); 备注(BZ); 附件(f_FJ); 录入人(LRR); 录入时间(LRSJ) |
| 19 | 资金保证金 | 自筹保证金退回 | `captured` | 办公/保证金/自筹保证金/自筹保证金退回 | `2aa899a761964e42a9bd63c9e5de7446` | `ZJGL_BZJGL_Branch_SBZJTH` | `ZJGL_BZJGL_Branch_SBZJTH_CB` | 状态(DJZTText); 收保证金单号(SBZJDH); 单据编号(DJBH); 项目名称(XMMC); 投标项目名称(TBXMMC); 退还金额(THJE); 备注(BZ); 退还账号(THKHHZH); 退还开户行(THKHH); 单位(DW); 收款开户行(SKKHH); 收款账号(SKZH); 录入人(LRR); 录入时间(LRSJ); 附件(f_FJ) |
| 20 | 资金保证金 | 付款还保证金 | `captured` | 办公/保证金/付保证金/付保证金 | `dffaa7ce90ca45d295d83fd66e407b07` | `ZJGL_BZJGL_Pay_FBZJ` | `` | 状态(DJZTText); 推送结果(TSJG); 金蝶单据编号(OTHER_SYSTEM_CODE); 单据编号(DJBH); 投标项目(TBXMMC); 工程项目(XMMC); 保证金类型(BZJLX); 所属公司(SSGS); 保证金金额(BZJJE); 已退金额(YTJE); 未退金额(WTJE); 是否需要退回(D_SCBSJS_SFXYTH); 收款单位(SKDW); 支付账户(ZFZH); 备注(BZ); 附件(f_FJ); 录入人(LRR); 录入时间(LRSJ) |
| 21 | 资金保证金 | 付款还保证金退回 | `captured` | 办公/保证金/付保证金/付保证金退回 | `0b947e8b721748fc8c7572ab48b2b629` | `ZJGL_BZJGL_Pay_FBZJTH` | `ZJGL_BZJGL_Pay_FBZJTH_CB` | 状态(DJZTText); 推送结果(TSJG); 退回单编号(DJBH); 所属公司(SSGS); 投标项目名称(TBXMMC); 保证金类型(Y_BZJLX); 退回项目(XMMC); 退回金额(THJE); 退回账户(ZHHM); 收款单位(Y_SKDW); 备注(Y_BZ); 录入人(LRR); 退回日期(THRQ); 附件(f_FJ) |
| 22 | 资金借还 | 借款申请 | `captured` | 办公/报销/借还款/借款申请 | `67b857cf441d403f9b38e2502a7c194c` | `BGGL_JHK_JKSQ` | `` | 单据状态(DJZTText); 项目名称(XMMC); 单据编号(DJBH); 申请部门(SQBM); 申请时间(SQSJ); 申请人(SQR); 是否预算内(SFYSN); 实际借款金额(JKJE); 主要资金使用安排(ZYZJSYAP); 收款人(SKR); 收款账户(SKZH); 开户银行(KHYH); 公司名称(GSMC); 备注(BZ); 付款单位(FKDW); 收款单位(SKDW); 往来单位名称(WLDWMC); 往来单位账户(WLDWZH); 借款账号(ZKZH); 实际批复金额(SJPFJE... |
| 23 | 资金借还 | 还款登记 | `captured` | 办公/报销/借还款/还款登记 | `1817964f26514480b38d72cfd07a4a93` | `BGGL_JHK_HKDJ` | `BGGL_JHK_HKDJ_CB` | 项目名称(XMMC); 单据状态(DJZTText); 单据编号(DJBH); 申请部门(SQBM); 申请时间(SQSJ); 申请人(SQR); 是否预算内(SFYSN); 借款金额(JKJE); 往来单位名称(WLDWMC); 附件(f_FJ); 录入人(LRR); 录入时间(LRSJ) |
| 24 | 费用报销 | 报销申请 | `captured` | 办公/报销/报销/报销申请 | `b05846f69bcb408a8f76db759b727964` | `CWGL_FYBX` | `CWGL_FYBX_CB` | 单据状态(DJZTText); 单据编号(DJBH); 所属公司(SSGS); 日期(RQ); 部门(BM); 报销人(XM); 报销类别(BXLB$CWGL_FYBX_CB); 事项说明(SXSM$CWGL_FYBX_CB); 报销金额(JE$CWGL_FYBX_CB); 收款人(SKR); 附件(f_FJ); 录入人(LRR); 录入时间(LRSJ) |
| 25 | 收支 | 收入 | `captured` | 办公/公司财务/财务收付款/收入 | `20cce886668d4327ab3bd0b5eeb3c6d0` | `C_CWSFK_GSCWSR` | `C_CWSFK_GSCWSR_CB` | 单据状态(DJZTText); 项目名称(XMMC); 单据编号(DJBH); 填写人(TXR); 收款账户(SKZH); 进账金额(JZJE); 收入类别(D_SCBSJS_CWSRLB); 收款时间(SKSJ); 备注(BZ); 附件(f_FJ); 录入人(LRR); 录入时间(LRSJ) |
| 26 | 收支 | 公司财务支出 | `captured` | 办公/公司财务/财务收付款/公司财务支出 | `5ee8feadd29942c397cd2ba9a4e564cf` | `C_CWSFK_GSCWZC` | `` | 单据状态(DJZTText); 推送结果(TSJG); 单据编号(DJBH); 付款时间(FKSJ); 付款金额(FKJE); 成本类别(D_SCBSJS_CWZCLB); 收款单位名称(SKDWMC); 付款账户名称(FKZHMC); 备注(BZ); 录入人(LRR); 录入时间(LRSJ); 附件(f_FJ) |
| 27 | 项目资金 | 承包人还项目款 | `captured` | 资金/自筹垫付/付息借款/承包人还项目款 | `04833d493d8c4b7e9abe576972e82c66` | `ZJGL_ZCDFSZ_FXJK_HK` | `` | 单据状态(DJZTText); 单据编号(DJBH); 项目名称(XMMC); 借款人(JKR); 借款金额(JKJE); 还款金额(HKJE); 用途(YT); 借款利率(JKLX); 利息(LX); 还款时间(HKSJ); 备注(BZ); 附件(f_FJ); 录入人(LRR); 录入时间(LRSJ) |
| 28 | 项目资金 | 承包人借项目款 | `captured` | 资金/自筹垫付/付息借款/承包人借项目款 | `95462a23156b45bc9beee2ee89078880` | `ZJGL_ZCDFSZ_FXJK_JK` | `` | 单据状态(DJZTText); 单据编号(DJBH); 项目名称(XMMC); 借款人(JKR); 借款金额(JKJE); 用途(YT); 约定期限(YDQX); 借款利息(JKLX); 备注(BZ); 附件(f_FJ); 录入人(LRR); 录入时间(LRSJ) |
| 29 | 付款 | 支付申请 | `captured` | 资金/资金收支/支付申请/支付申请 | `8797725d47ab49b2bc532ca3bfc0e410` | `C_ZFSQGL` | `C_ZFSQGL_CB` | 单据状态(DJZTText); 单据编号(DJBH); 项目名称(f_XMMC); 申请日期(f_SQRQ); 收款单位(f_GYSMC); 申请付款金额(f_JHJE); 实际付款金额(FKJE); 可用余额(SJKYYE); 成本分类名称(f_CBFLMC); 备注(f_Remark); 是否关联单据(SFGLDJ); 付款账号(FKZH); 金额大写(JEDX); 户名(HM); 开户行(f_KHH); 账号(f_ZH); 填写人(f_TXR); 附件(f_FJ); 录入时间(f_LRSJ) |
| 30 | 扣款 | 扣款单 | `captured` | 资金/资金收支/支付申请/扣款单 | `aa3a45e9fad54e85abdec43ebbaf5bd6` | `C_ZFSQGL_KKD` | `` | 单据状态(DJZTText); 单据编号(DJBH); 项目名称(XMMC); 扣款单位(KKDW); 扣款金额(KKJE); 扣款事由(KKSY); 单据日期(DJRQ); 附件(f_FJ); 录入人(LRR); 录入时间(LRSJ) |
| 31 | 付款 | 往来单位付款 | `captured` | 资金/资金收支/付款管理/往来单位付款 | `76a49bc01ef6469380e46555a9096139` | `T_FK_SUPPLIER` | `T_FK_Supplier_CB` | 单据状态(DJZTText); 推送结果(TSJG); 金蝶单据编号(OTHER_SYSTEM_CODE); 单据编号(DJBH); 項目名称(XMMC); 供应商名称(f_SupplierName); 付款日期(f_FKRQ); 付款金额(f_FKJE); 备注(f_BZ); 其他备注(Remark); 付款方式名称(f_FKFSMC); 填写人(f_TXR); 开户行(KHH); 账户(ZH); 付款账户(FKZH); 付款账户名称(FKZHMC); 支付申请单号(ZFSQDH); 附件(f_FJ) |
| 32 | 资金账户 | 账户间资金往来 | `captured` | 资金/资金收支/付款管理/账户间资金往来 | `ba6bf327bef542d5babc73047c3b6484` | `C_FKGL_ZHJZJWL` | `` | 单据状态(DJZTText); 项目名称(XMMC); 单据编号(DJBH); 发生时间(FSSJ); 账户号码(ZCZH); 收款账户(SKZH); 金额(JE); 转账类别(f_LB); 事由(SY); 备注(BZ); 附件(f_FJ); 录入人(LRR); 录入时间(LRSJ) |
| 33 | 扣款 | 扣款实缴登记 | `captured` | 资金/资金收支/付款管理/扣款实缴登记 | `f8030ead29934c2c986c5838a84acb3b` | `T_KK_SJDJB` | `T_KK_SJDJB_CB` | 单据状态(DJZTText); 单据编号(DJBH); 项目名称(XMMC); 单据日期(DJRQ); 标题(BTMC); 本次实缴数(BCSJS$T_KK_SJDJB_CB); 是否退回(SFTH$T_KK_SJDJB_CB); 上缴内容(SJNR$T_KK_SJDJB_CB); 本次计划已缴数(BCJHYJS$T_KK_SJDJB_CB); 录入人(LRR); 录入时间(LRSJ) |
| 34 | 扣款 | 扣款实缴退回 | `captured` | 资金/资金收支/付款管理/扣款实缴退回 | `77ed25cbfe1f44529241e05c849fcee2` | `T_KK_SJTHB` | `T_KK_SJTHB_CB` | 单据状态(DJZTText); 项目名称(XMMC); 单据编号(DJBH); 本次实缴数(BCSJS$T_KK_SJTHB_CB); 本次退回数(BCTHS$T_KK_SJTHB_CB); 上缴内容(NR$T_KK_SJTHB_CB); 备注(BZ); 附件(f_FJ); 录入人(LRR); 单据日期(DJRQ) |
| 35 | 收款 | 到款确认表 | `captured` | 资金/资金收支/收支确认表/到款确认表 | `c101aad0c08340e98b1cebb3dddead45` | `ZJGL_SZQR_DKQRB` | `` | 单据状态(DJZTText); 单据编号(DJBH); 时间(SJ); 项目名称(XMMC); 期数(QS); 本期收款(KPSKQK_BQS); 本期代扣代缴合计(BQDKDJHJ); 本期拨付金额合计(YFSGDGCK_2); 附件(f_FJ); 施工单位(SGD); 合同金额(HTJE); 目前形象进度(MQXXJD); 累计开票金额(LJKPJE); 上期留存余额(SQLCYE_SQLJS); 录入人(LRR); 录入时间(LRSJ) |
| 36 | 资金日报 | 资金日报表 | `captured` | 资金/资金收支/资金日报表 | `8c70515f098e4728aeb743b47418518d` | `D_SCBSJS_ZJGL_ZJSZ_ZJRBB` | `D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB` | 单据状态(DJZTText); 单据编号(DJBH); 单据日期(DJRQ); 账号名称(ZHMC$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB); 银行账号(YHZH$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB); 当前账户余额(DQZHYE$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB); 当前账户银行余额(DQZHYHYE$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB); 银行系统差额(YHXTCE$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB); 当... |
| 37 | 项目资金 | 项目借公司款登记 | `captured` | 资金/贷款管理/项目借公司款登记 | `d2253a78ecb14794b5b1851d82813c65` | `ZJGL_ZJSZ_DKGL_DKDJ` | `` | 单据状态(DJZTText); 单据编号(DJBH); 项目名称(XMMC); 贷款金额(DKJE); 到期利息(D_SCBSJS_DQLX); 还款金额(HKJE); 未还款金额(HKSYJE); 贷款日期(DKRQ); 还款日期(HKRQ); 贷款天数(DKSJ); 年利率(DKLL); 贷款账户(DKZH); 贷款银行(DKYH); 备注(BZ); 附件(f_FJ); 录入人(LRR); 录入时间(LRSJ) |
| 38 | 项目资金 | 项目还公司款登记 | `captured` | 资金/贷款管理/项目还公司款登记 | `fc3b2d537e794624853ee626f0c59ece` | `ZJGL_ZJSZ_DKGL_HKDJ` | `` | 单据状态(DJZTText); 单据编号(DJBH); 项目名称(XMMC); 还款金额(HKJE); 实际还款天数(D_SCBSJS_SJHKTS); 实际年利率(D_SCBSJS_SJNLL); 贷款利息(DKLX); 贷款银行(DKYH); 贷款账户(DKZH); 还款账户(HKZH); 填写人(TXR); 备注(BZ); 附件(f_FJ); 录入人(LRR); 录入时间(LRSJ) |
| 39 | 发票税务 | 开票申请 | `captured` | 税务/销项/开票申请 | `eba0e4922fa7445c9c9904fd4ab6da61` | `C_JXXP_KJFPSQ` | `` | 状态(DJZTText); 开票状态(KPZT); 合同编号(HTBH); 项目名称(XMMC); 单据编号(DJBH); 申请人(SQR); 预计回款日期(YJHKRQ); 申请日期(SQRQ); 受票方名称(SPF_MC); 累计开票金额(LJKPJE); 合同额(HTE); 本次开票张数(BCKP_ZS); 本次开票金额(BCKPJE); 附件(f_FJ); 备注(BZ); 录入人(LRR); 录入时间(LRSJ) |
| 40 | 发票税务 | 开票登记 | `captured` | 税务/销项/开票登记 | `c68b6f2c3fc8425f9b8a55ba9b4cd1e3` | `C_JXXP_XXKPDJ` | `C_JXXP_XXKPDJ_CB` | 单据状态(DJZTText); 推送结果(TSJG); 金蝶单据编号(OTHER_SYSTEM_CODE); 单据编号(DJBH); 项目名称(XMMC); 受票方名称(SPFMC); 含税金额(JE$C_JXXP_XXKPDJ_CB); 税额(SE$C_JXXP_XXKPDJ_CB); 不含税金额(JE_NO$C_JXXP_XXKPDJ_CB); 附加税(D_SCBSJS_FJS); 开票张数(KPZS); 税率(SLVS); 关联回款金额(GLHKJE); 发票号(FPH$C_JXXP_XXKPDJ_CB... |
| 41 | 发票税务 | 预缴税款 | `captured` | 税务/销项/预缴税款 | `324279dc2fc14e13996b26c21b619e43` | `C_JXXP_YJSKDJ` | `C_JXXP_YJSKDJ_CB` | 状态(DJZTText); 项目名称(XMMC); 单据编号(DJBH); 受票方名称(SPFMC); 交税类型(JSLX$C_JXXP_YJSKDJ_CB); 金额(JE$C_JXXP_YJSKDJ_CB); 发票开具日期(FPKJRQ); 预缴税款日期(YJRQ); 完税凭证号码(PZHM); 附件(f_FJ); 录入人(LRR) |
| 42 | 发票税务 | 进项上报 | `captured` | 税务/进项/进项上报 | `027f61bad00a4651a45dd27f681731e0` | `C_JXXP_ZYFPJJD` | `C_JXXP_ZYFPJJD_CB,C_JXXP_ZYFPJJD_CB_CB` | 状态(DJZTText); 推送结果(TSJG); 金蝶单据编号(OTHER_SYSTEM_CODE); 发票公司类型(D_SCBSJS_FPGSLX$C_JXXP_ZYFPJJD_CB); 单据编号(DJBH); 项目名称(XMMC); 发票开具日期(KPRQ$C_JXXP_ZYFPJJD_CB); 开票单位(GYSMC$C_JXXP_ZYFPJJD_CB); 发票提供人/单位(FPTGF$C_JXXP_ZYFPJJD_CB); 价税合计(HJJE$C_JXXP_ZYFPJJD_CB); 税额(JXSE$C... |
| 43 | 发票税务 | 抵扣登记 | `captured` | 税务/进项/抵扣登记 | `9967dab3faf047ce8bf958c4204931f3` | `C_JXXP_DKDJ_New` | `C_JXXP_DKDJ_CB` | 单据状态(DJZTText); 单据编号(DJBH); 是否转出(SFZC); 项目名称(XMMC); 开票单位(KPDW$C_JXXP_DKDJ_CB); 发票号(FPHM$C_JXXP_DKDJ_CB); 抵扣税额(DKSE$C_JXXP_DKDJ_CB); 抵扣总额(DKJE$C_JXXP_DKDJ_CB); 抵扣附加税(D_SCBSJS_DKFJS$C_JXXP_DKDJ_CB); 备注(BZ); 录入人(LRR); 单据日期(DJRQ) |
| 44 | 发票税务 | 外经证登记 | `captured` | 税务/外经证/外经证登记 | `b859cea258a748c985fe800cfaa5270e` | `ZJGL_WJZ_WJZDJB` | `` | 单据状态(DJZTText); 单据编号(DJBH); 项目名称(XMMC); 纳税人名称(NSRMC); 纳税人识别号(NSRSBH); 经办人手机(JBRSJ); 区域涉税事项联系人(QYSSSXLXR); 区域涉税事项联系人座机手机(QYSSSXLXRSJ); 跨区域经营地址(KQYJYDZ); 经营方式(JYFS); 合同名称(HTMC); 合同金额(HTJE); 合同开始日期(HTKSRQ); 合同结束日期(HTJSRQ); 合同相对方名称(HTXDFMC); 合同相对方名称编号(HTXDFMCNS... |
| 45 | 成本报表 | 供货合同分析 | `custom_or_non_lowcode_link` | 报表/成本报表/供货合同分析 | `` | `` | `` |  |
| 46 | 成本报表 | 库存统计表（新） | `report_config_id_captured` | 报表/成本报表/库存统计表（新） | `b6977b9743334b6cb8f35dc5768e1a5e` | `` | `` |  |
| 47 | 成本报表 | 账户收支统计表 | `report_config_id_captured` | 报表/成本报表/账户收支统计表 | `868e20eb104b4847854d458a0232268e` | `` | `` |  |
| 48 | 成本报表 | 成本统计表（综合） | `report_config_id_captured` | 报表/成本报表/成本统计表（综合） | `ad8b30d6c2f145598232d835c631540f` | `` | `` |  |
| 49 | 成本报表 | 投标保证金报表 | `report_config_id_captured` | 报表/成本报表/投标保证金报表 | `2205259cb52c43b79cfe997ee1f4b643` | `` | `` |  |
| 50 | 成本报表 | 发票成本进度报表 | `report_config_id_captured` | 报表/成本报表/发票成本进度报表 | `0b44ca60c88a4845b8f489b346896853` | `` | `` |  |
| 51 | 成本报表 | 发票分析报表 | `report_config_id_captured` | 报表/成本报表/发票分析报表 | `0c3c8434fff54c9e80fb3e483c318150` | `` | `` |  |
| 52 | 财税报表 | 项目经营统计表 | `report_config_id_captured` | 报表/财税报表/项目经营统计表 | `c901291a239649bf8e93e91255fc86b4` | `` | `` |  |
| 53 | 财税报表 | 应收应付报表 | `report_config_id_captured` | 报表/财税报表/应收应付报表 | `87f061c0258145239daa5bb639a4cfb3` | `` | `` |  |
| 54 | 分析大屏 | 成本大屏 | `menu_without_link` | 报表/分析大屏/成本大屏 | `` | `` | `` |  |
| 55 | 分析大屏 | 经营大屏 | `menu_without_link` | 报表/分析大屏/经营大屏 | `` | `` | `` |  |

## 已确认的关键口径

- `预缴税款`：老系统路径 `税务/销项/预缴税款`，ConfigId `324279dc2fc14e13996b26c21b619e43`，主表 `C_JXXP_YJSKDJ`，从表 `C_JXXP_YJSKDJ_CB`。列表启用从表展开，用户可见 `交税类型` 来源为 `JSLX$C_JXXP_YJSKDJ_CB`，`金额` 来源为 `JE$C_JXXP_YJSKDJ_CB`，`完税凭证号码` 为配置 SQL 派生字段 `PZHM`。
- `开票登记`：主表 `C_JXXP_XXKPDJ`，从表 `C_JXXP_XXKPDJ_CB`，含税/税额/不含税分别来自从表 `JE/SE/JE_NO`。
- `到款确认表`：主表 `ZJGL_SZQR_DKQRB`，用户列表不是单纯资金收入，而是工程款确认口径，包含本期收款、代扣代缴、拨付金额、形象进度等。
- `付款还保证金`、`付款还保证金退回`：55 清单名称和当前老系统菜单名不完全一致，live 菜单对应 `付保证金`、`付保证金退回`，已按 alias 捕获，后续落新系统时需保留用户文案确认。

## 下一步

1. 对 42 个 `captured` 表单入口，逐个比对新系统目标模型和列表 alias 字段。
2. 对 8 个报表入口补 `LowCode/Report` schema 抓取。
3. 对 3 个自定义页面和 2 个大屏入口补专用运行探针。
4. 修正迁移适配器和投影时，只允许使用本矩阵的主表/从表字段来源，不再做跨层回填。
