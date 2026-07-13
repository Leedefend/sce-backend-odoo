<template>
  <section class="field-chip-editor">
    <header>
      <strong>{{ title }}</strong>
      <span>{{ names.length }} 项</span>
    </header>
    <p class="field-chip-action-hint">拖动手柄或使用上移、下移调整顺序，移除会从当前配置中取消显示。</p>
    <label v-if="showGraphType" class="inline-select">
      图表类型
      <select :value="graphType" @change="$emit('update:graphType', ($event.target as HTMLSelectElement).value)">
        <option value="bar">柱状图</option>
        <option value="line">折线图</option>
        <option value="pie">饼图</option>
      </select>
    </label>
    <div class="field-chip-list">
      <span
        v-for="(name, index) in names"
        :key="`${chipKeyPrefix}-${name}`"
        class="field-chip"
        :class="{
          'field-chip--dragging': isDragging(name),
          'field-chip--drop-target': isDropTarget(name),
        }"
        :title="fieldHelpText(name)"
        @dragover.prevent="$emit('hoverDrop', name)"
        @drop.prevent="$emit('drop', name)"
        @dragend="$emit('clearDrag')"
      >
        <span
          class="field-chip-handle"
          draggable="true"
          role="button"
          tabindex="0"
          :aria-label="`拖动${fieldDisplayLabel(name)}调整顺序`"
          @dragstart.stop="$emit('startDrag', name, $event)"
          @dragend.stop="$emit('clearDrag')"
        >⋮⋮</span>
        {{ fieldDisplayLabel(name) }}
        <button type="button" title="上移" :aria-label="`上移${fieldDisplayLabel(name)}`" :disabled="index === 0" @click="$emit('moveName', name, -1)">↑</button>
        <button type="button" title="下移" :aria-label="`下移${fieldDisplayLabel(name)}`" :disabled="index === names.length - 1" @click="$emit('moveName', name, 1)">↓</button>
        <button type="button" title="移除" :aria-label="`移除${fieldDisplayLabel(name)}`" @click="$emit('removeName', name)">×</button>
      </span>
    </div>
    <form v-if="advancedPanelOpen" class="field-chip-add" @submit.prevent="$emit('addName')">
      <input
        :value="draftValue"
        type="text"
        placeholder="输入字段名"
        @input="$emit('update:draftValue', ($event.target as HTMLInputElement).value)"
      />
      <button type="submit" class="ghost small">添加</button>
    </form>
    <input
      v-if="fieldOptions.length || searchValue"
      :value="searchValue"
      class="field-option-search"
      type="search"
      placeholder="搜索可选字段"
      @input="$emit('update:searchValue', ($event.target as HTMLInputElement).value)"
    />
    <div class="field-option-summary">
      <span>可添加字段 {{ fieldOptionTotal }}，当前显示 {{ fieldOptions.length }}</span>
      <button
        type="button"
        class="link-button"
        :disabled="!fieldOptions.length"
        @click="$emit('addVisibleOptions')"
      >
        添加当前显示字段
      </button>
    </div>
    <div v-if="fieldOptions.length" class="field-option-pool">
      <button
        v-for="field in fieldOptions"
        :key="`${optionKeyPrefix}-${field.name}`"
        type="button"
        :title="fieldOptionHelpText(field)"
        @click="$emit('addName', field.name)"
      >
        {{ fieldOptionLabel(field) }}
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
type FieldOption = {
  name: string;
  label: string;
  type: string;
};

defineProps<{
  title: string;
  names: string[];
  fieldOptions: FieldOption[];
  fieldOptionTotal: number;
  searchValue: string;
  draftValue: string;
  advancedPanelOpen: boolean;
  chipKeyPrefix: string;
  optionKeyPrefix: string;
  showGraphType?: boolean;
  graphType?: string;
  fieldDisplayLabel: (name: string) => string;
  fieldHelpText: (name: string) => string;
  fieldOptionHelpText: (field: FieldOption) => string;
  fieldOptionLabel: (field: FieldOption) => string;
  isDragging: (name: string) => boolean;
  isDropTarget: (name: string) => boolean;
}>();

defineEmits<{
  'update:searchValue': [value: string];
  'update:draftValue': [value: string];
  'update:graphType': [value: string];
  addName: [name?: string];
  addVisibleOptions: [];
  removeName: [name: string];
  moveName: [name: string, delta: number];
  startDrag: [name: string, event: DragEvent];
  hoverDrop: [name: string];
  drop: [name: string];
  clearDrag: [];
}>();
</script>
