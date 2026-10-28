<script lang="ts">
import type { RemitoResponse } from '@vitalcer/api';
import { formatARS } from '@vitalcer/core';
import { Badge, Button, Card } from '@vitalcer/ui';
import { ArrowRight, FileText, Inbox } from 'lucide-svelte';

interface Props {
	remitos: RemitoResponse[];
}

let { remitos }: Props = $props();

function formatDate(dateStr: string | null | undefined): string {
	if (!dateStr) return 'Sin fecha';
	try {
		return new Date(dateStr).toLocaleDateString('es-AR', {
			day: '2-digit',
			month: 'short',
			year: 'numeric',
		});
	} catch {
		return dateStr;
	}
}
</script>

{#if remitos.length === 0}
	<Card class="p-12 text-center">
		<Inbox class="w-10 h-10 text-gray-300 mx-auto mb-3" />
		<div class="text-sm font-semibold text-gray-700">No se encontraron remitos</div>
		<p class="text-xs text-gray-400 mt-1 max-w-sm mx-auto">
			No hay comprobantes que coincidan con los filtros aplicados. Podés cargar un nuevo remito escaneando el comprobante en papel.
		</p>
		<div class="mt-4">
			<a href="/remitos/new">
				<Button size="sm" class="bg-emerald-600 hover:bg-emerald-700 text-white">
					Escanear Nuevo Remito
				</Button>
			</a>
		</div>
	</Card>
{:else}
	<Card class="overflow-hidden border border-gray-200">
		<div class="overflow-x-auto">
			<table class="w-full text-left text-xs">
				<thead class="bg-gray-50 border-b border-gray-200 text-gray-500 font-semibold uppercase text-2xs tracking-wider">
					<tr>
						<th class="py-3 px-4">Comprobante</th>
						<th class="py-3 px-4">Distribuidor</th>
						<th class="py-3 px-4">Estado</th>
						<th class="py-3 px-4">Líneas</th>
						<th class="py-3 px-4 text-right">Total Factura</th>
						<th class="py-3 px-4 text-right">Costo Real</th>
						<th class="py-3 px-4 text-right">Acción</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100 text-gray-800">
					{#each remitos as r (r.id)}
						<tr class="hover:bg-gray-50/70 transition-colors">
							<td class="py-3 px-4">
								<div class="font-bold text-gray-900 flex items-center gap-1.5">
									<FileText class="w-3.5 h-3.5 text-gray-400" />
									{r.remito_number || `Remito #${r.id}`}
								</div>
								<div class="text-2xs text-gray-400 mt-0.5">{formatDate(r.date_issued || r.created_at)}</div>
							</td>

							<td class="py-3 px-4 font-medium text-gray-900">
								{r.supplier_name}
							</td>

							<td class="py-3 px-4">
								{#if r.status === 'staged'}
									<Badge variant="warning" class="font-semibold">
										Pendiente
									</Badge>
								{:else if r.status === 'committed'}
									<Badge variant="success" class="font-semibold">
										Confirmado
									</Badge>
								{:else}
									<Badge variant="outline">
										{r.status}
									</Badge>
								{/if}
							</td>

							<td class="py-3 px-4 text-gray-600">
								{r.items?.length || 0} ítems ({r.page_count} {r.page_count === 1 ? 'pág' : 'págs'})
							</td>

							<td class="py-3 px-4 text-right font-mono text-gray-600">
								{formatARS(r.total_raw_amount || 0)}
							</td>

							<td class="py-3 px-4 text-right font-mono font-bold text-gray-900">
								{formatARS(r.total_real_amount || 0)}
							</td>

							<td class="py-3 px-4 text-right">
								<a href="/remitos/{r.id}">
									{#if r.status === 'staged'}
										<Button size="sm" class="bg-amber-500 hover:bg-amber-600 text-white gap-1 py-1 px-2.5 h-7 text-xs font-semibold">
											<span>Auditar</span>
											<ArrowRight class="w-3 h-3" />
										</Button>
									{:else}
										<Button variant="outline" size="sm" class="gap-1 py-1 px-2.5 h-7 text-xs">
											<span>Ver</span>
											<ArrowRight class="w-3 h-3" />
										</Button>
									{/if}
								</a>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</Card>
{/if}
