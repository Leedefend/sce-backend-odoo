import { defineComponent, h, type PropType } from 'vue';
import type { MenuConfigMenu } from '../../api/menuConfig';

export type MenuConfigDropPosition = 'before' | 'after' | 'inside';

export function createMenuConfigTree(options: {
  menuPathLabel: (menu: MenuConfigMenu) => string;
  menuDisplayLabel: (menu: MenuConfigMenu) => string;
  menuHandlingStateClass: (menu: MenuConfigMenu) => string;
  menuTreeStateLabel: (menu: MenuConfigMenu) => string;
  isUserCreatedMenu: (menu: MenuConfigMenu) => boolean;
}) {
  const MenuConfigTree = defineComponent({
    name: 'MenuConfigTree',
    props: {
      nodes: { type: Array as PropType<MenuConfigMenu[]>, required: true },
      selectedMenuId: { type: Number, required: true },
      dragSourceMenuId: { type: Number, default: 0 },
      dragTargetMenuId: { type: Number, default: 0 },
      dragDropPosition: { type: String as PropType<MenuConfigDropPosition>, default: 'after' },
      dragEnabled: { type: Boolean, default: true },
      searchActive: { type: Boolean, default: false },
      collapsedMenuIds: { type: Object as PropType<Set<number>>, required: true },
      level: { type: Number, default: 0 },
    },
    emits: ['select', 'drag-start', 'drag-over', 'drop', 'drag-end', 'reorder', 'order-move', 'toggle-collapse'],
    setup(props, { emit }) {
      return () => h('ul', { class: ['config-tree-list', `depth-${props.level}`] }, props.nodes.map((node) => {
        const hasChildren = Boolean(node.children?.length);
        const collapsed = hasChildren && !props.searchActive && props.collapsedMenuIds.has(node.id);
        return h('li', { key: node.id }, [
        h('button', {
          type: 'button',
          draggable: false,
          'data-menu-id': String(node.id),
          class: [
            'tree-node',
            {
              active: node.id === props.selectedMenuId,
              draggable: props.dragEnabled,
              dragging: node.id === props.dragSourceMenuId,
              'drop-before': node.id === props.dragTargetMenuId && props.dragDropPosition === 'before',
              'drop-after': node.id === props.dragTargetMenuId && props.dragDropPosition === 'after',
              'drop-inside': node.id === props.dragTargetMenuId && props.dragDropPosition === 'inside',
            },
          ],
          style: { paddingLeft: `${8 + props.level * 14}px` },
          title: props.dragEnabled ? '拖动调整同级菜单顺序' : '搜索时不可拖动排序',
          onClick: () => emit('select', node.id),
          onMousedown: (event: MouseEvent) => {
            if (!props.dragEnabled || event.button !== 0) return;
            event.preventDefault();
            emit('drag-start', node.id);
            const resolveTarget = (rawEvent: MouseEvent) => {
              const element = document.elementFromPoint(rawEvent.clientX, rawEvent.clientY)?.closest('.tree-node') as HTMLElement | null;
              const menuId = Number(element?.dataset?.menuId || 0);
              if (!element || !menuId) return null;
              const rect = element.getBoundingClientRect();
              const position: MenuConfigDropPosition = rawEvent.clientY < rect.top + rect.height / 2 ? 'before' : 'after';
              return { menuId, position };
            };
            const cleanup = () => {
              window.removeEventListener('mousemove', handleMove);
              window.removeEventListener('mouseup', handleUp);
            };
            const handleMove = (moveEvent: MouseEvent) => {
              const target = resolveTarget(moveEvent);
              if (target) emit('drag-over', target);
            };
            const handleUp = (upEvent: MouseEvent) => {
              const target = resolveTarget(upEvent);
              cleanup();
              if (target && target.menuId !== node.id) {
                emit('reorder', { sourceId: node.id, targetId: target.menuId, position: target.position });
                return;
              }
              emit('drop', target?.menuId || node.id);
            };
            window.addEventListener('mousemove', handleMove);
            window.addEventListener('mouseup', handleUp, { once: true });
          },
          onDragstart: (event: DragEvent) => {
            if (!props.dragEnabled) return;
            event.dataTransfer?.setData('text/plain', String(node.id));
            event.dataTransfer?.setDragImage(event.currentTarget as Element, 12, 12);
            emit('drag-start', node.id);
          },
          onDragover: (event: DragEvent) => {
            if (!props.dragEnabled) return;
            event.preventDefault();
            const rect = (event.currentTarget as Element).getBoundingClientRect();
            const position: MenuConfigDropPosition = event.clientY < rect.top + rect.height / 2 ? 'before' : 'after';
            emit('drag-over', { menuId: node.id, position });
          },
            onDrop: (event: DragEvent) => {
              if (!props.dragEnabled) return;
              event.preventDefault();
              emit('drop', node.id);
          },
          onDragend: () => emit('drag-end'),
        }, [
          hasChildren
            ? h('span', {
              class: ['branch-marker', 'toggleable', { collapsed }],
              role: 'button',
              title: collapsed ? '展开分组' : '收起分组',
              onMousedown: (event: MouseEvent) => event.stopPropagation(),
              onClick: (event: MouseEvent) => {
                event.stopPropagation();
                emit('toggle-collapse', node.id);
              },
            }, collapsed ? '▸' : '▾')
            : h('span', { class: 'branch-marker' }, ''),
          h('span', { title: options.menuPathLabel(node) }, options.menuDisplayLabel(node)),
          h('span', {
            class: [
              'menu-origin-badge',
              options.menuHandlingStateClass(node),
              'tree-origin-badge',
            ],
          }, options.menuTreeStateLabel(node)),
          options.isUserCreatedMenu(node)
            ? h('span', { class: ['menu-origin-badge', 'deletable', 'tree-origin-badge'] }, '可删除')
            : null,
        ]),
        hasChildren && !collapsed
          ? h(MenuConfigTree, {
            nodes: node.children,
            selectedMenuId: props.selectedMenuId,
            dragSourceMenuId: props.dragSourceMenuId,
            dragTargetMenuId: props.dragTargetMenuId,
            dragDropPosition: props.dragDropPosition,
            dragEnabled: props.dragEnabled,
            searchActive: props.searchActive,
            collapsedMenuIds: props.collapsedMenuIds,
            level: props.level + 1,
            onSelect: (id: number) => emit('select', id),
            onDragStart: (id: number) => emit('drag-start', id),
            onDragOver: (payload: { menuId: number; position: MenuConfigDropPosition }) => emit('drag-over', payload),
            onDrop: (id: number) => emit('drop', id),
            onDragEnd: () => emit('drag-end'),
            onReorder: (payload: { sourceId: number; targetId: number; position: MenuConfigDropPosition }) => emit('reorder', payload),
            onOrderMove: (payload: { menuId: number; delta: number }) => emit('order-move', payload),
            onToggleCollapse: (id: number) => emit('toggle-collapse', id),
          })
          : null,
        ]);
      }));
    },
  });
  return MenuConfigTree;
}
