<script lang="ts" generics="TData extends RowData">
import {
	FlexRender,
	type RowData,
	type SvelteTable,
	type TableFeatures,
} from '@tanstack/svelte-table';
import { cn } from '../utils.js';

// biome-ignore lint/suspicious/noExplicitAny: TanStack Table v9 generic row data default
export interface DataTableProps<TData extends RowData = any> {
	// biome-ignore lint/suspicious/noExplicitAny: TanStack Table v9 features vary per table instance
	table: any;
	class?: string;
}

let { table, class: className = '' }: DataTableProps<TData> = $props();
</script>

<div class={cn('w-full overflow-x-auto border border-gray-200 rounded-md bg-white', className)}>
  <table class="w-full text-left text-sm text-gray-700 divide-y divide-gray-200">
    <thead class="bg-gray-50 text-xs uppercase tracking-wider text-gray-500 select-none">
      {#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
        <tr>
          {#each headerGroup.headers as header (header.id)}
            {@const metaClass = (header.column.columnDef.meta as any)?.className ?? ''}
            <th
              scope="col"
              class={cn(
                'px-3 sm:px-4 py-2 sm:py-3 font-semibold text-[11px] sm:text-xs',
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
      {#each table.getRowModel().rows as row (row.id)}
        <tr class="hover:bg-gray-50 transition-colors">
          {#each row.getVisibleCells() as cell (cell.id)}
            {@const metaClass = (cell.column.columnDef.meta as any)?.className ?? ''}
            <td class={cn('px-3 sm:px-4 py-2 sm:py-2.5 whitespace-nowrap text-xs sm:text-sm', metaClass)}>
              <FlexRender {cell} />
            </td>
          {/each}
        </tr>
      {:else}
        <tr>
          <td colspan={table.getAllColumns().length} class="px-4 py-8 text-center text-gray-400">
            No se encontraron registros
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
