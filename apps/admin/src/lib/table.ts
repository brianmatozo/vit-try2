import {
	columnVisibilityFeature,
	createSortedRowModel,
	createTableHook,
	rowSortingFeature,
	sortFns,
	tableFeatures,
} from '@tanstack/svelte-table';

export const { createAppTable, createAppColumnHelper } = createTableHook({
	features: tableFeatures({
		rowSortingFeature,
		columnVisibilityFeature,
		sortedRowModel: createSortedRowModel(),
		sortFns,
	}),
});
