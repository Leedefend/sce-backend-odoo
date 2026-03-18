import type { ProjectionRefreshPolicy } from './sceneActionProtocol';

type RefreshTarget = 'scene_projection' | 'workbench_projection' | 'role_surface_projection';

export interface ProjectionRefreshContext {
  policy?: ProjectionRefreshPolicy | null;
  refreshScene?: () => Promise<void> | void;
  refreshWorkbench?: () => Promise<void> | void;
  refreshRoleSurface?: () => Promise<void> | void;
  recordTrace?: (params: { intent: string; writeMode?: string; latencyMs?: number | null }) => void;
}

function normalizeTargets(policy?: ProjectionRefreshPolicy | null): RefreshTarget[] {
  const rows = Array.isArray(policy?.on_success) ? policy?.on_success : [];
  const out: RefreshTarget[] = [];
  const seen = new Set<string>();
  for (const item of rows) {
    const target = String(item || '').trim().toLowerCase();
    if (!target || seen.has(target)) continue;
    if (target === 'scene_projection' || target === 'workbench_projection' || target === 'role_surface_projection') {
      seen.add(target);
      out.push(target as RefreshTarget);
    }
  }
  return out;
}

export async function executeProjectionRefresh(ctx: ProjectionRefreshContext) {
  const startedAt = Date.now();
  const targets = normalizeTargets(ctx.policy);
  for (const target of targets) {
    if (target === 'scene_projection') {
      await ctx.refreshScene?.();
    } else if (target === 'workbench_projection') {
      await ctx.refreshWorkbench?.();
    } else if (target === 'role_surface_projection') {
      await ctx.refreshRoleSurface?.();
    }
  }
  const elapsed = Date.now() - startedAt;
  ctx.recordTrace?.({
    intent: 'projection.refresh',
    writeMode: targets.join(','),
    latencyMs: elapsed,
  });
  return {
    targetCount: targets.length,
    targets,
    latencyMs: elapsed,
  };
}

