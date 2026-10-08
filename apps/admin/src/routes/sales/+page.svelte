<script lang="ts">
import { createQuery, useQueryClient } from '@tanstack/svelte-query';
import {
	getInventoryLedgerOptions,
	type InventoryLedgerResponse,
	type ProductResponse,
	productReadMultiApiV1ProductsGetOptions,
} from '@vitalcer/api';
import {
	calculateBulkLineTotal,
	formatARS,
	formatWeight,
} from '@vitalcer/core';
import { Badge, Button, Card, Input } from '@vitalcer/ui';
import {
	AlertCircle,
	ArrowRight,
	Calendar,
	ChevronDown,
	ChevronUp,
	DollarSign,
	ExternalLink,
	Package,
	Receipt,
	RefreshCw,
	Search,
	ShoppingBag,
	TrendingUp,
} from 'lucide-svelte';

const queryClient = useQueryClient();

// Query completed POS sales from immutable ledger
const ledgerQuery = createQuery(() =>
	getInventoryLedgerOptions({
		query: {
			movement_type: 'sale_pos',
			limit: 500,
		},
	}),
);

// Query product catalog for name, SKU, and unit prices
const productsQuery = createQuery(() =>
	productReadMultiApiV1ProductsGetOptions({
		query: { limit: 1000 },
	}),
);

const ledgerEntries = $derived<InventoryLedgerResponse[]>(
	Array.isArray(ledgerQuery.data) ? ledgerQuery.data : [],
);

const productsList = $derived<ProductResponse[]>(
	productsQuery.data && 'data' in productsQuery.data
		? (productsQuery.data.data as ProductResponse[])
		: Array.isArray(productsQuery.data)
			? (productsQuery.data as ProductResponse[])
			: [],
);

const productsMap = $derived.by(() => {
	const map = new Map<number, ProductResponse>();
	for (const p of productsList) {
		map.set(p.id, p);
	}
	return map;
});

interface TicketItem {
	ledgerId: number;
	productId: number;
	productName: string;
	sku: string;
	productType: 'bulk' | 'discrete';
	quantity: number;
	unitPrice: number;
	bulkReferenceGrams?: number;
	subtotal: number;
}

interface TicketGroup {
	ticketId: string;
	createdAt: string;
	date: Date;
	items: TicketItem[];
	totalAmount: number;
	totalUnitsOrLines: number;
}

// Group ledger entries by ticket reference ID
const tickets = $derived.by<TicketGroup[]>(() => {
	const map = new Map<string, TicketGroup>();

	for (const entry of ledgerEntries) {
		if (entry.movement_type !== 'sale_pos') continue;

		const ticketId = entry.reference_id || `POS-MOV-${entry.id}`;
		let group = map.get(ticketId);
		if (!group) {
			group = {
				ticketId,
				createdAt: entry.created_at,
				date: new Date(entry.created_at),
				items: [],
				totalAmount: 0,
				totalUnitsOrLines: 0,
			};
			map.set(ticketId, group);
		}

		const product = productsMap.get(entry.product_id);
		const qty = Math.abs(entry.quantity_delta);

		let subtotal = 0;
		let productName = `Artículo #${entry.product_id}`;
		let sku = `ID-${entry.product_id}`;
		let productType: 'bulk' | 'discrete' = 'discrete';
		let unitPrice = 0;
		let bulkReferenceGrams: number | undefined;

		if (product) {
			productName = product.name;
			sku = product.sku;
			productType = product.product_type ?? 'discrete';
			unitPrice = product.unit_price;
			bulkReferenceGrams = product.bulk_reference_grams ?? 100;

			if (productType === 'bulk') {
				subtotal = calculateBulkLineTotal(unitPrice, bulkReferenceGrams, qty);
			} else {
				subtotal = qty * unitPrice;
			}
		}

		group.items.push({
			ledgerId: entry.id,
			productId: entry.product_id,
			productName,
			sku,
			productType,
			quantity: qty,
			unitPrice,
			bulkReferenceGrams,
			subtotal,
		});

		group.totalAmount += subtotal;
		group.totalUnitsOrLines += 1;
	}

	return Array.from(map.values()).sort(
		(a, b) => b.date.getTime() - a.date.getTime(),
	);
});

// Search filter
let searchTerm = $state('');
let expandedTicketIds = $state(new Set<string>());

function toggleExpand(ticketId: string) {
	const next = new Set(expandedTicketIds);
	if (next.has(ticketId)) {
		next.delete(ticketId);
	} else {
		next.add(ticketId);
	}
	expandedTicketIds = next;
}

const filteredTickets = $derived(
	tickets.filter((t) => {
		const term = searchTerm.trim().toLowerCase();
		if (!term) return true;
		if (t.ticketId.toLowerCase().includes(term)) return true;
		return t.items.some(
			(item) =>
				item.productName.toLowerCase().includes(term) ||
				item.sku.toLowerCase().includes(term),
		);
	}),
);

// High-level KPI metrics
const totalRevenue = $derived(
	tickets.reduce((acc, t) => acc + t.totalAmount, 0),
);
const totalTicketsCount = $derived(tickets.length);
const averageTicket = $derived(
	totalTicketsCount > 0 ? Math.round(totalRevenue / totalTicketsCount) : 0,
);
const totalItemsSold = $derived(
	tickets.reduce((acc, t) => acc + t.totalUnitsOrLines, 0),
);

function formatTicketDate(isoDate: string): string {
	const d = new Date(isoDate);
	if (Number.isNaN(d.getTime())) return isoDate;
	return d.toLocaleString('es-AR', {
		day: '2-digit',
		month: '2-digit',
		year: 'numeric',
		hour: '2-digit',
		minute: '2-digit',
	});
}

async function handleRefresh() {
	await Promise.all([
		queryClient.invalidateQueries({ queryKey: ['getInventoryLedger'] }),
		queryClient.invalidateQueries({
			queryKey: ['productReadMultiApiV1ProductsGet'],
		}),
	]);
}
</script>

<svelte:head>
	<title>Ventas de Caja | Vitalcer Admin</title>
</svelte:head>

<div class="space-y-6">
	<!-- Page Header -->
	<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
		<div>
			<h1 class="text-2xl font-bold tracking-tight text-gray-900">
				Ventas de Caja
			</h1>
			<p class="text-sm text-gray-500 mt-1">
				Registro y desglose de comprobantes cobrados en mostrador (POS).
			</p>
		</div>

		<div class="flex items-center gap-2">
			<Button
				variant="outline"
				onclick={handleRefresh}
				disabled={ledgerQuery.isFetching || productsQuery.isFetching}
				class="gap-1.5 cursor-pointer text-xs sm:text-sm"
			>
				<RefreshCw
					class="w-4 h-4 {ledgerQuery.isFetching || productsQuery.isFetching ? 'animate-spin' : ''}"
				/>
				<span>Actualizar</span>
			</Button>
		</div>
	</div>

	<!-- KPI Summary Metrics -->
	<div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
		<!-- Total Facturado -->
		<Card class="p-4 sm:p-5 flex flex-col justify-between">
			<div class="flex items-center justify-between text-gray-500 mb-2">
				<span class="text-xs font-semibold uppercase tracking-wider">Total Facturado</span>
				<div class="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
					<DollarSign class="w-4 h-4" />
				</div>
			</div>
			<div>
				<div class="text-xl sm:text-2xl font-black text-emerald-700">
					{formatARS(totalRevenue)}
				</div>
				<div class="text-xs text-gray-400 mt-0.5">Monto total cobrado</div>
			</div>
		</Card>

		<!-- Cantidad de Tickets -->
		<Card class="p-4 sm:p-5 flex flex-col justify-between">
			<div class="flex items-center justify-between text-gray-500 mb-2">
				<span class="text-xs font-semibold uppercase tracking-wider">Tickets Emitidos</span>
				<div class="p-2 bg-blue-50 text-blue-600 rounded-lg">
					<ShoppingBag class="w-4 h-4" />
				</div>
			</div>
			<div>
				<div class="text-xl sm:text-2xl font-black text-gray-900">
					{totalTicketsCount}
				</div>
				<div class="text-xs text-gray-400 mt-0.5">Operaciones completadas</div>
			</div>
		</Card>

		<!-- Ticket Promedio -->
		<Card class="p-4 sm:p-5 flex flex-col justify-between">
			<div class="flex items-center justify-between text-gray-500 mb-2">
				<span class="text-xs font-semibold uppercase tracking-wider">Ticket Promedio</span>
				<div class="p-2 bg-violet-50 text-violet-600 rounded-lg">
					<TrendingUp class="w-4 h-4" />
				</div>
			</div>
			<div>
				<div class="text-xl sm:text-2xl font-black text-gray-900">
					{formatARS(averageTicket)}
				</div>
				<div class="text-xs text-gray-400 mt-0.5">Promedio por venta</div>
			</div>
		</Card>

		<!-- Artículos Vendidos -->
		<Card class="p-4 sm:p-5 flex flex-col justify-between">
			<div class="flex items-center justify-between text-gray-500 mb-2">
				<span class="text-xs font-semibold uppercase tracking-wider">Artículos Despachados</span>
				<div class="p-2 bg-amber-50 text-amber-600 rounded-lg">
					<Package class="w-4 h-4" />
				</div>
			</div>
			<div>
				<div class="text-xl sm:text-2xl font-black text-gray-900">
					{totalItemsSold}
				</div>
				<div class="text-xs text-gray-400 mt-0.5">Líneas de venta en caja</div>
			</div>
		</Card>
	</div>

	<!-- Filter / Search Header -->
	<Card class="p-3 sm:p-4">
		<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
			<div class="relative flex-1 max-w-md">
				<Search class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
				<Input
					bind:value={searchTerm}
					placeholder="Buscar por N° Ticket (POS-...), producto o SKU..."
					class="pl-9 h-10 text-sm"
				/>
			</div>

			<div class="text-xs text-gray-500 flex items-center justify-between sm:justify-end gap-3">
				<span>
					Mostrando <strong class="text-gray-900 font-semibold">{filteredTickets.length}</strong> de {tickets.length} comprobantes
				</span>
				{#if searchTerm}
					<Button
						variant="ghost"
						size="sm"
						onclick={() => (searchTerm = '')}
						class="text-xs text-rose-600 hover:text-rose-700 h-8 px-2 cursor-pointer"
					>
						Limpiar filtro
					</Button>
				{/if}
			</div>
		</div>
	</Card>

	<!-- Content State -->
	{#if ledgerQuery.isLoading || productsQuery.isLoading}
		<Card class="p-12 text-center">
			<RefreshCw class="w-8 h-8 text-emerald-600 animate-spin mx-auto mb-3" />
			<div class="text-sm font-semibold text-gray-700">Cargando historial de ventas...</div>
			<div class="text-xs text-gray-400 mt-1">Consultando registros del libro mayor de inventario</div>
		</Card>
	{:else if ledgerQuery.isError}
		<Card class="p-6 border-rose-200 bg-rose-50 text-rose-800">
			<div class="flex items-center gap-3">
				<AlertCircle class="w-5 h-5 text-rose-600 shrink-0" />
				<div>
					<div class="text-sm font-bold">Error al consultar las ventas</div>
					<div class="text-xs text-rose-600 mt-0.5">
						No se pudieron cargar los comprobantes desde el servidor. Verificá la conexión con la API.
					</div>
				</div>
			</div>
		</Card>
	{:else if filteredTickets.length === 0}
		<Card class="p-12 text-center">
			<div class="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-3 text-gray-400">
				<Receipt class="w-6 h-6" />
			</div>
			{#if tickets.length === 0}
				<div class="text-sm font-semibold text-gray-700">No hay ventas registradas aún</div>
				<p class="text-xs text-gray-400 max-w-sm mx-auto mt-1">
					Cuando realices cobros en la caja del POS, los comprobantes aparecerán automáticamente en este panel.
				</p>
			{:else}
				<div class="text-sm font-semibold text-gray-700">Sin coincidencias</div>
				<p class="text-xs text-gray-400 max-w-sm mx-auto mt-1">
					No se encontraron comprobantes que coincidan con "{searchTerm}".
				</p>
			{/if}
		</Card>
	{:else}
		<!-- Tickets List -->
		<div class="space-y-3">
			{#each filteredTickets as ticket (ticket.ticketId)}
				{@const isExpanded = expandedTicketIds.has(ticket.ticketId)}
				<Card class="overflow-hidden border-gray-200 transition-all hover:border-gray-300">
					<!-- Ticket Summary Row -->
					<div
						role="button"
						tabindex="0"
						onclick={() => toggleExpand(ticket.ticketId)}
						onkeydown={(e) => {
							if (e.key === 'Enter' || e.key === ' ') {
								e.preventDefault();
								toggleExpand(ticket.ticketId);
							}
						}}
						class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer bg-white hover:bg-gray-50/75 transition-colors select-none"
					>
						<div class="flex items-start sm:items-center gap-3">
							<div class="p-2.5 rounded-xl bg-neutral-100 text-neutral-700 shrink-0 mt-0.5 sm:mt-0">
								<Receipt class="w-5 h-5" />
							</div>

							<div>
								<div class="flex items-center gap-2 flex-wrap">
									<span class="font-mono font-bold text-sm text-gray-900 tracking-tight">
										#{ticket.ticketId}
									</span>
									<Badge variant="outline" class="text-[11px] font-medium py-0 px-2 bg-gray-50 text-gray-600">
										{ticket.items.length} {ticket.items.length === 1 ? 'artículo' : 'artículos'}
									</Badge>
								</div>
								<div class="flex items-center gap-1.5 text-xs text-gray-500 mt-1">
									<Calendar class="w-3.5 h-3.5 text-gray-400" />
									<span>{formatTicketDate(ticket.createdAt)}</span>
								</div>
							</div>
						</div>

						<div class="flex items-center justify-between sm:justify-end gap-4 pt-2 sm:pt-0 border-t sm:border-t-0 border-gray-100">
							<div class="text-right">
								<div class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total</div>
								<div class="text-lg font-black text-emerald-600">
									{formatARS(ticket.totalAmount)}
								</div>
							</div>

							<button
								type="button"
								class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
								aria-label={isExpanded ? 'Contraer ticket' : 'Ver detalle del ticket'}
							>
								{#if isExpanded}
									<ChevronUp class="w-5 h-5" />
								{:else}
									<ChevronDown class="w-5 h-5" />
								{/if}
							</button>
						</div>
					</div>

					<!-- Expandable Item Breakdown -->
					{#if isExpanded}
						<div class="border-t border-gray-100 bg-gray-50/50 p-4 space-y-3">
							<div class="text-xs font-bold uppercase tracking-wider text-gray-500">
								Desglose de Artículos
							</div>

							<div class="overflow-x-auto rounded-lg border border-gray-200 bg-white">
								<table class="w-full text-left text-xs text-gray-600">
									<thead class="bg-gray-50 text-gray-700 font-semibold border-b border-gray-200">
										<tr>
											<th scope="col" class="py-2.5 px-3">Artículo</th>
											<th scope="col" class="py-2.5 px-3">Tipo</th>
											<th scope="col" class="py-2.5 px-3 text-right">Cantidad</th>
											<th scope="col" class="py-2.5 px-3 text-right">Precio Unitario</th>
											<th scope="col" class="py-2.5 px-3 text-right">Subtotal</th>
											<th scope="col" class="py-2.5 px-3 text-center">Auditoría</th>
										</tr>
									</thead>
									<tbody class="divide-y divide-gray-100 font-medium">
										{#each ticket.items as item (item.ledgerId)}
											<tr class="hover:bg-gray-50/75 transition-colors">
												<td class="py-2.5 px-3">
													<div class="font-bold text-gray-900">{item.productName}</div>
													<div class="text-[11px] text-gray-400 font-mono">{item.sku}</div>
												</td>
												<td class="py-2.5 px-3">
													{#if item.productType === 'bulk'}
														<Badge variant="outline" class="text-[10px] bg-purple-50 text-purple-700 border-purple-200">
															Granel
														</Badge>
													{:else}
														<Badge variant="outline" class="text-[10px] bg-sky-50 text-sky-700 border-sky-200">
															Unidad
														</Badge>
													{/if}
												</td>
												<td class="py-2.5 px-3 text-right font-mono font-semibold text-gray-800">
													{#if item.productType === 'bulk'}
														{formatWeight(item.quantity)}
													{:else}
														{item.quantity} u.
													{/if}
												</td>
												<td class="py-2.5 px-3 text-right font-mono text-gray-700">
													{#if item.productType === 'bulk'}
														{formatARS(item.unitPrice)} / {item.bulkReferenceGrams ?? 100}g
													{:else}
														{formatARS(item.unitPrice)}
													{/if}
												</td>
												<td class="py-2.5 px-3 text-right font-mono font-bold text-emerald-700">
													{formatARS(item.subtotal)}
												</td>
												<td class="py-2.5 px-3 text-center">
													<a
														href={`/ledger?product_id=${item.productId}`}
														title="Ver auditoría de movimientos"
														class="inline-flex items-center gap-1 text-[11px] text-emerald-600 hover:text-emerald-700 hover:underline font-semibold"
													>
														<span>Ver</span>
														<ExternalLink class="w-3 h-3" />
													</a>
												</td>
											</tr>
										{/each}
									</tbody>
									<tfoot class="bg-gray-50/80 border-t border-gray-200 font-bold text-gray-900">
										<tr>
											<td colspan="4" class="py-2.5 px-3 text-right uppercase text-[11px] tracking-wider text-gray-500">
												Total Ticket:
											</td>
											<td class="py-2.5 px-3 text-right text-emerald-700 text-sm font-black font-mono">
												{formatARS(ticket.totalAmount)}
											</td>
											<td></td>
										</tr>
									</tfoot>
								</table>
							</div>
						</div>
					{/if}
				</Card>
			{/each}
		</div>
	{/if}
</div>
