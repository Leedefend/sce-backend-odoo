import BlockMetricRow from '../components/page/blocks/BlockMetricRow.vue';
import BlockTodoList from '../components/page/blocks/BlockTodoList.vue';
import BlockAlertPanel from '../components/page/blocks/BlockAlertPanel.vue';
import BlockEntryGrid from '../components/page/blocks/BlockEntryGrid.vue';
import BlockRecordSummary from '../components/page/blocks/BlockRecordSummary.vue';
import BlockProgressSummary from '../components/page/blocks/BlockProgressSummary.vue';
import BlockActivityFeed from '../components/page/blocks/BlockActivityFeed.vue';
import BlockAccordionGroup from '../components/page/blocks/BlockAccordionGroup.vue';

const BLOCK_REGISTRY: Record<string, object> = {
  metric: BlockMetricRow,
  metric_row: BlockMetricRow,
  progress_summary: BlockProgressSummary,
  record_summary: BlockRecordSummary,
  todo: BlockTodoList,
  todo_list: BlockTodoList,
  activity_feed: BlockActivityFeed,
  alert: BlockAlertPanel,
  alert_panel: BlockAlertPanel,
  entry: BlockEntryGrid,
  entry_grid: BlockEntryGrid,
  accordion_group: BlockAccordionGroup,
};

export function resolveBlockComponent(blockType: string): object | null {
  const normalized = String(blockType || '').trim().toLowerCase();
  if (!normalized) return null;
  return BLOCK_REGISTRY[normalized] || null;
}

export function supportedBlockTypes(): string[] {
  return Object.keys(BLOCK_REGISTRY).sort();
}
