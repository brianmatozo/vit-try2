<script lang="ts" generics="TData extends RowData">
import {
	FlexRender,
	type RowData,
	type SvelteTable,
	type TableFeatures,
} from '@tanstack/svelte-table';
import { createVirtualizer } from '@tanstack/svelte-virtual';
import { get } from 'svelte/store';
import { cn } from '../utils.js';

// biome-ignore lint/suspicious/noExplicitAny: TanStack Table v9 generic row data default
export interface VirtualTableProps<TData extends RowData = any> {
	// biome-ignore lint/suspicious/noExplicitAny: TanStack Table v9 features vary per table instance
	table: any;
	height?: string;
	estimateRowHeight?: number;
	class?: string;
}

let {
	table,
	height = '500px',
	estimateRowHeight = 40,
	class: className = '',
}: VirtualTableProps<TData> = $props();

let scrollContainer: HTMLDivElement | undefined = $state();

const rows = $derived(table.getRowModel().rows);

const virtualizer = createVirtualizer({
	count: 0,
	getScrollElement: () => scrollContainer ?? null,
	estimateSize: () => estimateRowHeight,
	overscan: 10,
	getItemKey: (index) => rows[index]?.id ?? index,
});

$effect(() => {
	const count = rows.length;
	const container = scrollContainer;
	get(virtualizer).setOptions({
		count,
		getScrollElement: () => container ?? null,
		estimateSize: () => estimateRowHeight,
		overscan: 10,
		getItemKey: (index) => rows[index]?.id ?? index,
	});
});

const virtualRows = $derived($virtualizer.getVirtualItems());
const totalSize = $derived($virtualizer.getTotalSize());

const paddingTop = $derived(virtualRows.length > 0 ? virtualRows[0].start : 0);
const paddingBottom = $derived(
	virtualRows.length > 0
		? totalSize - virtualRows[virtualRows.length - 1].end
		: 0,
);
</script>

<div
  bind:this={scrollContainer}
  style:height
  class={cn(
    'w-full overflow-auto border border-gray-200 rounded-md bg-white relative',
    className
  )}
>
  <table class="w-full text-left text-sm text-gray-700 divide-y divide-gray-200">
    <thead class="sticky top-0 z-10 bg-gray-50 text-xs uppercase tracking-wider text-gray-500 shadow-xs select-none">
      {#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
        <tr>
          {#each headerGroup.headers as header (header.id)}
            {@const metaClass = (header.column.columnDef.meta as any)?.className ?? ''}
            <th
              scope="col"
              class={cn(
                'px-3 sm:px-4 py-2 sm:py-3 font-semibold bg-gray-50 text-[11px] sm:text-xs',
                metaClass,
                header.column.getCanSort() && 'cursor-pointer hover:bg-gray-100'
              )}
              onclick={header.column.getToggleSortingHandler()}
            >
              {#if !header.isPlaceholder}
                <div class="flex items-center gap-1.5">
                  <FlexRender {header} />
                  {#if header.column.getIsSorted() === 'asc'}
                    <span class="text-xs text-emerald-600 font-bold">▲</span>
                  {:else if header.column.getIsSorted() === 'desc'}
                    <span class="text-xs text-emerald-600 font-bold">▼</span>
                  {/if}
                </div>
              {/if}
            </th>
          {/each}
        </tr>
      {/each}
    </thead>
    <tbody class="divide-y divide-gray-200 bg-white">
      {#if rows.length === 0}
        <tr>
          <td
            colspan={table.getAllColumns().length}
            class="px-4 py-8 text-center text-gray-400"
          >
            No se encontraron registros
          </td>
        </tr>
      {:else if virtualRows.length > 0}
        {#if paddingTop > 0}
          <tr>
            <td style:height="{paddingTop}px" colspan={table.getAllColumns().length}></td>
          </tr>
        {/if}
        {#each virtualRows as virtualRow (virtualRow.key ?? virtualRow.index)}
          {@const row = rows[virtualRow.index]}
          {#if row}
            <tr
              data-index={virtualRow.index}
              class="hover:bg-gray-50 transition-colors h-[40px]"
            >
              {#each (row.getVisibleCells ? row.getVisibleCells() : row.getAllCells()) as cell (cell.id)}
                {@const metaClass = (cell.column.columnDef.meta as any)?.className ?? ''}
                <td class={cn('px-3 sm:px-4 py-2 sm:py-2.5 whitespace-nowrap text-xs sm:text-sm', metaClass)}>
                  <FlexRender {cell} />
                </td>
              {/each}
            </tr>
          {/if}
        {/each}
        {#if paddingBottom > 0}
          <tr>
            <td style:height="{paddingBottom}px" colspan={table.getAllColumns().length}></td>
          </tr>
        {/if}
      {:else}
        {#each rows.slice(0, 30) as row (row.id)}
          <tr class="hover:bg-gray-50 transition-colors h-[40px]">
            {#each (row.getVisibleCells ? row.getVisibleCells() : row.getAllCells()) as cell (cell.id)}
              {@const metaClass = (cell.column.columnDef.meta as any)?.className ?? ''}
              <td class={cn('px-3 sm:px-4 py-2 sm:py-2.5 whitespace-nowrap text-xs sm:text-sm', metaClass)}>
                <FlexRender {cell} />
              </td>
            {/each}
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>
</div>
