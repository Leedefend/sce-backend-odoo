import fs from 'node:fs';
import net from 'node:net';
import path from 'node:path';

const ARTIFACTS_DIR = String(process.env.ARTIFACTS_DIR || 'artifacts').trim() || 'artifacts';
const gateways = String(process.env.GATEWAY_BASE_URLS || 'http://localhost:8069')
  .split(',')
  .map((item) => item.trim().replace(/\/+$/, ''))
  .filter(Boolean);
const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
const outDir = path.join(ARTIFACTS_DIR, 'codex', 'host-permission-lane-diag', ts);

function writeJson(fileName, payload) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, fileName), `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

function probeTcp(host, port, timeoutMs = 1500) {
  return new Promise((resolve) => {
    const startedAt = Date.now();
    const socket = net.createConnection({ host, port });
    let settled = false;
    const finish = (ok, error = '') => {
      if (settled) return;
      settled = true;
      socket.destroy();
      resolve({ ok, error, elapsed_ms: Date.now() - startedAt });
    };
    socket.setTimeout(timeoutMs);
    socket.on('connect', () => finish(true));
    socket.on('timeout', () => finish(false, 'tcp_timeout'));
    socket.on('error', (error) => finish(false, String(error?.message || error)));
  });
}

const summary = {
  status: 'PENDING',
  ts,
  gateways,
  checks: [],
};

for (const gateway of gateways) {
  const parsed = new URL(gateway);
  const host = parsed.hostname;
  const port = Number(parsed.port || (parsed.protocol === 'https:' ? 443 : 80));
  const tcp = await probeTcp(host, port, 1500);
  const errorText = String(tcp.error || '').toLowerCase();
  const permissionBlocked = !tcp.ok && errorText.includes('eperm');
  summary.checks.push({
    gateway,
    host,
    port,
    tcp_ok: tcp.ok,
    elapsed_ms: tcp.elapsed_ms,
    error: tcp.error || '',
    permission_lane_blocked: permissionBlocked,
  });
}

const hasPermissionBlocked = summary.checks.some((item) => item.permission_lane_blocked);
const hasReachable = summary.checks.some((item) => item.tcp_ok);

if (hasPermissionBlocked) {
  summary.status = 'FAIL';
  summary.classification = 'permission_lane_blocked';
  summary.error = 'deterministic_connect_eperm';
} else if (!hasReachable) {
  summary.status = 'FAIL';
  summary.classification = 'network_unreachable';
  summary.error = 'no_tcp_reachability';
} else {
  summary.status = 'PASS';
  summary.classification = 'tcp_reachable';
}

writeJson('summary.json', summary);
console.log(`[host_permission_lane_diag] artifacts: ${outDir}`);
if (summary.status !== 'PASS') {
  throw new Error(`${summary.classification}: ${summary.error}`);
}
