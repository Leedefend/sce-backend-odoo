app_config_engine/
├─ controllers/
│  └─ contract_api.py            # 仅做HTTP入口 & 调度（<=150行）
├─ contract/                     # 新增：契约V2的领域层
│  ├─ dispatcher.py              # subject分派：nav/menu/action/model/operation
│  ├─ resolvers/
│  │  ├─ menu_resolver.py        # 菜单解析（含“向下搜索第一个可用叶子”）
│  │  └─ action_resolver.py      # 动作解析（id/xmlid，superuser读取元数据）
│  ├─ services/
│  │  ├─ contract_service.py     # 组装完整契约（views/fields/permissions/search/buttons...）
│  │  └─ data_service.py         # with_data 首屏数据查询（严格用用户env）
│  ├─ readers/
│  │  └─ config_reader.py        # 统一“配置类模型 sudo 读取”入口
│  ├─ normalizers/
│  │  ├─ payload_normalizer.py   # 请求负载规范化/默认值填充
│  │  └─ contract_normalizer.py  # 返回结构统一化（data.records/next_offset等）
│  ├─ cache/
│  │  └─ etag.py                 # 稳定ETag计算（版本+关键查询参数）
│  ├─ validators/
│  │  └─ payload_validator.py    # subject必填、参数类型校验
│  └─ utils/response.py          # 统一 make_ok/make_err、错误模型
└─ tests/
   └─ test_contract_api.py       # SavepointCase：nav/menu/action最小回归
