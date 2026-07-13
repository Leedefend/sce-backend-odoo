import type { BusinessConfigSnapshotComparePayload } from '../../api/businessConfig';

export function normalizeSnapshotFileToken(value: string) {
  return String(value || 'business-config').replace(/[^a-zA-Z0-9_-]+/g, '-');
}

function snapshotContractIdentity(row: Partial<BusinessConfigSnapshotComparePayload['added'][number]>) {
  return {
    name: row.name || '',
    model: row.model || '',
    view_type: row.view_type || '',
    action_id: Number(row.action_id || 0),
    view_id: Number(row.view_id || 0),
    role_key: row.role_key || '',
  };
}

export function buildSnapshotRemediationPlan(result: BusinessConfigSnapshotComparePayload) {
  const generatedAt = new Date().toISOString();
  const actions = [
    ...result.added.map((row) => ({
      action: 'review_added_contract',
      severity: 'review_required',
      reason: '当前环境存在基线快照中没有的业务配置合同，确认是否应沉淀到目标环境或回退。',
      contract: snapshotContractIdentity(row),
      current: {
        status: row.status,
        version_no: row.version_no,
        payload_hash: row.payload_hash || '',
      },
    })),
    ...result.removed.map((row) => ({
      action: 'restore_or_accept_removed_contract',
      severity: 'review_required',
      reason: '基线快照存在但当前环境缺失该业务配置合同，确认是否需要从基线恢复或接受删除。',
      contract: snapshotContractIdentity(row),
      baseline: {
        status: row.status,
        version_no: row.version_no,
        payload_hash: row.payload_hash || '',
      },
    })),
    ...result.changed.map((row) => ({
      action: 'review_changed_contract',
      severity: 'review_required',
      reason: '当前环境与基线快照的业务配置合同状态或内容不同，确认保留当前版本还是按基线调整。',
      contract: {
        key: row.key,
        name: row.name || '',
        model: row.model || '',
        view_type: row.view_type || '',
      },
      baseline: {
        status: row.previous_status || '',
        version_no: row.previous_version_no || 0,
      },
      current: {
        status: row.current_status || '',
        version_no: row.current_version_no || 0,
      },
    })),
  ];
  return {
    schema_version: 'business_config_snapshot_remediation_plan.v1',
    generated_at: generatedAt,
    source: 'business_config_snapshot_compare',
    current_database: result.current_database,
    baseline_database: result.baseline_database,
    summary: {
      current_contract_count: result.current_contract_count,
      baseline_contract_count: result.baseline_contract_count,
      added_count: result.added_count,
      removed_count: result.removed_count,
      changed_count: result.changed_count,
      action_count: actions.length,
    },
    acceptance: {
      product_boundary: '仅包含低代码配置差异项。',
      execution_policy: '本清单用于上线复核，变更应通过低代码配置页面、迁移脚本或客户模块基线完成。',
      required_after_action: [
        '复核配置快照一致性',
        '复核低代码运行边界',
        '复核产品界面无工程口径残留',
      ],
    },
    actions,
  };
}
