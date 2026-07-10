/* eslint-disable @typescript-eslint/no-unused-vars */
<template>
  <section class="page sc-page sc-product-workspace-stack" data-product-page-mode="list">
    <PageHeader
      v-if="status !== 'ok' && status !== 'empty'"
      :title="title"
      :subtitle="subtitle"
    />

    <StatusPanel v-if="loading" :title="uiLabel('loading_list', '正在加载列表...')" variant="info" />
    <StatusPanel
      v-else-if="status === 'error'"
      :title="errorCopy.title"
      :message="errorCopy.message"
      :trace-id="error?.traceId || traceId"
      :error-code="error?.code || errorCode"
      :reason-code="error?.reasonCode"
      :error-category="error?.errorCategory"
      :error-details="error?.details"
      :retryable="error?.retryable"
      :hint="errorCopy.hint || errorHint"
      :suggested-action="error?.suggestedAction"
      variant="error"
      :on-retry="onReload"
    />
    <template v-else-if="status === 'empty'">
      <section class="list-toolbar sc-product-page-toolbar">
        <div class="list-title">
          <h2>{{ title }}</h2>
          <p v-if="toolbarSubtitle">{{ toolbarSubtitle }}</p>
        </div>
        <div class="list-header-toolbar">
          <slot name="toolbar"></slot>
        </div>
        <div v-if="showPlainSearch" class="list-plain-search">
          <input
            type="search"
            :value="plainSearchDraft"
            :disabled="loading"
            :placeholder="uiLabel('plain_search_placeholder', '输入关键字搜索')"
            @compositionstart="plainSearchComposing = true"
            @compositionend="onPlainSearchCompositionEnd"
            @input="onPlainSearchInput"
            @keydown.enter.prevent="submitPlainSearch"
          />
          <button type="button" class="pagination-btn" :disabled="loading" @click="submitPlainSearch">
            {{ uiLabel('search_submit', '搜索') }}
          </button>
        </div>
      </section>
      <section class="list-empty-state">
        <div class="list-empty-copy">
          <h2>{{ emptyStateTitle }}</h2>
          <p>{{ emptyStateMessage }}</p>
        </div>
        <div class="list-empty-actions">
          <button
            v-if="canCreateRecord"
            type="button"
            class="list-empty-primary"
            :disabled="loading"
            @click="onCreate"
          >
            {{ createLabelText }}
          </button>
          <button type="button" class="list-empty-secondary" :disabled="loading" @click="onReload">
            {{ uiLabel('empty_retry', '刷新') }}
          </button>
        </div>
      </section>
      <section class="pagination-footer pagination-footer--count-only">
        <div class="pagination-actions pagination-actions--bottom">
          <span class="pagination-total">{{ listRecordCountText }}</span>
        </div>
      </section>
    </template>

    <template v-else>
      <section class="list-toolbar sc-product-page-toolbar">
        <div class="list-title">
          <h2>{{ title }}</h2>
          <p v-if="toolbarSubtitle">{{ toolbarSubtitle }}</p>
        </div>
        <div class="list-header-toolbar">
          <slot name="toolbar"></slot>
        </div>
        <div v-if="showPlainSearch" class="list-plain-search">
          <input
            type="search"
            :value="plainSearchDraft"
            :disabled="loading"
            :placeholder="uiLabel('plain_search_placeholder', '输入关键字搜索')"
            @compositionstart="plainSearchComposing = true"
            @compositionend="onPlainSearchCompositionEnd"
            @input="onPlainSearchInput"
            @keydown.enter.prevent="submitPlainSearch"
          />
          <button type="button" class="pagination-btn" :disabled="loading" @click="submitPlainSearch">
            {{ uiLabel('search_submit', '搜索') }}
          </button>
        </div>
      </section>

      <section v-if="enableSummaryStrip && summaryItems.length" class="summary-strip sc-product-summary-strip">
        <article v-for="item in summaryItems" :key="item.key" class="summary-card" :class="`tone-${item.tone || 'neutral'}`">
          <p class="summary-label">{{ item.label }}</p>
          <p class="summary-value">{{ item.value }}</p>
        </article>
      </section>

      <section v-if="showBatchBar" class="batch-bar sc-product-feedback-layer">
        <span>{{ uiLabel('selected_count', '已选 {count} 条', { count: selectedCount }) }}</span>
        <button
          v-for="action in selectionActions"
          :key="`selection-action-${action.key}`"
          type="button"
          :disabled="loading || !selectedCount || !action.enabled"
          :title="action.hint || ''"
          @click="runSelectionAction(action.key)"
        >
          {{ action.label }}
        </button>
        <button type="button" class="ghost" :disabled="loading" @click="clearSelection">{{ uiLabel('clear', '清空') }}</button>
        <span v-if="selectedCount > 0 && batchMessage" class="batch-message">{{ batchMessage }}</span>
      </section>
      <p v-if="attachmentErrorText" class="list-inline-feedback is-error">{{ attachmentErrorText }}</p>

      <section class="table sc-product-main-surface">
	        <section v-if="showGroupedRows" class="grouped-table">
        <header class="grouped-toolbar">
          <div class="grouped-toolbar-title">
            <span>{{ uiLabel('grouped_result', '分组结果') }}</span>
            <span v-if="groupWindowInfoText" class="group-window-info">{{ groupWindowInfoText }}</span>
          </div>
          <div class="grouped-toolbar-actions">
            <button
              v-if="onGroupWindowPrev"
              type="button"
              class="grouped-sort-btn"
              :disabled="loading || !canGroupWindowPrev"
              @click="onGroupWindowPrev"
            >
              {{ uiLabel('group_window_prev', '上一组') }}
            </button>
            <button
              v-if="onGroupWindowNext"
              type="button"
              class="grouped-sort-btn"
              :disabled="loading || !canGroupWindowNext"
              @click="onGroupWindowNext"
            >
              {{ uiLabel('group_window_next', '下一组') }}
            </button>
            <button
              type="button"
              class="grouped-sort-btn"
              :disabled="!groupedRows.length || !hasCollapsedGroups"
              @click="expandAllGroups"
            >
              {{ uiLabel('expand_all', '全部展开') }}
            </button>
            <button
              type="button"
              class="grouped-sort-btn"
              :disabled="!groupedRows.length || allGroupsCollapsed"
              @click="collapseAllGroups"
            >
              {{ uiLabel('collapse_all', '全部收起') }}
            </button>
            <button type="button" class="grouped-sort-btn" @click="toggleGroupSort">
              {{ groupSortLabel }}
            </button>
            <label v-if="onGroupSampleLimitChange" class="group-sample-limit">
              <span>{{ uiLabel('group_sample_limit', '每组') }}</span>
              <select
                class="group-sample-limit-select"
                :value="String(effectiveGroupSampleLimit)"
                :disabled="loading"
                @change="onGroupSampleLimitSelectChange"
              >
                <option v-for="option in groupSampleLimitOptions" :key="`group-sample-limit-${option}`" :value="String(option)">
                  {{ option }}
                </option>
              </select>
            </label>
          </div>
        </header>
        <article v-for="group in sortedGroupedRows" :key="group.key" class="group-block">
          <header class="group-head">
            <button type="button" class="group-toggle" @click="toggleGroupCollapsed(group.key)">
              {{ isGroupCollapsed(group.key) ? uiLabel('group_toggle_expand', '展开') : uiLabel('group_toggle_collapse', '收起') }}
            </button>
            <p>{{ group.label }}</p>
            <span>{{ groupCountText(group) }}</span>
            <div v-if="onGroupPageChange && groupTotalPages(group) > 1" class="group-page">
              <button
                type="button"
                class="group-page-btn"
                :disabled="Boolean(group.loading) || !canGroupPagePrev(group)"
                @click="pageGroupPrev(group)"
              >
                {{ uiLabel('pagination_prev', '上一页') }}
              </button>
              <span>{{ groupPageInfoText(group) }}</span>
              <button
                type="button"
                class="group-page-btn"
                :disabled="Boolean(group.loading) || !canGroupPageNext(group)"
                @click="pageGroupNext(group)"
              >
                {{ uiLabel('pagination_next', '下一页') }}
              </button>
              <input
                class="group-page-input"
                :value="groupJumpPageInput[group.key] || String(groupCurrentPage(group))"
                :disabled="Boolean(group.loading) || groupTotalPages(group) <= 1"
                inputmode="numeric"
                pattern="[0-9]*"
                @change="onGroupJumpInputChange(group.key, $event)"
              />
              <button
                type="button"
                class="group-page-btn"
                :disabled="Boolean(group.loading) || groupTotalPages(group) <= 1"
                @click="jumpGroupPage(group)"
              >
                {{ uiLabel('pagination_jump', '跳转') }}
              </button>
            </div>
            <button
              v-if="onOpenGroup"
              type="button"
              class="group-open-btn"
              @click="openGroup(group)"
            >
              {{ uiLabel('group_view_all', '查看全部') }}
            </button>
          </header>
          <table
            v-if="!isGroupCollapsed(group.key)"
            class="group-table"
            :class="{ 'has-selection-column': showSelectionColumn }"
            :style="tableWidthStyle"
          >
            <colgroup>
              <col v-if="showSelectionColumn" class="col-select" />
              <col v-if="showRowNumberColumn" class="col-row-number" />
              <col v-for="col in displayedColumns" :key="`group-col-width-${group.key}-${col}`" :style="columnWidthStyle(col)" />
            </colgroup>
            <thead>
              <tr>
                <th v-if="showSelectionColumn" class="cell-select">
                  <input
                    type="checkbox"
                    :checked="isGroupAllSelected(group)"
                    :disabled="loading || !groupSelectableRows(group).length"
                    @click.stop
                    @change="onGroupSelectAllChange(group, $event)"
                  />
                </th>
                <th v-if="showRowNumberColumn" class="cell-row-number">{{ uiLabel('row_number', '序号') }}</th>
                <th
                  v-for="col in displayedColumns"
                  :key="`group-col-${group.key}-${col}`"
                  class="cell-sortable"
                  :class="[columnDensityClass(col), { 'is-sorted': isSortedColumn(col), 'is-dragging': draggingColumn === col, 'is-sort-disabled': !isColumnSortable(col) }]"
                  :data-column="col"
                  :style="columnWidthStyle(col)"
                  @dragover="onColumnDragOver(col, $event)"
                  @drop="onColumnDrop(col, $event)"
                  @dragend="onColumnDragEnd"
                  @click="toggleColumnSort(col)"
                  @keydown.enter.prevent="toggleColumnSort(col)"
                  @keydown.space.prevent="toggleColumnSort(col)"
                  :tabindex="isColumnSortable(col) ? 0 : -1"
                  :title="columnSortTitle(col)"
                  :aria-sort="columnAriaSort(col)"
                >
                  <button
                    type="button"
                    class="column-drag-handle"
                    :title="uiLabel('column_drag_reorder', '拖动调整列顺序')"
                    draggable="true"
                    @click.stop
                    @keydown.stop
                    @dragstart.stop="onColumnDragStart(col, $event)"
                    @dragend.stop="onColumnDragEnd"
                  ></button>
                  <button
                    type="button"
                    class="column-sort-btn"
                    :title="columnSortTitle(col)"
                    :aria-disabled="!isColumnSortable(col)"
                    draggable="false"
                    @click.stop="toggleColumnSort(col)"
                  >
                    <span>{{ columnLabel(col) }}</span>
                    <span class="sort-indicator" aria-hidden="true">{{ columnSortIndicator(col) }}</span>
                  </button>
                  <button
                    type="button"
                    class="column-resize-handle"
                    :title="uiLabel('column_resize', '调整列宽')"
                    draggable="false"
                    @click.stop
                    @dragstart.stop.prevent
                    @mousedown.stop.prevent="startColumnResize(col, $event)"
                  ></button>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, index) in group.sampleRows"
                :key="`group-row-${group.key}-${String(row.id ?? index)}`"
                :class="rowToneClass(row)"
                @click="handleRowClick(row, $event)"
              >
                <td v-if="showSelectionColumn" class="cell-select" @click.stop>
                  <input
                    v-if="rowId(row)"
                    type="checkbox"
                    :checked="isSelected(row)"
                    :disabled="loading"
                    @change="onRowCheckboxChange(row, $event)"
                  />
                </td>
                <td v-if="showRowNumberColumn" class="cell-row-number">{{ groupedRowNumber(group.key, index) }}</td>
                <td
                  v-for="col in displayedColumns"
                  :key="`group-cell-${group.key}-${String(row.id ?? index)}-${col}`"
                  :style="columnWidthStyle(col)"
                  :class="columnDensityClass(col)"
                >
                  <button
                    v-if="isFavoriteColumn(col)"
                    type="button"
                    class="favorite-toggle"
                    :class="{ active: isFavoriteValue(row[col]) }"
                    :disabled="loading || !onToggleRecordFavorite"
                    :title="favoriteTitle(col)"
                    :aria-label="favoriteTitle(col)"
                    @click.stop="toggleRecordFavorite(row, col)"
                  >
                    <span class="favorite-star" aria-hidden="true">{{ isFavoriteValue(row[col]) ? '★' : '☆' }}</span>
                  </button>
                  <span
                    v-else-if="isStatusLikeColumn(col)"
                    class="status-badge"
                    :class="`tone-${semanticCell(col, row[col]).tone}`"
                  >
                    {{ semanticCell(col, row[col]).text }}
                  </span>
                  <span v-else-if="attachmentLinks(row[col]).length" class="attachment-links">
                    <a
                      v-for="link in attachmentLinks(row[col])"
                      :key="`${link.name}-${link.url}`"
                      href="#"
                      target="_blank"
                      rel="noopener"
                      @click.prevent.stop="previewAttachmentLink(link, row)"
                    >
                      {{ link.name }}
                    </a>
                  </span>
                  <button
                    v-else-if="isAttachmentCountCell(col, row[col])"
                    type="button"
                    class="attachment-count-link"
                    @click.prevent.stop="previewRecordAttachmentCount(row, row[col])"
                  >
                    {{ semanticCell(col, row[col]).text }}
                  </button>
                  <span v-else>{{ semanticCell(col, row[col]).text }}</span>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td v-if="showSelectionColumn" class="cell-select"></td>
                <th v-if="showRowNumberColumn" class="cell-row-number footer-row-label">{{ footerRowLabel('page', group.sampleRows.length) }}</th>
                <td
                  v-for="col in displayedColumns"
                  :key="`group-footer-page-${group.key}-${col}`"
                  :style="columnWidthStyle(col)"
                  :class="[columnDensityClass(col), { 'footer-number': isNumericColumn(col) }]"
                >
                  <span v-if="isNumericColumn(col)" class="footer-number-value">{{ groupFooterCellText(col, group, 'page') }}</span>
                  <template v-else>{{ groupFooterCellText(col, group, 'page') }}</template>
                </td>
              </tr>
              <tr>
                <td v-if="showSelectionColumn" class="cell-select"></td>
                <th v-if="showRowNumberColumn" class="cell-row-number footer-row-label">{{ footerRowLabel('total', group.count) }}</th>
                <td
                  v-for="col in displayedColumns"
                  :key="`group-footer-total-${group.key}-${col}`"
                  :style="columnWidthStyle(col)"
                  :class="[columnDensityClass(col), { 'footer-number': isNumericColumn(col) }]"
                >
                  <span v-if="isNumericColumn(col)" class="footer-number-value">{{ groupFooterCellText(col, group, 'total') }}</span>
                  <template v-else>{{ groupFooterCellText(col, group, 'total') }}</template>
                </td>
              </tr>
            </tfoot>
          </table>
        </article>
      </section>
      <table
        v-if="!showGroupedRows"
        class="flat-table"
        :class="{ 'has-selection-column': showSelectionColumn }"
        :style="tableWidthStyle"
      >
          <colgroup>
            <col v-if="showSelectionColumn" class="col-select" />
          <col v-if="showRowNumberColumn" class="col-row-number" />
            <col v-for="col in displayedColumns" :key="`col-width-${col}`" :style="columnWidthStyle(col)" />
            <col v-if="columnChoices.length" class="col-column-picker" />
          </colgroup>
        <thead>
          <tr>
            <th v-if="showSelectionColumn" class="cell-select">
              <input
                type="checkbox"
                :checked="allSelected"
                :disabled="loading || !selectableRows.length"
                @click.stop
                @change="onSelectAllChange"
              />
            </th>
            <th v-if="showRowNumberColumn" class="cell-row-number">{{ uiLabel('row_number', '序号') }}</th>
            <th
              v-for="col in displayedColumns"
              :key="col"
              class="cell-sortable"
              :class="[columnDensityClass(col), { 'is-sorted': isSortedColumn(col), 'is-dragging': draggingColumn === col, 'is-sort-disabled': !isColumnSortable(col) }]"
              :data-column="col"
              :style="columnWidthStyle(col)"
              @dragover="onColumnDragOver(col, $event)"
              @drop="onColumnDrop(col, $event)"
              @dragend="onColumnDragEnd"
              @click="toggleColumnSort(col)"
              @keydown.enter.prevent="toggleColumnSort(col)"
              @keydown.space.prevent="toggleColumnSort(col)"
              :tabindex="isColumnSortable(col) ? 0 : -1"
              :title="columnSortTitle(col)"
              :aria-sort="columnAriaSort(col)"
            >
              <button
                type="button"
                class="column-drag-handle"
                :title="uiLabel('column_drag_reorder', '拖动调整列顺序')"
                draggable="true"
                @click.stop
                @keydown.stop
                @dragstart.stop="onColumnDragStart(col, $event)"
                @dragend.stop="onColumnDragEnd"
              ></button>
              <button
                type="button"
                class="column-sort-btn"
                :title="columnSortTitle(col)"
                :aria-disabled="!isColumnSortable(col)"
                draggable="false"
                @click.stop="toggleColumnSort(col)"
              >
                <span>{{ columnLabel(col) }}</span>
                <span class="sort-indicator" aria-hidden="true">{{ columnSortIndicator(col) }}</span>
              </button>
              <button
                type="button"
                class="column-resize-handle"
                :title="uiLabel('column_resize', '调整列宽')"
                draggable="false"
                @click.stop
                @dragstart.stop.prevent
                @mousedown.stop.prevent="startColumnResize(col, $event)"
              ></button>
            </th>
            <th v-if="columnChoices.length" ref="columnPickerRoot" class="cell-column-picker">
              <button type="button" class="column-picker-btn" :disabled="loading" @click.stop="columnPickerOpen = !columnPickerOpen">
                {{ uiLabel('column_picker', '列') }}
              </button>
              <span v-if="columnSaveStatusText" class="column-save-badge" :class="`is-${columnSaveStatus}`">
                {{ columnSaveStatusText }}
              </span>
              <div v-if="columnPickerOpen" class="column-picker-menu">
                <label v-for="column in columnChoices" :key="`column-choice-${column.name}`" class="column-choice">
                  <input
                    type="checkbox"
                    :checked="isColumnVisible(column.name)"
                    :disabled="loading || isLastVisibleColumn(column.name)"
                    @change="onColumnVisibilityChange(column.name, $event)"
                  />
                  <span>{{ columnChoiceLabel(column) }}</span>
                </label>
                <button type="button" class="column-reset" :disabled="loading" @click="resetColumnVisibility">{{ uiLabel('column_reset', '恢复默认') }}</button>
                <p v-if="columnSaveStatusText" class="column-save-message" :class="`is-${columnSaveStatus}`">
                  {{ columnSaveStatusText }}
                </p>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, index) in records"
            :key="String(row.id ?? index)"
            :class="rowToneClass(row)"
            @click="handleRowClick(row, $event)"
          >
            <td v-if="showSelectionColumn" class="cell-select" @click.stop>
              <input
                v-if="rowId(row)"
                type="checkbox"
                :checked="isSelected(row)"
                :disabled="loading"
                @change="onRowCheckboxChange(row, $event)"
              />
            </td>
            <td v-if="showRowNumberColumn" class="cell-row-number">{{ flatRowNumber(index) }}</td>
            <td v-for="col in displayedColumns" :key="col" :style="columnWidthStyle(col)" :class="columnDensityClass(col)">
              <button
                v-if="isFavoriteColumn(col)"
                type="button"
                class="favorite-toggle"
                :class="{ active: isFavoriteValue(row[col]) }"
                :disabled="loading || !onToggleRecordFavorite"
                :title="favoriteTitle(col)"
                :aria-label="favoriteTitle(col)"
                @click.stop="toggleRecordFavorite(row, col)"
              >
                <span class="favorite-star" aria-hidden="true">{{ isFavoriteValue(row[col]) ? '★' : '☆' }}</span>
              </button>
              <div v-else-if="isStatusLikeColumn(col)">
                <span class="status-badge" :class="`tone-${semanticCell(col, row[col]).tone}`">
                  {{ semanticCell(col, row[col]).text }}
                </span>
              </div>
              <div v-else-if="isPrimaryTextColumn(col)" class="cell-primary">
                <div class="primary">{{ semanticCell(col, row[col]).text }}</div>
                <div v-if="shouldRenderRowSecondary(col, row)" class="secondary">{{ semanticCell(rowSecondary, row[rowSecondary]).text }}</div>
              </div>
              <div v-else-if="attachmentLinks(row[col]).length" class="attachment-links">
                <a
                  v-for="link in attachmentLinks(row[col])"
                  :key="`${link.name}-${link.url}`"
                  href="#"
                  target="_blank"
                  rel="noopener"
                  @click.prevent.stop="previewAttachmentLink(link, row)"
                >
                  {{ link.name }}
                </a>
              </div>
              <button
                v-else-if="isAttachmentCountCell(col, row[col])"
                type="button"
                class="attachment-count-link"
                @click.prevent.stop="previewRecordAttachmentCount(row, row[col])"
              >
                {{ semanticCell(col, row[col]).text }}
              </button>
              <div v-else>
                {{ semanticCell(col, row[col]).text }}
              </div>
            </td>
            <td v-if="columnChoices.length" class="cell-column-picker"></td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td v-if="showSelectionColumn" class="cell-select"></td>
            <th v-if="showRowNumberColumn" class="cell-row-number footer-row-label">{{ footerRowLabel('page', pageVisibleRows.length) }}</th>
            <td
              v-for="col in displayedColumns"
              :key="`footer-page-${col}`"
              :style="columnWidthStyle(col)"
              :class="[columnDensityClass(col), { 'footer-number': isNumericColumn(col) }]"
            >
              <span v-if="isNumericColumn(col)" class="footer-number-value">{{ footerCellText(col, 'page', pageVisibleRows.length) }}</span>
              <template v-else>{{ footerCellText(col, 'page', pageVisibleRows.length) }}</template>
            </td>
            <td v-if="columnChoices.length" class="cell-column-picker"></td>
          </tr>
          <tr>
            <td v-if="showSelectionColumn" class="cell-select"></td>
            <th v-if="showRowNumberColumn" class="cell-row-number footer-row-label">{{ footerRowLabel('total', listTotal || pageVisibleRows.length) }}</th>
            <td
              v-for="col in displayedColumns"
              :key="`footer-total-${col}`"
              :style="columnWidthStyle(col)"
              :class="[columnDensityClass(col), { 'footer-number': isNumericColumn(col) }]"
            >
              <span v-if="isNumericColumn(col)" class="footer-number-value">{{ footerCellText(col, 'total', listTotal || pageVisibleRows.length) }}</span>
              <template v-else>{{ footerCellText(col, 'total', listTotal || pageVisibleRows.length) }}</template>
            </td>
            <td v-if="columnChoices.length" class="cell-column-picker"></td>
          </tr>
        </tfoot>
      </table>
    </section>

      <section v-if="showGroupedWindowPagination" class="pagination-footer">
        <div class="pagination-actions pagination-actions--bottom">
          <span class="pagination-total">{{ listRecordCountText }}</span>
          <button
            type="button"
            class="pagination-btn"
            :disabled="loading || !canGroupWindowPrev"
            @click="onGroupWindowPrev?.()"
          >
            {{ uiLabel('group_window_prev', '上一组') }}
          </button>
          <span>{{ groupWindowPageText }}</span>
          <button
            type="button"
            class="pagination-btn"
            :disabled="loading || !canGroupWindowNext"
            @click="onGroupWindowNext?.()"
          >
            {{ uiLabel('group_window_next', '下一组') }}
          </button>
        </div>
      </section>
      <section v-else-if="showPagination" class="pagination-footer">
        <div class="pagination-actions pagination-actions--bottom">
          <span class="pagination-total">{{ listRecordCountText }}</span>
          <button
            type="button"
            class="pagination-btn"
            :disabled="loading || !canPagePrev"
            @click="pagePrev"
          >
            {{ uiLabel('pagination_prev', '上一页') }}
          </button>
          <span>{{ paginationPageText }}</span>
          <button
            type="button"
            class="pagination-btn"
            :disabled="loading || !canPageNext"
            @click="pageNext"
          >
            {{ uiLabel('pagination_next', '下一页') }}
          </button>
          <input
            class="pagination-input"
            :value="pageJumpInput"
            :disabled="loading || totalPages <= 1"
            inputmode="numeric"
            pattern="[0-9]*"
            @input="onPageJumpInput"
            @keyup.enter="jumpPage"
          />
          <button
            type="button"
            class="pagination-btn"
            :disabled="loading || totalPages <= 1"
            @click="jumpPage"
          >
            {{ uiLabel('pagination_jump', '跳转') }}
          </button>
          <label class="pagination-size-control">
            <span class="pagination-size-label">{{ uiLabel('pagination_page_size', '每页') }}</span>
            <span class="pagination-size-combo">
              <input
                class="pagination-input pagination-input--size"
                :value="pageLimitInput"
                :disabled="loading"
                inputmode="numeric"
                pattern="[0-9]*"
                @input="onPageLimitInput"
                @change="applyPageLimit"
                @keyup.enter="applyPageLimit"
              />
              <select
                class="pagination-size-select"
                :value="pageLimitOptions.includes(listLimit) ? String(listLimit) : undefined"
                :disabled="loading"
                :aria-label="uiLabel('pagination_page_size_select', '选择每页条数')"
                @change="onPageLimitSelectChange"
              >
                <option v-for="option in pageLimitOptions" :key="`page-limit-${option}`" :value="String(option)">
                  {{ option }}
                </option>
              </select>
            </span>
          </label>
        </div>
      </section>
      <section v-else class="pagination-footer pagination-footer--count-only">
        <div class="pagination-actions pagination-actions--bottom">
          <span class="pagination-total">{{ listRecordCountText }}</span>
        </div>
      </section>

    </template>
    <AttachmentViewer ref="attachmentViewerRef" />
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import StatusPanel from '../components/StatusPanel.vue';
import PageHeader from '../components/page/PageHeader.vue';
import AttachmentViewer from '../components/attachment/AttachmentViewer.vue';
import { resolveEmptyCopy, resolveErrorCopy, type StatusError } from '../composables/useStatus';
import type { SceneListProfile } from '../app/resolvers/sceneRegistry';
import { formatAttachmentReferenceValue, parseAttachmentReferenceLinks } from '../utils/display';
import { attachmentLinkDownloadParams, openExternalAttachmentUrl } from '../utils/filePreview';

type SelectionAction = {
  key: string;
  label: string;
  enabled: boolean;
  hint?: string;
};

type ColumnOption = {
  name: string;
  label: string;
  optional?: string;
  defaultVisible?: boolean;
  sortable?: boolean;
  type?: string;
  widget?: string;
  cellRole?: string;
  mutation?: Record<string, unknown>;
  selection?: Array<{ value: string; label: string }>;
  toneByValue?: Record<string, string>;
};
type GroupSortDirection = 'asc' | 'desc';

const props = defineProps<{
  title: string;
  model: string;
  status: 'loading' | 'ok' | 'empty' | 'error';
  loading: boolean;
  errorMessage?: string;
  traceId?: string;
  errorCode?: number | null;
  errorHint?: string;
  error?: StatusError | null;
  columns: string[];
  records: Array<Record<string, unknown>>;
  onReload: () => void;
  onRowClick: (row: Record<string, unknown>) => void;
  onSearch: (value: string) => void;
  onSort: (value: string) => void;
  sortLabel?: string;
  searchTerm?: string;
  sortOptions?: Array<{ label: string; value: string }>;
  sortValue?: string;
  filterValue?: 'all' | 'active' | 'archived';
  subtitle: string;
  statusLabel: string;
  pageMode?: string;
  sceneKey?: string;
  recordCount?: number;
  listTotalCount?: number | null;
  listOffset?: number;
  listLimit?: number;
  listAggregates?: Record<string, Record<string, unknown>>;
  columnOptions?: ColumnOption[];
  columnVisibility?: Record<string, boolean>;
  columnOrder?: string[];
  columnWidths?: Record<string, number>;
  columnSaveStatus?: 'idle' | 'saving' | 'saved' | 'error';
  uiLabels?: Record<string, string>;
  enableSummaryStrip?: boolean;
  enableGroupedRows?: boolean;
  listProfile?: SceneListProfile | null;
  columnLabels?: Record<string, string>;
  onFilter: (value: 'all' | 'active' | 'archived') => void;
  summaryItems?: Array<{ key: string; label: string; value: string; tone?: string }>;
  selectedIds?: number[];
  selectionActions?: SelectionAction[];
  onToggleSelection?: (id: number, selected: boolean) => void;
  onToggleSelectionAll?: (ids: number[], selected: boolean) => void;
  onRunSelectionAction?: (key: string) => void;
  onClearSelection?: () => void;
  onToggleRecordFavorite?: (row: Record<string, unknown>, field: string, nextValue: boolean) => void | Promise<void>;
  batchMessage?: string;
  groupedRows?: Array<{
    key: string;
    label: string;
    count: number;
    sampleRows: Array<Record<string, unknown>>;
    sampleCount?: number;
    isSampled?: boolean;
    domain?: unknown[];
    pageOffset?: number;
    pageLimit?: number;
    pageCurrent?: number;
    pageTotal?: number;
    pageRangeStart?: number;
    pageRangeEnd?: number;
    pageWindow?: { start?: number; end?: number };
    pageHasPrev?: boolean;
    pageHasNext?: boolean;
    aggregates?: Record<string, Record<string, unknown>>;
    loading?: boolean;
  }>;
  onOpenGroup?: (group: {
    key: string;
    label: string;
    count: number;
    domain?: unknown[];
  }) => void;
  onGroupPageChange?: (group: {
    key: string;
    label: string;
    count: number;
    domain?: unknown[];
    offset: number;
    limit: number;
  }) => void;
  groupWindowOffset?: number;
  groupWindowCount?: number;
  groupWindowTotal?: number;
  groupWindowStart?: number;
  groupWindowEnd?: number;
  canGroupWindowPrev?: boolean;
  canGroupWindowNext?: boolean;
  onGroupWindowPrev?: () => void;
  onGroupWindowNext?: () => void;
  groupSampleLimit?: number;
  onGroupSampleLimitChange?: (limit: number) => void;
  groupSort?: 'asc' | 'desc';
  onGroupSortChange?: (next: 'asc' | 'desc') => void;
  collapsedGroupKeys?: string[];
  onGroupCollapsedChange?: (keys: string[]) => void;
  onPageChange?: (offset: number) => void;
  onPageLimitChange?: (limit: number) => void;
  canCreateRecord?: boolean;
  createLabel?: string;
  onCreate?: () => void;
  showPlainSearch?: boolean;
}>();
const emit = defineEmits<{
  'column-visibility-change': [payload: { visibility: Record<string, boolean> }];
  'column-order-change': [payload: { columnOrder: string[] }];
  'column-widths-change': [payload: { columnWidths: Record<string, number> }];
}>();
const attachmentViewerRef = ref<InstanceType<typeof AttachmentViewer> | null>(null);
const attachmentErrorText = ref('');
function uiLabel(key: string, fallback: string, vars: Record<string, string | number> = {}) {
  const candidate = String(props.uiLabels?.[key] || '').trim();
  const template = candidate || fallback;
  return Object.entries(vars).reduce(
    (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)),
    template,
  );
}

const errorCopy = computed(() =>
  resolveErrorCopy(
    props.error || null,
    props.errorMessage || uiLabel('list_load_failed', '列表加载失败'),
  ),
);
const emptyCopy = computed(() => resolveEmptyCopy('list'));
const createLabelText = computed(() => props.createLabel || uiLabel('create', '新建'));
const emptyStateTitle = computed(() =>
  props.canCreateRecord
    ? uiLabel('empty_create_title', '当前还没有数据')
    : uiLabel('empty_readonly_title', emptyCopy.value.title),
);
const emptyStateMessage = computed(() =>
  props.canCreateRecord
    ? uiLabel('empty_create_message', '可以先新建一条业务记录，开始录入和办理。')
    : uiLabel('empty_readonly_message', emptyCopy.value.message),
);
const showPlainSearch = computed(() => props.showPlainSearch !== false);
const groupedRows = computed(() =>
  Array.isArray(props.groupedRows) ? props.groupedRows : [],
);
const showGroupedRows = computed(() => props.enableGroupedRows === true && groupedRows.value.length > 0);
const groupJumpPageInput = ref<Record<string, string>>({});
const pageJumpInput = ref('');
const pageLimitInput = ref('');
const plainSearchDraft = ref('');
const plainSearchComposing = ref(false);
const observedListLimit = ref(0);
const columnPickerRoot = ref<HTMLElement | null>(null);
const columnPickerOpen = ref(false);
const draggingColumn = ref('');
const resizingColumn = ref('');
const resizeStartX = ref(0);
const resizeStartWidth = ref(0);
const draftColumnWidths = ref<Record<string, number>>({});
const columnSaveStatus = computed(() => props.columnSaveStatus || 'idle');
const columnSaveStatusText = computed(() => {
  if (columnSaveStatus.value === 'saving') return uiLabel('column_saving', '保存中');
  if (columnSaveStatus.value === 'saved') return uiLabel('column_saved', '已保存');
  if (columnSaveStatus.value === 'error') return uiLabel('column_save_error', '保存失败，请重试');
  return '';
});
const groupSortConfig = computed(() => props.listProfile?.grouping?.sort || {});
const groupSortKey = computed(() => String(groupSortConfig.value.key || '').trim());
const groupSortDirections = computed<GroupSortDirection[]>(() => {
  const values = Array.isArray(groupSortConfig.value.directions) ? groupSortConfig.value.directions : [];
  const normalized = values
    .map((item) => String(item || '').trim())
    .filter((item): item is GroupSortDirection => item === 'asc' || item === 'desc');
  return normalized.length ? normalized : ['desc', 'asc'];
});
const groupSortDefaultDirection = computed<GroupSortDirection>(() => {
  const direction = String(groupSortConfig.value.default_direction || '').trim();
  return direction === 'asc' ? 'asc' : 'desc';
});
const groupSortDirection = computed<GroupSortDirection>(() => {
  const direction = props.groupSort === 'asc' || props.groupSort === 'desc'
    ? props.groupSort
    : groupSortDefaultDirection.value;
  return groupSortDirections.value.includes(direction) ? direction : groupSortDirections.value[0];
});
const groupSortDesc = computed(() => groupSortDirection.value === 'desc');
const sortedGroupedRows = computed(() => {
  const rows = [...groupedRows.value];
  if (groupSortKey.value !== 'count') return rows;
  rows.sort((a, b) => {
    const cmp = Number(a.count || 0) - Number(b.count || 0);
    if (cmp === 0) return String(a.label || '').localeCompare(String(b.label || ''));
    return groupSortDesc.value ? -cmp : cmp;
  });
  return rows;
});
const groupSortLabel = computed(() =>
  groupSortDesc.value
    ? uiLabel('group_sort_desc', '按数量降序')
    : uiLabel('group_sort_asc', '按数量升序'),
);
const showGroupedWindowPagination = computed(() =>
  showGroupedRows.value
  && Boolean(props.onGroupWindowPrev || props.onGroupWindowNext)
  && (
    Math.max(0, Math.trunc(Number(props.groupWindowCount || 0))) > 0
    || Boolean(props.canGroupWindowPrev)
    || Boolean(props.canGroupWindowNext)
  ),
);
const groupWindowRange = computed(() => {
  if (!showGroupedRows.value) return '';
  const count = Math.max(0, Math.trunc(Number(props.groupWindowCount || 0)));
  if (count <= 0) return '';
  const offset = Math.max(0, Math.trunc(Number(props.groupWindowOffset || 0)));
  const startRaw = Number(props.groupWindowStart);
  const endRaw = Number(props.groupWindowEnd);
  const totalRaw = Number(props.groupWindowTotal);
  const start = Number.isFinite(startRaw) && startRaw > 0 ? Math.trunc(startRaw) : offset + 1;
  const end = Number.isFinite(endRaw) && endRaw >= start ? Math.trunc(endRaw) : offset + count;
  return { start, end, total: Number.isFinite(totalRaw) && totalRaw >= 0 ? Math.trunc(totalRaw) : null };
});
const groupWindowInfoText = computed(() => {
  if (!groupWindowRange.value) return '';
  const range = groupWindowRange.value;
  if (range.total !== null) {
    return uiLabel('group_window_range_total', '当前显示第 {start}-{end} 组 / 共 {total} 组', range);
  }
  return uiLabel('group_window_range', '当前显示第 {start}-{end} 组', range);
});
const groupWindowPageText = computed(() => {
  if (!groupWindowRange.value) return uiLabel('group_window_page_empty', '分组 0 组');
  const range = groupWindowRange.value;
  if (range.total !== null) {
    return uiLabel('group_window_page_total', '第 {start}-{end} 组 / 共 {total} 组', range);
  }
  return uiLabel('group_window_page', '第 {start}-{end} 组', range);
});
const summaryItems = computed(() => Array.isArray(props.summaryItems) ? props.summaryItems : []);
const collapsedSet = computed(() => new Set(Array.isArray(props.collapsedGroupKeys) ? props.collapsedGroupKeys : []));
const allGroupsCollapsed = computed(() => {
  if (!sortedGroupedRows.value.length) return false;
  return sortedGroupedRows.value.every((item) => collapsedSet.value.has(item.key));
});
const hasCollapsedGroups = computed(() => {
  if (!sortedGroupedRows.value.length) return false;
  return sortedGroupedRows.value.some((item) => collapsedSet.value.has(item.key));
});
function normalizeCellRawValue(value: unknown) {
  if (Array.isArray(value)) {
    if (value.length > 1 && value[1] !== null && value[1] !== undefined) return value[1];
    if (value.length) return value[0];
  }
  return value;
}

function scalarTexts(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value
      .filter((item) => item !== null && item !== undefined)
      .map((item) => String(item).trim())
      .filter(Boolean);
  }
  const text = String(value ?? '').trim();
  return text ? [text] : [];
}

function rowNumericCellValue(value: unknown): number | null {
  const raw = Array.isArray(value) ? (value.length > 1 ? value[1] : value[0]) : value;
  if (typeof raw === 'number' && Number.isFinite(raw)) return raw;
  if (typeof raw !== 'string') return null;
  const cleaned = raw.replace(/,/g, '').trim();
  if (!cleaned) return null;
  const numeric = Number(cleaned);
  return Number.isFinite(numeric) ? numeric : null;
}

function isOutputInvoiceAdjustmentRow(row: Record<string, unknown>) {
  if (props.model !== 'sc.output.invoice.ledger') return false;
  const adjustmentTexts = scalarTexts(row.adjustment_kind).map((text) => text.toLowerCase());
  if (adjustmentTexts.some((text) => text === 'signed_adjustment' || text.includes('冲抵') || text.includes('红冲'))) {
    return true;
  }
  return ['invoice_amount', 'amount_no_tax', 'tax_amount', 'surcharge_amount']
    .some((field) => {
      const numeric = rowNumericCellValue(row[field]);
      return numeric !== null && numeric < 0;
    });
}

function rowToneClass(row: Record<string, unknown>) {
  return { 'row-tone-danger': isOutputInvoiceAdjustmentRow(row) };
}

function selectionLabel(option: ColumnOption | null, value: unknown) {
  const raw = normalizeCellRawValue(value);
  const key = String(raw ?? '').trim();
  if (!key || !Array.isArray(option?.selection)) return '';
  return option.selection.find((item) => item.value === key)?.label || '';
}

function semanticCell(field: string, value: unknown) {
  const option = columnOption(field);
  const raw = normalizeCellRawValue(value);
  const selectionText = selectionLabel(option, value);
  const numericText = formatNumericCellValue(field, raw);
  const fieldType = String(option?.type || '').trim().toLowerCase();
  const rawText = typeof raw === 'string' ? raw : '';
  const rawTrimmedText = rawText.trim();
  const attachmentText = rawText && /\|\s*(?:legacy-file-id|legacy-file|https?|file):\/\//i.test(rawText)
    ? formatAttachmentReferenceValue(rawText)
    : '';
  const text = selectionText
    || (raw === null || raw === undefined || raw === ''
      ? (isNumericDisplayColumn(field) ? '0' : '--')
      : (raw === false && isNumericDisplayColumn(field)
        ? '0'
      : (rawTrimmedText === '--' && isNumericDisplayColumn(field)
        ? '0'
      : (typeof raw === 'boolean'
        ? (fieldType === 'boolean' ? uiLabel(raw ? 'boolean_true' : 'boolean_false', raw ? '是' : '否') : '--')
        : attachmentText || numericText || String(raw)))));
  const toneKey = String(raw ?? '').trim();
  const tone = option?.cellRole === 'status'
    ? (option.toneByValue?.[toneKey] || 'neutral')
    : 'neutral';
  return { text, tone };
}

function attachmentLinks(value: unknown) {
  return parseAttachmentReferenceLinks(value);
}

async function previewAttachmentLink(link: { name: string; url: string }, row: Record<string, unknown>) {
  attachmentErrorText.value = '';
  try {
    const context = {
      model: props.model,
      res_id: Number(row.id || 0) || undefined,
    };
    const params = attachmentLinkDownloadParams(link, context);
    if (params) {
      await attachmentViewerRef.value?.open(params, link.name);
      return;
    }
    openExternalAttachmentUrl(link.url);
  } catch (err) {
    attachmentErrorText.value = err instanceof Error ? err.message : uiLabel('attachment_open_failed', '附件打开失败，请稍后重试。');
  }
}

function isAttachmentCountCell(field: string, value: unknown) {
  const label = columnLabel(field).trim();
  const text = String(normalizeCellRawValue(value) ?? '').trim();
  return label === '附件' && /^附件\([1-9]\d*\)$/.test(text);
}

async function previewRecordAttachmentCount(row: Record<string, unknown>, value: unknown) {
  const text = String(normalizeCellRawValue(value) ?? '').trim() || '附件';
  attachmentErrorText.value = '';
  try {
    await attachmentViewerRef.value?.open({
      model: props.model,
      res_id: Number(row.id || 0) || undefined,
    }, text);
  } catch (err) {
    attachmentErrorText.value = err instanceof Error ? err.message : uiLabel('attachment_open_failed', '附件打开失败，请稍后重试。');
  }
}

function isStatusColumn(field: string) {
  const option = columnOption(field);
  const normalized = String(field || '').trim();
  return option?.cellRole === 'status'
    || props.listProfile?.status_field === normalized
    || ['document_status', 'state', 'status', 'lifecycle_state'].includes(normalized);
}

function isStatusLikeColumn(field: string) {
  const label = columnLabel(field).trim();
  return isStatusColumn(field) || /^(状态|单据状态|开票状态|付款状态|结算状态|支付申请状态|账户状态)$/.test(label);
}

function isPrimaryTextColumn(field: string) {
  return field === rowPrimary.value && !isStatusLikeColumn(field);
}

function shouldRenderRowSecondary(field: string, row: Record<string, unknown>) {
  void field;
  void row;
  return false;
}

function isFavoriteColumn(field: string) {
  const option = columnOption(field);
  return option?.widget === 'boolean_favorite';
}

function isFavoriteValue(value: unknown) {
  return value === true || value === 1 || String(value).trim().toLowerCase() === 'true';
}

function favoriteTitle(field: string) {
  return columnLabel(field);
}

function toggleRecordFavorite(row: Record<string, unknown>, field: string) {
  if (!props.onToggleRecordFavorite || !isFavoriteColumn(field)) return;
  props.onToggleRecordFavorite(row, field, !isFavoriteValue(row[field]));
}

function toggleGroupCollapsed(key: string) {
  if (!props.onGroupCollapsedChange) return;
  const set = new Set(collapsedSet.value);
  if (set.has(key)) set.delete(key);
  else set.add(key);
  props.onGroupCollapsedChange(Array.from(set));
}

function isGroupCollapsed(key: string) {
  return collapsedSet.value.has(key);
}

function toggleGroupSort() {
  if (!props.onGroupSortChange) return;
  const directions = groupSortDirections.value;
  const currentIndex = directions.indexOf(groupSortDirection.value);
  const nextDirection = directions[(currentIndex + 1) % directions.length] || groupSortDefaultDirection.value;
  props.onGroupSortChange(nextDirection);
}

function onGroupSampleLimitSelectChange(event: Event) {
  const raw = Number((event.target as HTMLSelectElement).value || 0);
  if (!Number.isFinite(raw) || raw <= 0) return;
  props.onGroupSampleLimitChange?.(Math.trunc(raw));
}

function openGroup(group: { key: string; label: string; count: number; domain?: unknown[] }) {
  props.onOpenGroup?.(group);
}

function flatRowNumber(index: number) {
  return Math.trunc(Number(index || 0)) + 1;
}

function groupedRowNumber(groupKey: string, rowIndex: number) {
  const currentIndex = sortedGroupedRows.value.findIndex((group) => group.key === groupKey);
  const priorVisibleCount = sortedGroupedRows.value
    .slice(0, Math.max(0, currentIndex))
    .reduce((total, group) => {
      if (isGroupCollapsed(group.key)) return total;
      return total + (Array.isArray(group.sampleRows) ? group.sampleRows.length : 0);
    }, 0);
  return priorVisibleCount + Math.trunc(Number(rowIndex || 0)) + 1;
}

function groupVisibleCount(group: { sampleRows?: Array<Record<string, unknown>>; sampleCount?: number }) {
  const explicit = Number(group.sampleCount);
  if (Number.isFinite(explicit) && explicit >= 0) return Math.trunc(explicit);
  return Array.isArray(group.sampleRows) ? group.sampleRows.length : 0;
}

function groupCountText(group: { count: number; sampleRows?: Array<Record<string, unknown>>; sampleCount?: number; isSampled?: boolean }) {
  const total = Math.max(0, Math.trunc(Number(group.count || 0)));
  const visible = groupVisibleCount(group);
  const sampled = typeof group.isSampled === 'boolean' ? group.isSampled : visible < total;
  if (sampled) {
    return uiLabel('group_count_sampled', '共 {total} 条 · 当前显示 {visible} 条', { total, visible });
  }
  return uiLabel('group_count', '共 {count} 条', { count: total });
}

function resolveGroupPageLimit(group: { pageLimit?: number }) {
  const limitRaw = Number(group.pageLimit || effectiveGroupSampleLimit.value);
  return Number.isFinite(limitRaw) && limitRaw > 0 ? Math.trunc(limitRaw) : 3;
}

function resolveGroupPageOffset(group: { pageOffset?: number; count: number; pageLimit?: number }) {
  const limit = resolveGroupPageLimit(group);
  const maxOffset = Math.max(0, Number(group.count || 0) - limit);
  const offsetRaw = Number(group.pageOffset || 0);
  if (!Number.isFinite(offsetRaw)) return 0;
  const clamped = Math.min(Math.max(Math.trunc(offsetRaw), 0), maxOffset);
  return Math.floor(clamped / limit) * limit;
}

function resolveGroupPageMeta(group: {
  count: number;
  pageOffset?: number;
  pageLimit?: number;
  pageCurrent?: number;
  pageTotal?: number;
  pageRangeStart?: number;
  pageRangeEnd?: number;
}) {
  const total = Math.max(0, Number(group.count || 0));
  const limit = Math.max(1, resolveGroupPageLimit(group));
  const offset = resolveGroupPageOffset(group);
  const fallbackTotal = Math.max(1, Math.ceil(total / limit));
  const fallbackCurrent = Math.floor(offset / limit) + 1;
  const fallbackStart = total > 0 ? offset + 1 : 0;
  const fallbackEnd = total > 0 ? Math.min(total, offset + limit) : 0;
  const backendTotal = Math.trunc(Number(group.pageTotal || 0));
  const backendCurrent = Math.trunc(Number(group.pageCurrent || 0));
  const backendStart = Math.trunc(Number(group.pageRangeStart || 0));
  const backendEnd = Math.trunc(Number(group.pageRangeEnd || 0));
  const backendWindow = (group as { pageWindow?: { start?: unknown; end?: unknown } }).pageWindow;
  const backendWindowStart = Math.trunc(Number(backendWindow?.start || 0));
  const backendWindowEnd = Math.trunc(Number(backendWindow?.end || 0));
  return {
    totalPages: backendTotal > 0 ? backendTotal : fallbackTotal,
    currentPage: backendCurrent > 0 ? backendCurrent : fallbackCurrent,
    rangeStart: backendWindowStart > 0 ? backendWindowStart : (backendStart > 0 ? backendStart : fallbackStart),
    rangeEnd: backendWindowEnd > 0 ? backendWindowEnd : (backendEnd > 0 ? backendEnd : fallbackEnd),
  };
}

function canGroupPagePrev(group: { count: number; pageOffset?: number; pageLimit?: number }) {
  if (typeof (group as { pageHasPrev?: unknown }).pageHasPrev === 'boolean') {
    return Boolean((group as { pageHasPrev?: unknown }).pageHasPrev);
  }
  return resolveGroupPageOffset(group) > 0;
}

function canGroupPageNext(group: { count: number; pageOffset?: number; pageLimit?: number }) {
  if (typeof (group as { pageHasNext?: unknown }).pageHasNext === 'boolean') {
    return Boolean((group as { pageHasNext?: unknown }).pageHasNext);
  }
  const offset = resolveGroupPageOffset(group);
  const limit = resolveGroupPageLimit(group);
  return offset + limit < Number(group.count || 0);
}

function groupPageRangeText(group: { count: number; pageOffset?: number; pageLimit?: number }) {
  const total = Math.max(0, Number(group.count || 0));
  if (!total) return '0 / 0';
  const meta = resolveGroupPageMeta(group);
  const start = meta.rangeStart;
  const end = meta.rangeEnd;
  return `${start}-${end} / ${total}`;
}

function groupTotalPages(group: { count: number; pageLimit?: number }) {
  return resolveGroupPageMeta(group).totalPages;
}

function groupCurrentPage(group: { count: number; pageOffset?: number; pageLimit?: number }) {
  return resolveGroupPageMeta(group).currentPage;
}

function groupPageInfoText(group: { count: number; pageOffset?: number; pageLimit?: number }) {
  return uiLabel('group_page_info', '第 {current} / {total} 页 · {range}', {
    current: groupCurrentPage(group),
    total: groupTotalPages(group),
    range: groupPageRangeText(group),
  });
}

function pageGroupPrev(group: { key: string; label: string; count: number; domain?: unknown[]; pageOffset?: number; pageLimit?: number }) {
  if (!props.onGroupPageChange) return;
  const limit = resolveGroupPageLimit(group);
  const offset = resolveGroupPageOffset(group);
  const next = Math.max(0, offset - limit);
  props.onGroupPageChange({ key: group.key, label: group.label, count: group.count, domain: group.domain, offset: next, limit });
}

function pageGroupNext(group: { key: string; label: string; count: number; domain?: unknown[]; pageOffset?: number; pageLimit?: number }) {
  if (!props.onGroupPageChange) return;
  const limit = resolveGroupPageLimit(group);
  const offset = resolveGroupPageOffset(group);
  const maxOffset = Math.max(0, Number(group.count || 0) - limit);
  const next = Math.min(maxOffset, offset + limit);
  props.onGroupPageChange({ key: group.key, label: group.label, count: group.count, domain: group.domain, offset: next, limit });
}

function jumpGroupPage(group: { key: string; label: string; count: number; domain?: unknown[]; pageOffset?: number; pageLimit?: number }) {
  if (!props.onGroupPageChange) return;
  const totalPages = groupTotalPages(group);
  const raw = String(groupJumpPageInput.value[group.key] || '').trim();
  const page = Number(raw);
  if (!Number.isFinite(page)) return;
  const normalizedPage = Math.min(Math.max(Math.trunc(page), 1), totalPages);
  const limit = resolveGroupPageLimit(group);
  const offset = (normalizedPage - 1) * limit;
  groupJumpPageInput.value = { ...groupJumpPageInput.value, [group.key]: String(normalizedPage) };
  props.onGroupPageChange({ key: group.key, label: group.label, count: group.count, domain: group.domain, offset, limit });
}

function onGroupJumpInputChange(groupKey: string, event: Event) {
  const value = String((event.target as HTMLInputElement | null)?.value || '');
  groupJumpPageInput.value = { ...groupJumpPageInput.value, [groupKey]: value };
}

watch(
  sortedGroupedRows,
  (rows) => {
    const next: Record<string, string> = {};
    rows.forEach((group) => {
      const key = String(group.key || '').trim();
      if (!key) return;
      const existing = groupJumpPageInput.value[key];
      if (existing && existing.trim()) {
        next[key] = existing;
      } else {
        next[key] = String(groupCurrentPage(group));
      }
    });
    groupJumpPageInput.value = next;
  },
  { immediate: true },
);

const groupSampleLimitOptions = computed(() => {
  const values = Array.isArray(props.listProfile?.grouping?.sample_limits)
    ? props.listProfile?.grouping?.sample_limits || []
    : [];
  const normalized = values
    .map((item) => Number(item))
    .filter((item) => Number.isFinite(item) && item > 0)
    .map((item) => Math.trunc(item));
  return normalized.length ? normalized : [3];
});
const groupDefaultSampleLimit = computed(() => {
  const raw = Number(props.listProfile?.grouping?.default_sample_limit || 0);
  const candidate = Number.isFinite(raw) && raw > 0 ? Math.trunc(raw) : groupSampleLimitOptions.value[0];
  return groupSampleLimitOptions.value.includes(candidate) ? candidate : groupSampleLimitOptions.value[0];
});
const effectiveGroupSampleLimit = computed(() => {
  const raw = Number(props.groupSampleLimit || 0);
  const candidate = Number.isFinite(raw) && raw > 0 ? Math.trunc(raw) : groupDefaultSampleLimit.value;
  return groupSampleLimitOptions.value.includes(candidate) ? candidate : groupDefaultSampleLimit.value;
});

function collapseAllGroups() {
  if (!props.onGroupCollapsedChange) return;
  props.onGroupCollapsedChange(sortedGroupedRows.value.map((item) => item.key));
}

function expandAllGroups() {
  if (!props.onGroupCollapsedChange) return;
  props.onGroupCollapsedChange([]);
}

function handleRow(row: Record<string, unknown>) {
  props.onRowClick(row);
}

function hasActiveTextSelection() {
  return Boolean(window.getSelection?.()?.toString().trim());
}

function isInteractiveTarget(target: EventTarget | null) {
  return Boolean((target as HTMLElement | null)?.closest('button,input,select,textarea,a,[role="button"]'));
}

function handleRowClick(row: Record<string, unknown>, event: MouseEvent) {
  if (event.defaultPrevented || hasActiveTextSelection() || isInteractiveTarget(event.target)) return;
  handleRow(row);
}

function rowId(row: Record<string, unknown>) {
  const value = row?.id;
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value);
    return Number.isNaN(parsed) ? null : parsed;
  }
  return null;
}

const selectedIdSet = computed(() => new Set((props.selectedIds || []).filter((id) => Number.isFinite(id))));
const selectedCount = computed(() => (props.selectedIds || []).length);
const selectionActions = computed(() =>
  Array.isArray(props.selectionActions) ? props.selectionActions : [],
);
const hasSelectionActions = computed(() => selectionActions.value.length > 0);
const selectableRows = computed(() => pageVisibleRows.value.map((row) => rowId(row)).filter((id): id is number => typeof id === 'number'));
const showSelectionColumn = computed(() => hasSelectionActions.value && !!props.onToggleSelection && !!props.onToggleSelectionAll);
const showBatchBar = computed(() => showSelectionColumn.value && (selectedCount.value > 0 || Boolean(props.batchMessage)));
const allSelected = computed(() => {
  const rows = selectableRows.value;
  if (!rows.length) return false;
  return rows.every((id) => selectedIdSet.value.has(id));
});
const listLimit = computed(() => {
  if (observedListLimit.value > 0) return observedListLimit.value;
  const limit = Number(props.listLimit || 40);
  return Number.isFinite(limit) && limit > 0 ? Math.trunc(limit) : 40;
});
const pageLimitOptions = computed(() => [10, 20, 50]);
const listTotal = computed(() => {
  if (props.listTotalCount === null || typeof props.listTotalCount === 'undefined') return null;
  const raw = Number(props.listTotalCount);
  if (!Number.isFinite(raw) || raw < 0) return null;
  return Math.trunc(raw);
});
const listOffset = computed(() => {
  const offset = Number(props.listOffset || 0);
  if (!Number.isFinite(offset) || offset <= 0) return 0;
  return Math.trunc(offset);
});
const totalPages = computed(() => {
  const total = listTotal.value || 0;
  return Math.max(1, Math.ceil(total / listLimit.value));
});
const currentPage = computed(() => Math.min(totalPages.value, Math.floor(listOffset.value / listLimit.value) + 1));
const showPagination = computed(() => listTotal.value !== null && props.status === 'ok' && !showGroupedRows.value);
const groupedRecordTotal = computed(() => {
  if (!showGroupedRows.value) return null;
  const total = sortedGroupedRows.value.reduce((sum, group) => {
    const count = Number(group.count);
    return Number.isFinite(count) && count > 0 ? sum + Math.trunc(count) : sum;
  }, 0);
  return total > 0 ? total : null;
});
const listRecordTotal = computed(() =>
  listTotal.value ?? groupedRecordTotal.value ?? pageVisibleRows.value.length ?? props.records.length,
);
const listRecordCountText = computed(() =>
  uiLabel('footer_record_count', '共 {count} 条', { count: listRecordTotal.value }),
);
const toolbarSubtitle = computed(() => props.subtitle || '');
const canPagePrev = computed(() => listOffset.value > 0);
const canPageNext = computed(() => {
  const total = listTotal.value || 0;
  return listOffset.value + listLimit.value < total;
});
const paginationPageText = computed(() =>
  uiLabel('pagination_page', '第 {current} / {total} 页', {
    current: currentPage.value,
    total: totalPages.value,
  }),
);

function isSelected(row: Record<string, unknown>) {
  const id = rowId(row);
  if (!id) return false;
  return selectedIdSet.value.has(id);
}

function onToggleRow(row: Record<string, unknown>, selected: boolean) {
  const id = rowId(row);
  if (!id || !props.onToggleSelection) return;
  props.onToggleSelection(id, selected);
}

function onToggleAll(selected: boolean) {
  if (!props.onToggleSelectionAll) return;
  props.onToggleSelectionAll(selectableRows.value, selected);
}

function groupSelectableRows(group: { sampleRows?: Array<Record<string, unknown>> }) {
  return (Array.isArray(group.sampleRows) ? group.sampleRows : [])
    .map((row) => rowId(row))
    .filter((id): id is number => typeof id === 'number');
}

function isGroupAllSelected(group: { sampleRows?: Array<Record<string, unknown>> }) {
  const ids = groupSelectableRows(group);
  if (!ids.length) return false;
  return ids.every((id) => selectedIdSet.value.has(id));
}

function onGroupSelectAllChange(group: { sampleRows?: Array<Record<string, unknown>> }, event: Event) {
  if (!props.onToggleSelectionAll) return;
  const selected = Boolean((event.target as HTMLInputElement | null)?.checked);
  props.onToggleSelectionAll(groupSelectableRows(group), selected);
}

function clearSelection() {
  props.onClearSelection?.();
}

function runSelectionAction(key: string) {
  if (!key || selectedCount.value <= 0) return;
  props.onRunSelectionAction?.(key);
}

function emitPageOffset(offset: number) {
  if (!props.onPageChange) return;
  const total = listTotal.value || 0;
  const maxOffset = total > 0 ? Math.floor((total - 1) / listLimit.value) * listLimit.value : 0;
  const normalized = Math.min(Math.max(Math.trunc(offset || 0), 0), maxOffset);
  props.onPageChange(normalized);
}

function pagePrev() {
  emitPageOffset(listOffset.value - listLimit.value);
}

function pageNext() {
  emitPageOffset(listOffset.value + listLimit.value);
}

function onPageJumpInput(event: Event) {
  pageJumpInput.value = String((event.target as HTMLInputElement | null)?.value || '');
}

function jumpPage() {
  const page = Number(pageJumpInput.value || currentPage.value);
  if (!Number.isFinite(page)) return;
  const normalizedPage = Math.min(Math.max(Math.trunc(page), 1), totalPages.value);
  pageJumpInput.value = String(normalizedPage);
  emitPageOffset((normalizedPage - 1) * listLimit.value);
}

function applyPageLimitValue(raw: number) {
  if (!Number.isFinite(raw)) return;
  const normalized = Math.min(Math.max(Math.trunc(raw), 1), 200);
  pageLimitInput.value = String(normalized);
  if (normalized === listLimit.value) return;
  observedListLimit.value = normalized;
  props.onPageLimitChange?.(normalized);
}

function onPageLimitInput(event: Event) {
  pageLimitInput.value = String((event.target as HTMLInputElement | null)?.value || '');
}

function applyPageLimit() {
  applyPageLimitValue(Number(pageLimitInput.value || listLimit.value));
}

function onPageLimitSelectChange(event: Event) {
  applyPageLimitValue(Number((event.target as HTMLSelectElement | null)?.value || 0));
}

function onPlainSearchInput(event: Event) {
  plainSearchDraft.value = String((event.target as HTMLInputElement | null)?.value || '');
}

function onPlainSearchCompositionEnd(event: CompositionEvent) {
  plainSearchComposing.value = false;
  plainSearchDraft.value = String((event.target as HTMLInputElement | null)?.value || '');
}

function submitPlainSearch() {
  if (plainSearchComposing.value) return;
  props.onSearch(plainSearchDraft.value || '');
}

watch(
  currentPage,
  (page) => {
    pageJumpInput.value = String(page);
  },
  { immediate: true },
);

watch(
  listLimit,
  (limit) => {
    pageLimitInput.value = String(limit);
  },
  { immediate: true },
);

watch(
  () => props.searchTerm,
  (value) => {
    if (plainSearchComposing.value) return;
    plainSearchDraft.value = value || '';
  },
  { immediate: true },
);

watch(
  [() => props.records.length, listTotal],
  ([length, totalRaw]) => {
    const total = totalRaw || 0;
    if (length <= 0 || total <= 0) return;
    if (length > observedListLimit.value) {
      observedListLimit.value = length;
      return;
    }
    if (listOffset.value === 0) {
      observedListLimit.value = length;
    }
  },
  { immediate: true },
);

function onSelectAllChange(event: Event) {
  const checked = Boolean((event.target as HTMLInputElement | null)?.checked);
  onToggleAll(checked);
}

function onRowCheckboxChange(row: Record<string, unknown>, event: Event) {
  const checked = Boolean((event.target as HTMLInputElement | null)?.checked);
  onToggleRow(row, checked);
}

const rowPrimary = computed(() => props.listProfile?.row_primary || '');
const rowSecondary = computed(() => props.listProfile?.row_secondary || '');
const showRowNumberColumn = computed(() => props.listProfile?.show_row_number !== false);
const hiddenColumns = computed(() => {
  return (props.listProfile?.hidden_columns || []).reduce<Record<string, true>>((acc, col) => {
    acc[col] = true;
    return acc;
  }, {});
});
const preferredColumns = computed(() => props.listProfile?.columns || []);
const columnLabels = computed(() => props.listProfile?.column_labels || {});
const contractColumnLabels = computed(() => props.columnLabels || {});

function applyColumnOrder(source: string[], order: string[]) {
  const sourceSet = new Set(source);
  const ordered = order
    .map((item) => String(item || '').trim())
    .filter((name, index, rows) => Boolean(name) && sourceSet.has(name) && rows.indexOf(name) === index);
  return [...ordered, ...source.filter((name) => !ordered.includes(name))];
}

const orderedColumnNames = computed(() => {
  const source = preferredColumns.value.length ? preferredColumns.value : props.columns;
  return applyColumnOrder(source, Array.isArray(props.columnOrder) ? props.columnOrder : []);
});

const columnChoices = computed<ColumnOption[]>(() => {
  if (Array.isArray(props.columnOptions) && props.columnOptions.length) {
    const byName = props.columnOptions.reduce<Record<string, ColumnOption>>((acc, column) => {
      acc[column.name] = column;
      return acc;
    }, {});
    return applyColumnOrder(props.columnOptions.map((column) => column.name), Array.isArray(props.columnOrder) ? props.columnOrder : [])
      .map((name) => byName[name])
      .filter((column): column is ColumnOption => Boolean(column));
  }
  return orderedColumnNames.value.map((name) => ({
    name,
    label: columnLabels.value[name] || contractColumnLabels.value[name] || name,
    defaultVisible: !hiddenColumns.value[name],
  }));
});
const defaultVisibleColumnMap = computed<Record<string, boolean>>(() =>
  columnChoices.value.reduce<Record<string, boolean>>((acc, column) => {
    acc[column.name] = column.defaultVisible !== false && !hiddenColumns.value[column.name];
    return acc;
  }, {}),
);
const displayedColumns = computed(() => {
  const source = columnChoices.value.length
    ? columnChoices.value.map((column) => column.name)
    : orderedColumnNames.value;
  const filtered = source.filter((col) => {
    const visibility = props.columnVisibility || {};
    if (Object.prototype.hasOwnProperty.call(visibility, col)) {
      return visibility[col] === true;
    }
    return defaultVisibleColumnMap.value[col] !== false;
  });
  return filtered.length ? filtered : source.slice(0, 1);
});
const tableMinWidthPx = computed(() => {
  const fixedWidth = (showSelectionColumn.value ? 44 : 0)
    + (showRowNumberColumn.value ? 64 : 0)
    + (columnChoices.value.length ? 72 : 0);
  const dynamicWidth = displayedColumns.value.reduce((total, field) => {
    const explicit = effectiveColumnWidth(field);
    if (explicit) return total + explicit;
    if (isNameLikeColumn(field)) return total + 220;
    if (isLongTextColumn(field)) return total + 180;
    if (isNumericColumn(field)) return total + 120;
    return total + 128;
  }, 0);
  return Math.max(0, fixedWidth + dynamicWidth);
});
const tableWidthStyle = computed(() => ({
  minWidth: `max(100%, ${tableMinWidthPx.value}px)`,
}));

function firstSortClause(value: string) {
  return String(value || '').split(',')[0]?.trim() || '';
}

function sortField(value: string) {
  return firstSortClause(value).split(/\s+/)[0] || '';
}

function sortDirection(value: string) {
  const direction = firstSortClause(value).split(/\s+/)[1] || 'asc';
  return direction.toLowerCase() === 'desc' ? 'desc' : 'asc';
}

function isSortedColumn(col: string) {
  return sortField(props.sortValue || '') === col;
}

function columnSortIndicator(col: string) {
  if (!isSortedColumn(col)) return '';
  return sortDirection(props.sortValue || '') === 'desc' ? '▼' : '▲';
}

function columnAriaSort(col: string) {
  if (!isColumnSortable(col)) return undefined;
  if (!isSortedColumn(col)) return 'none';
  return sortDirection(props.sortValue || '') === 'desc' ? 'descending' : 'ascending';
}

function columnSortTitle(col: string) {
  const label = columnLabel(col);
  if (!isColumnSortable(col)) {
    return uiLabel('sort_column_disabled', '{column} 不支持排序', { column: label });
  }
  if (isSortedColumn(col) && sortDirection(props.sortValue || '') === 'asc') {
    return uiLabel('sort_column_desc', '按 {column} 降序', { column: label });
  }
  return uiLabel('sort_column_asc', '按 {column} 升序', { column: label });
}

function toggleColumnSort(col: string) {
  if (!isColumnSortable(col)) return;
  const currentDirection = isSortedColumn(col) ? sortDirection(props.sortValue || '') : '';
  const nextDirection = currentDirection === 'asc' ? 'desc' : 'asc';
  props.onSort(`${col} ${nextDirection}`);
}

function onColumnDragStart(col: string, event: DragEvent) {
  if (resizingColumn.value) {
    event.preventDefault();
    return;
  }
  if (!displayedColumns.value.includes(col)) return;
  draggingColumn.value = col;
  event.dataTransfer?.setData('text/plain', col);
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move';
}

function onColumnDragOver(col: string, event: DragEvent) {
  if (!draggingColumn.value || draggingColumn.value === col) return;
  event.preventDefault();
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move';
}

function onColumnDrop(target: string, event: DragEvent) {
  event.preventDefault();
  const source = draggingColumn.value || event.dataTransfer?.getData('text/plain') || '';
  draggingColumn.value = '';
  if (!source || source === target) return;
  const base = columnChoices.value.map((column) => column.name);
  const sourceIndex = base.indexOf(source);
  const targetIndex = base.indexOf(target);
  if (sourceIndex < 0 || targetIndex < 0) return;
  const next = [...base];
  const [moved] = next.splice(sourceIndex, 1);
  next.splice(targetIndex, 0, moved);
  emit('column-order-change', { columnOrder: next });
}

function onColumnDragEnd() {
  draggingColumn.value = '';
}

function normalizeColumnWidth(value: unknown) {
  const parsed = Number(value || 0);
  if (!Number.isFinite(parsed) || parsed <= 0) return 0;
  return Math.min(Math.max(Math.trunc(parsed), 80), 640);
}

watch(
  () => props.columnWidths,
  (value) => {
    draftColumnWidths.value = Object.entries(value || {}).reduce<Record<string, number>>((acc, [name, width]) => {
      const normalizedName = String(name || '').trim();
      const normalizedWidth = normalizeColumnWidth(width);
      if (normalizedName && normalizedWidth) acc[normalizedName] = normalizedWidth;
      return acc;
    }, {});
  },
  { immediate: true },
);

function effectiveColumnWidth(field: string) {
  return normalizeColumnWidth(draftColumnWidths.value[field] || props.columnWidths?.[field]);
}

function columnWidthStyle(field: string) {
  const width = effectiveColumnWidth(field);
  if (!width) return {};
  return { width: `${width}px`, minWidth: `${width}px`, maxWidth: `${width}px` };
}

function isLongTextColumn(field: string) {
  if (isNumericColumn(field)) return false;
  const name = String(field || '').toLowerCase();
  const label = columnLabel(field);
  const type = String(columnOption(field)?.type || '').trim();
  return [
    'name',
    'display_name',
    'title',
    'subject',
    'description',
  ].includes(name)
    || ['char', 'text', 'html', 'many2one', 'reference'].includes(type)
    || /名称|标题|摘要|说明|备注|开户行|账号|来源/.test(label);
}

function isNameLikeColumn(field: string) {
  const name = String(field || '').toLowerCase();
  const label = columnLabel(field);
  return ['name', 'display_name', 'title', 'subject'].includes(name) || /名称|标题/.test(label);
}

function columnDensityClass(field: string) {
  return {
    'column-long-text': isLongTextColumn(field),
    'column-name-text': isNameLikeColumn(field),
    'column-numeric': isNumericColumn(field),
  };
}

function startColumnResize(field: string, event: MouseEvent) {
  const header = (event.currentTarget as HTMLElement | null)?.closest('th');
  resizingColumn.value = field;
  resizeStartX.value = event.clientX;
  resizeStartWidth.value = effectiveColumnWidth(field) || Math.trunc(header?.getBoundingClientRect().width || 160);
  window.addEventListener('mousemove', onColumnResizeMove);
  window.addEventListener('mouseup', stopColumnResize, { once: true });
}

function onColumnResizeMove(event: MouseEvent) {
  const field = resizingColumn.value;
  if (!field) return;
  const nextWidth = normalizeColumnWidth(resizeStartWidth.value + event.clientX - resizeStartX.value);
  if (!nextWidth) return;
  draftColumnWidths.value = { ...draftColumnWidths.value, [field]: nextWidth };
}

function stopColumnResize() {
  const field = resizingColumn.value;
  window.removeEventListener('mousemove', onColumnResizeMove);
  resizingColumn.value = '';
  if (!field) return;
  emit('column-widths-change', { columnWidths: { ...draftColumnWidths.value } });
}

function columnLabel(col: string) {
  const option = columnOption(col);
  return option?.label || columnLabels.value[col] || contractColumnLabels.value[col] || col;
}

function columnChoiceLabel(column: ColumnOption) {
  return column.label || columnLabel(column.name);
}

function columnOption(field: string) {
  return columnChoices.value.find((column) => column.name === field) || null;
}

function isColumnSortable(field: string) {
  return columnOption(field)?.sortable !== false;
}

function isColumnVisible(name: string) {
  const visibility = props.columnVisibility || {};
  if (Object.prototype.hasOwnProperty.call(visibility, name)) {
    return visibility[name] === true;
  }
  return defaultVisibleColumnMap.value[name] !== false;
}

function isLastVisibleColumn(name: string) {
  return isColumnVisible(name) && displayedColumns.value.length <= 1;
}

function onColumnVisibilityChange(name: string, event: Event) {
  const checked = Boolean((event.target as HTMLInputElement | null)?.checked);
  if (!checked && isLastVisibleColumn(name)) return;
  emit('column-visibility-change', {
    visibility: {
      ...(props.columnVisibility || {}),
      [name]: checked,
    },
  });
}

function resetColumnVisibility() {
  emit('column-visibility-change', { visibility: {} });
}

const pageVisibleRows = computed(() => {
  if (!showGroupedRows.value) return props.records;
  return sortedGroupedRows.value.flatMap((group) => {
    if (isGroupCollapsed(group.key)) return [];
    return Array.isArray(group.sampleRows) ? group.sampleRows : [];
  });
});

function isNumericColumn(field: string) {
  const type = String(columnOption(field)?.type || '').trim();
  return type === 'integer' || type === 'float' || type === 'monetary';
}

function isNumericDisplayColumn(field: string) {
  if (isNumericColumn(field)) return true;
  const label = columnLabel(field).trim();
  if (!label) return false;
  if (/编号|单号|号码|账号|代码|日期|时间|状态|是否|项目|名称|单位|人员|录入人|附件|备注|类型/.test(label)) {
    return false;
  }
  return /金额|税额|总额|余额|收入|支出|价税|含税|不含税|附加税|抵扣|付款|收款|借款|还款|未还款|利息|保证金|合同价|控制价|单价|数量|税率|累计|本期|已退|未退|张数|份数|天数/.test(label);
}

function numericCellValue(value: unknown) {
  const raw = normalizeCellRawValue(value);
  if (typeof raw === 'number' && Number.isFinite(raw)) return raw;
  if (typeof raw !== 'string') return null;
  const normalized = raw.replace(/,/g, '').trim();
  if (!normalized) return null;
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatNumericCellValue(field: string, value: unknown) {
  if (!isNumericColumn(field)) return '';
  const numeric = numericCellValue(value);
  if (numeric === null) return '';
  const type = String(columnOption(field)?.type || '').trim();
  return numeric.toLocaleString('zh-CN', {
    maximumFractionDigits: type === 'integer' ? 0 : 2,
    minimumFractionDigits: type === 'integer' ? 0 : 2,
  });
}

function formatFooterNumber(value: number, field: string) {
  const type = String(columnOption(field)?.type || '').trim();
  return value.toLocaleString('zh-CN', {
    maximumFractionDigits: type === 'integer' ? 0 : 2,
    minimumFractionDigits: type === 'integer' ? 0 : 2,
  });
}

const pageFooterStats = computed(() =>
  displayedColumns.value
    .filter((field) => isNumericColumn(field))
    .map((field) => {
      const values = pageVisibleRows.value
        .map((row) => numericCellValue(row[field]))
        .filter((value): value is number => typeof value === 'number');
      return {
        name: field,
        label: uiLabel('page_footer_summary', '{column} 汇总', { column: columnLabel(field) }),
        count: values.length,
        sumText: formatFooterNumber(values.reduce((total, value) => total + value, 0), field),
      };
    })
    .filter((item) => item.count > 0),
);

const pageFooterStatsMap = computed(() =>
  pageFooterStats.value.reduce<Record<string, { sumText: string; count: number }>>((acc, item) => {
    acc[item.name] = { sumText: item.sumText, count: item.count };
    return acc;
  }, {}),
);

function totalAggregateValue(field: string) {
  const aggregate = props.listAggregates?.[field] || {};
  const value = aggregate.sum;
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function footerCellText(field: string, scope: 'page' | 'total', rowCount: number) {
  void rowCount;
  if (!isNumericColumn(field)) return '';
  if (scope === 'page') {
    return pageFooterStatsMap.value[field]?.sumText || '--';
  }
  const value = totalAggregateValue(field);
  return value === null ? '--' : formatFooterNumber(value, field);
}

function rowsNumericSum(rows: Array<Record<string, unknown>>, field: string) {
  const values = rows
    .map((row) => numericCellValue(row[field]))
    .filter((value): value is number => typeof value === 'number');
  if (!values.length) return null;
  return values.reduce((total, value) => total + value, 0);
}

function groupAggregateValue(group: { aggregates?: Record<string, Record<string, unknown>> }, field: string) {
  const aggregate = group.aggregates?.[field] || {};
  const value = aggregate.sum;
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function groupFooterCellText(
  field: string,
  group: { sampleRows: Array<Record<string, unknown>>; aggregates?: Record<string, Record<string, unknown>> },
  scope: 'page' | 'total',
) {
  if (!isNumericColumn(field)) return '';
  if (scope === 'page') {
    const value = rowsNumericSum(group.sampleRows || [], field);
    return value === null ? '--' : formatFooterNumber(value, field);
  }
  const value = groupAggregateValue(group, field);
  return value === null ? '--' : formatFooterNumber(value, field);
}

function footerRowLabel(scope: 'page' | 'total', rowCount: number) {
  void rowCount;
  return scope === 'page'
    ? uiLabel('page_footer_current_total', '当页总计')
    : uiLabel('page_footer_total', '总计');
}

function handleColumnPickerPointerDown(event: PointerEvent) {
  const root = columnPickerRoot.value;
  if (!root || root.contains(event.target as Node)) return;
  columnPickerOpen.value = false;
}

onMounted(() => {
  document.addEventListener('pointerdown', handleColumnPickerPointerDown);
});

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleColumnPickerPointerDown);
  window.removeEventListener('mousemove', onColumnResizeMove);
});

</script>

<style scoped>
.page {
  display: grid;
  gap: var(--sc-product-workspace-stack-gap);
  min-width: 0;
}

.list-toolbar {
  position: relative;
  z-index: 35;
  display: grid;
  grid-template-columns: minmax(180px, 240px) minmax(0, 1fr) max-content;
  align-items: center;
  gap: 10px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
  padding: 8px 10px;
  min-height: 52px;
  box-shadow: 0 8px 18px var(--sc-app-shadow);
}

.list-title {
  min-width: 0;
  justify-self: start;
}

.list-title h2 {
  margin: 0;
  color: var(--sc-app-text-primary);
  font-size: 18px;
  font-weight: 700;
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.list-title p {
  margin: 2px 0 0;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.list-header-toolbar {
  display: flex;
  justify-content: flex-start;
  min-width: 0;
  width: 100%;
}

.list-header-toolbar :deep(.action-toolbar) {
  grid-template-columns: max-content minmax(280px, 460px) minmax(max-content, 1fr);
  justify-content: stretch;
  width: 100%;
  max-width: none;
  border: 0;
  box-shadow: none;
  padding: 0;
}

.list-header-toolbar :deep(.native-search) {
  width: clamp(280px, 32vw, 460px);
}

.list-empty-state {
  display: grid;
  gap: 14px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
  padding: 20px;
  box-shadow: 0 12px 28px var(--sc-app-shadow);
}

.list-empty-copy {
  display: grid;
  gap: 6px;
}

.list-empty-copy h2,
.list-empty-copy p {
  margin: 0;
}

.list-empty-copy h2 {
  color: var(--sc-app-text-primary);
  font-size: 18px;
  line-height: 1.3;
}

.list-empty-copy p {
  color: var(--sc-app-text-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.list-empty-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.list-empty-primary,
.list-empty-secondary {
  min-height: 34px;
  border-radius: 8px;
  padding: 7px 12px;
  font-size: 13px;
  cursor: pointer;
}

.list-empty-primary {
  border: 1px solid var(--sc-semantic-surface-interactive);
  background: var(--sc-semantic-surface-interactive);
  color: var(--sc-semantic-text-on-interactive);
}

.list-empty-secondary {
  border: 1px solid var(--sc-app-border-strong);
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
}

.list-empty-primary:disabled,
.list-empty-secondary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.table {
  width: 100%;
  max-width: 100%;
  max-height: max(420px, calc(100vh - 210px));
  overflow-x: auto;
  overflow-y: auto;
  background: var(--sc-app-panel);
  border-radius: 8px;
  box-shadow: 0 20px 40px var(--sc-app-shadow);
  overscroll-behavior: contain;
  touch-action: pan-x pan-y;
}

.list-plain-search {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  flex: 0 1 360px;
  min-width: min(240px, 100%);
}

.list-plain-search input {
  min-width: 0;
  width: 100%;
  height: 30px;
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 8px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  padding: 4px 8px;
  font-size: 13px;
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.summary-card {
  border: 1px solid var(--sc-app-border);
  border-radius: 10px;
  background: var(--sc-app-panel);
  padding: 10px;
}

.summary-label {
  margin: 0;
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}

.summary-value {
  margin: 6px 0 0;
  font-size: 20px;
  font-weight: 700;
}

.summary-card.tone-danger { background: var(--sc-app-danger-bg); border-color: var(--sc-app-danger-border); color: var(--sc-app-danger-text); }
.summary-card.tone-warning { background: var(--sc-app-warning-bg); border-color: var(--sc-app-warning-border); color: var(--sc-app-warning-text); }
.summary-card.tone-success { background: var(--sc-app-success-bg); border-color: var(--sc-app-success-border); color: var(--sc-app-success-text); }
.summary-card.tone-info { background: var(--sc-app-info-bg); border-color: var(--sc-app-info-border); color: var(--sc-app-info-text); }

.grouped-table {
  display: grid;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid var(--sc-app-border);
  background: var(--sc-app-muted-bg);
}

.grouped-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.grouped-toolbar span {
  color: var(--sc-app-text-primary);
  font-size: 13px;
  font-weight: 700;
}

.grouped-toolbar-title {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  min-width: 0;
}

.grouped-toolbar-title .group-window-info {
  color: var(--sc-semantic-text-muted);
  font-size: 12px;
  font-weight: 600;
}

.grouped-toolbar-actions {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.grouped-toolbar-actions select {
  border: 1px solid var(--sc-app-info-border);
  border-radius: 999px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-info-text);
  padding: 2px 10px;
  font-size: 12px;
}

.grouped-sort-btn {
  border: 1px solid var(--sc-app-info-border);
  border-radius: 999px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-info-text);
  padding: 2px 10px;
  font-size: 12px;
  cursor: pointer;
}

.group-block {
  border: 1px solid var(--sc-app-info-border);
  border-radius: 10px;
  background: var(--sc-app-panel);
  overflow: visible;
}

.group-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 10px;
  border-bottom: 1px solid var(--sc-app-info-border);
}

.group-toggle,
.group-open-btn {
  border: 1px solid var(--sc-app-info-border);
  border-radius: 999px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-info-text);
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
}

.group-head p {
  flex: 1 1 180px;
  min-width: 0;
  margin: 0;
  color: var(--sc-app-text-primary);
  font-size: 13px;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.group-head span {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.group-page {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.group-page-btn {
  border: 1px solid var(--sc-app-info-border);
  border-radius: 8px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-info-text);
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
}

.group-page-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.group-page-input {
  width: 56px;
  border: 1px solid var(--sc-app-info-border);
  border-radius: 8px;
  padding: 2px 6px;
  font-size: 12px;
  color: var(--sc-app-text-primary);
}

.batch-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  background: var(--sc-app-muted-bg);
  border: 1px solid var(--sc-app-border);
  border-radius: 10px;
  padding: 10px 12px;
}

.batch-bar button {
  border: 1px solid var(--sc-app-border-strong);
  background: var(--sc-app-input-bg);
  border-radius: 8px;
  padding: 6px 10px;
  cursor: pointer;
}

.batch-bar button.ghost {
  color: var(--sc-app-text-secondary);
}

.batch-message {
  margin-left: 0;
  font-size: 13px;
  color: var(--sc-app-success-text);
  overflow-wrap: anywhere;
}

.list-inline-feedback {
  margin: 0;
  border: 1px solid var(--sc-app-border);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 13px;
  overflow-wrap: anywhere;
}

.list-inline-feedback.is-error {
  border-color: var(--sc-app-danger-border);
  background: var(--sc-app-danger-bg);
  color: var(--sc-app-danger-text);
}

.batch-note {
  font-size: 12px;
  color: var(--sc-app-text-secondary);
}

.batch-details {
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
  padding: 8px 10px;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.batch-details p {
  margin: 3px 0;
}

.batch-detail-action {
  margin-left: 8px;
  border: 1px solid var(--sc-app-info-border);
  border-radius: 6px;
  background: var(--sc-app-info-bg);
  color: var(--sc-app-info-text);
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
}

.batch-download {
  margin-top: 8px;
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 6px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  padding: 6px 10px;
  cursor: pointer;
}

.batch-load-more {
  margin-top: 8px;
  margin-right: 8px;
  border: 1px solid var(--sc-app-info-border);
  border-radius: 6px;
  background: var(--sc-app-info-bg);
  color: var(--sc-app-info-text);
  padding: 6px 10px;
  cursor: pointer;
}

.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  border: 1px solid var(--sc-app-border);
  border-radius: 10px;
  background: var(--sc-app-panel);
  padding: 10px 12px;
  color: var(--sc-app-text-secondary);
  font-size: 13px;
}

.pagination-actions {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px;
}

.pagination-footer {
  display: flex;
  justify-content: flex-end;
  position: sticky;
  bottom: 0;
  z-index: 24;
  background: var(--sc-app-bg);
  padding-top: 6px;
}

.pagination-footer--count-only {
  position: static;
}

.pagination-actions--bottom {
  justify-content: flex-end;
  flex-wrap: nowrap;
  color: var(--sc-app-text-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.pagination-total {
  color: var(--sc-app-text-secondary);
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.pagination-size-control {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.pagination-size-label {
  color: var(--sc-app-text-secondary);
  font-size: 12px;
}

.cell-column-picker {
  position: relative;
  width: 1%;
  min-width: 56px;
  text-align: right;
  white-space: nowrap;
  vertical-align: top;
}

.column-picker-btn {
  border: 1px solid var(--sc-app-info-border);
  border-radius: 6px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-info-text);
  padding: 3px 8px;
  font-size: 12px;
  line-height: 18px;
  cursor: pointer;
}

.column-picker-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.column-save-badge {
  display: inline-flex;
  margin-left: 4px;
  border: 1px solid var(--sc-app-success-border);
  border-radius: 6px;
  background: var(--sc-app-success-bg);
  color: var(--sc-app-success-text);
  padding: 2px 6px;
  font-size: 12px;
  line-height: 16px;
  white-space: nowrap;
}

.column-save-badge.is-saving,
.column-save-message.is-saving {
  border-color: var(--sc-app-info-border);
  background: var(--sc-app-info-bg);
  color: var(--sc-app-info-text);
}

.column-save-badge.is-error,
.column-save-message.is-error {
  border-color: var(--sc-app-danger-border);
  background: var(--sc-app-danger-bg);
  color: var(--sc-app-danger-text);
}

.column-picker-menu {
  position: absolute;
  z-index: 20;
  right: 0;
  top: calc(100% + 6px);
  display: grid;
  gap: 4px;
  min-width: 190px;
  max-height: 320px;
  overflow: auto;
  border: 1px solid var(--sc-app-info-border);
  border-radius: 8px;
  background: var(--sc-app-panel);
  padding: 8px;
  box-shadow: 0 16px 32px var(--sc-app-shadow);
}

.column-choice {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 28px;
  color: var(--sc-app-text-primary);
  font-size: 13px;
  white-space: nowrap;
}

.column-reset {
  margin-top: 4px;
  border: 1px solid var(--sc-app-info-border);
  border-radius: 8px;
  background: var(--sc-app-muted-bg);
  color: var(--sc-app-info-text);
  padding: 5px 8px;
  cursor: pointer;
}

.column-save-message {
  margin: 2px 0 0;
  border: 1px solid var(--sc-app-success-border);
  border-radius: 6px;
  background: var(--sc-app-success-bg);
  color: var(--sc-app-success-text);
  padding: 5px 8px;
  font-size: 12px;
  text-align: left;
}

.pagination-btn {
  border: 1px solid var(--sc-app-info-border);
  border-radius: 6px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-info-text);
  padding: 3px 7px;
  font-size: 12px;
  line-height: 18px;
  cursor: pointer;
}

.pagination-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.pagination-input {
  width: 46px;
  border: 1px solid var(--sc-app-info-border);
  border-radius: 6px;
  padding: 3px 6px;
  color: var(--sc-app-text-primary);
  font-size: 12px;
  line-height: 18px;
}

.pagination-input--size {
  width: 64px;
  padding-right: 28px;
}

.pagination-size-combo {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.pagination-size-select {
  position: absolute;
  top: 1px;
  right: 1px;
  bottom: 1px;
  width: 26px;
  border: 0;
  border-left: 1px solid var(--sc-app-info-border);
  border-radius: 0 5px 5px 0;
  background: var(--sc-app-info-bg);
  font-size: 0;
  color: var(--sc-app-info-text);
  cursor: pointer;
}

.pagination-size-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.pagination-size-select option {
  font-size: 12px;
  color: var(--sc-app-text-primary);
}

@media (max-width: 900px) {
  .list-toolbar {
    grid-template-columns: 1fr;
    align-items: flex-start;
  }

  .pagination-bar {
    align-items: flex-start;
    flex-direction: column;
  }

  .list-header-toolbar,
  .list-header-toolbar :deep(.native-search) {
    width: 100%;
  }

  .pagination-actions {
    flex-wrap: wrap;
  }

  .pagination-actions--bottom {
    justify-content: flex-start;
    white-space: normal;
  }

  .list-plain-search {
    width: 100%;
    flex: 1 1 auto;
  }
}

table {
  width: max-content;
  min-width: 100%;
  table-layout: auto;
  border-collapse: collapse;
}

.col-row-number {
  width: 52px;
}

.col-select {
  width: 44px;
}

.col-column-picker {
  width: 72px;
}

th,
td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--sc-app-border);
  text-align: left;
  font-size: 13px;
  vertical-align: top;
  min-width: 72px;
  overflow-wrap: anywhere;
}

tbody td {
  user-select: text;
  cursor: text;
}

.cell-select {
  width: 44px;
  min-width: 44px;
  padding-right: 4px;
}

.cell-row-number {
  box-sizing: border-box;
  width: 52px;
  min-width: 52px;
  padding-right: 4px;
  padding-left: 4px;
  color: var(--sc-semantic-text-muted);
  font-variant-numeric: tabular-nums;
  text-align: center;
  white-space: nowrap;
}

.column-long-text {
  max-width: 180px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  overflow-wrap: normal;
}

.column-name-text {
  max-width: 220px;
}

.column-long-text > *,
.column-long-text .column-sort-btn,
.column-long-text .column-drag-handle,
.column-long-text .primary,
.column-long-text .secondary {
  min-width: 0;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  overflow-wrap: normal;
}

.column-numeric {
  min-width: 92px;
  text-align: right;
}

thead {
  position: sticky;
  top: 0;
  z-index: 20;
}

thead th {
  position: sticky;
  top: 0;
  background: var(--sc-app-panel);
  z-index: 20;
}

tfoot th,
tfoot td {
  background: var(--sc-app-muted-bg);
  border-top: 1px solid var(--sc-app-border-strong);
  color: var(--sc-app-text-primary);
  font-size: 12px;
  font-weight: 700;
  line-height: 1.35;
}

tfoot tr:nth-child(2) th,
tfoot tr:nth-child(2) td {
  background: var(--sc-app-info-bg);
}

.footer-row-label {
  color: var(--sc-app-text-primary);
  font-size: 11px;
  line-height: 1.15;
  min-width: 52px;
  width: 52px;
  max-width: 52px;
  white-space: normal;
  overflow-wrap: anywhere;
}

.footer-number {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  overflow-wrap: normal;
}

.footer-number-value {
  display: block;
  width: 100%;
  min-width: 0;
  text-align: right;
}

.cell-sortable {
  position: relative;
  cursor: pointer;
  user-select: none;
  padding: 0;
  transition: background 120ms ease, box-shadow 120ms ease;
}

.cell-sortable.is-dragging {
  opacity: 0.55;
}

.cell-sortable:hover,
.cell-sortable:focus-visible {
  background: var(--sc-app-hover-bg);
}

.cell-sortable:focus-visible {
  outline: none;
  box-shadow: inset 0 0 0 2px var(--sc-app-info-text);
}

.cell-sortable.is-sort-disabled {
  cursor: default;
}

.cell-sortable.is-sort-disabled:hover,
.cell-sortable.is-sort-disabled:focus-visible {
  background: var(--sc-app-panel);
  box-shadow: none;
}

.cell-sortable.is-sort-disabled .column-sort-btn {
  color: var(--sc-app-text-secondary);
  cursor: default;
}

.column-drag-handle {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 6;
  width: 22px;
  height: 100%;
  border: 0;
  background: transparent;
  padding: 0;
  cursor: grab;
}

.column-drag-handle:active {
  cursor: grabbing;
}

.column-drag-handle::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 9px;
  width: 3px;
  height: 14px;
  border-radius: 999px;
  background:
    radial-gradient(circle, var(--sc-app-text-secondary) 1.2px, transparent 1.4px) 0 0 / 3px 5px repeat-y;
  opacity: 0.45;
  transform: translateY(-50%);
}

.column-drag-handle:hover::before,
.column-drag-handle:focus-visible::before,
.cell-sortable.is-dragging .column-drag-handle::before {
  background:
    radial-gradient(circle, var(--sc-app-info-text) 1.2px, transparent 1.4px) 0 0 / 3px 5px repeat-y;
  opacity: 1;
}

.column-drag-handle:focus-visible {
  outline: 2px solid var(--sc-app-info-text);
  outline-offset: -3px;
}

.column-sort-btn {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  width: 100%;
  min-height: 36px;
  max-width: calc(100% - 12px);
  border: 0;
  background: transparent;
  color: var(--sc-app-text-primary);
  padding: 8px 8px 8px 28px;
  font: inherit;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
  white-space: normal;
  overflow-wrap: anywhere;
}

.column-resize-handle {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 5;
  width: 12px;
  height: 100%;
  border: 0;
  background: transparent;
  padding: 0;
  cursor: col-resize;
}

.column-resize-handle::after {
  content: "";
  position: absolute;
  top: 10px;
  right: 5px;
  width: 1px;
  height: calc(100% - 20px);
  background: transparent;
}

.column-resize-handle:hover::after,
.cell-sortable.is-dragging .column-resize-handle::after {
  background: var(--sc-app-info-text);
}

.cell-sortable:hover .column-sort-btn,
.cell-sortable:focus-visible .column-sort-btn,
.column-sort-btn:hover {
  color: var(--sc-app-info-text);
}

.cell-sortable.is-sort-disabled:hover .column-sort-btn,
.cell-sortable.is-sort-disabled:focus-visible .column-sort-btn,
.cell-sortable.is-sort-disabled .column-sort-btn:hover {
  color: var(--sc-app-text-secondary);
}

.sort-indicator {
  width: 12px;
  min-width: 12px;
  color: var(--sc-app-info-text);
  font-size: 11px;
  line-height: 1;
}

tr:hover {
  background: var(--sc-app-hover-bg);
  cursor: pointer;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 12px;
  border: 1px solid var(--sc-app-border);
  white-space: normal;
  overflow-wrap: anywhere;
}

.status-badge.tone-success { background: var(--sc-app-success-bg); color: var(--sc-app-success-text); border-color: var(--sc-app-success-border); }
.status-badge.tone-warning { background: var(--sc-app-warning-bg); color: var(--sc-app-warning-text); border-color: var(--sc-app-warning-border); }
.status-badge.tone-danger { background: var(--sc-app-danger-bg); color: var(--sc-app-danger-text); border-color: var(--sc-app-danger-border); }
.status-badge.tone-info { background: var(--sc-app-info-bg); color: var(--sc-app-info-text); border-color: var(--sc-app-info-border); }
.status-badge.tone-neutral { background: var(--sc-app-subtle-bg); color: var(--sc-app-text-primary); border-color: var(--sc-app-border); }

.attachment-links {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 4px 8px;
  max-width: 100%;
}

.attachment-links a {
  color: var(--sc-app-accent, #2563eb);
  overflow-wrap: anywhere;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.attachment-count-link {
  border: 0;
  background: transparent;
  color: var(--sc-app-accent, #2563eb);
  cursor: pointer;
  font: inherit;
  padding: 0;
  text-align: left;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.favorite-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-width: 30px;
  height: 28px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: var(--sc-app-text-secondary);
  padding: 0 6px;
  font-size: 17px;
  line-height: 1;
  cursor: pointer;
}

.favorite-toggle.active {
  border-color: var(--sc-app-warning-border);
  background: var(--sc-app-warning-bg);
  color: var(--sc-app-warning-text);
}

.favorite-toggle:not(:disabled):hover {
  border-color: var(--sc-app-border);
  background: var(--sc-app-hover-bg);
  color: var(--sc-app-text-secondary);
}

.favorite-toggle.active:not(:disabled):hover {
  border-color: var(--sc-app-warning-border);
  background: var(--sc-app-warning-bg);
  color: var(--sc-app-warning-text);
}

.favorite-star {
  width: 16px;
  text-align: center;
}

.favorite-label {
  color: var(--sc-app-warning-text);
  font-size: 12px;
  line-height: 16px;
}

.favorite-toggle:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.flat-table .cell-select,
.group-table .cell-select {
  position: sticky;
  left: 0;
  background: var(--sc-app-panel);
  z-index: 14;
}

.flat-table .cell-row-number,
.group-table .cell-row-number {
  position: sticky;
  left: 0;
  background: var(--sc-app-panel);
  z-index: 13;
}

.flat-table.has-selection-column .cell-row-number,
.group-table.has-selection-column .cell-row-number {
  left: 44px;
}

.flat-table thead .cell-select,
.group-table thead .cell-select {
  z-index: 26;
}

.flat-table thead .cell-row-number,
.group-table thead .cell-row-number {
  z-index: 25;
}

.flat-table tfoot .cell-select,
.group-table tfoot .cell-select {
  background: var(--sc-app-muted-bg);
  z-index: 15;
}

.flat-table tfoot .cell-row-number,
.group-table tfoot .cell-row-number {
  background: var(--sc-app-muted-bg);
  z-index: 14;
}

.flat-table tfoot tr:nth-child(2) .cell-select,
.flat-table tfoot tr:nth-child(2) .cell-row-number,
.group-table tfoot tr:nth-child(2) .cell-select,
.group-table tfoot tr:nth-child(2) .cell-row-number {
  background: var(--sc-app-info-bg);
}

.flat-table tbody tr.row-tone-danger td,
.group-table tbody tr.row-tone-danger td,
.flat-table tbody tr.row-tone-danger .cell-select,
.flat-table tbody tr.row-tone-danger .cell-row-number,
.group-table tbody tr.row-tone-danger .cell-select,
.group-table tbody tr.row-tone-danger .cell-row-number {
  background: var(--sc-app-danger-bg);
  color: var(--sc-app-danger-text);
}

.flat-table tbody tr.row-tone-danger:hover td,
.group-table tbody tr.row-tone-danger:hover td,
.flat-table tbody tr.row-tone-danger:hover .cell-select,
.flat-table tbody tr.row-tone-danger:hover .cell-row-number,
.group-table tbody tr.row-tone-danger:hover .cell-select,
.group-table tbody tr.row-tone-danger:hover .cell-row-number {
  background: var(--sc-app-danger-bg);
  color: var(--sc-app-danger-text);
}

tbody tr:hover .cell-select,
tbody tr:hover .cell-row-number {
  background: var(--sc-app-hover-bg);
}

</style>
