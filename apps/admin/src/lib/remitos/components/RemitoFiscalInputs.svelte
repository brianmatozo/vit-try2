<script lang="ts">
import { Button, Card, Input } from '@vitalcer/ui';
import { AlertTriangle, Sparkles } from 'lucide-svelte';
import type { RemitoConfigState } from '../remito-config-state.svelte';

interface Props {
	config: RemitoConfigState;
	blancoPct: number;
	negroPct: number;
	ivaPct: number;
	isScanning: boolean;
	hasImages: boolean;
	errorMessage: string | null;
	onBlancoChange: (val: number) => void;
	onIvaChange: (val: number) => void;
	onSubmitScan: () => void;
}

let {
	config,
	blancoPct,
	negroPct,
	ivaPct,
	isScanning,
	hasImages,
	errorMessage,
	onBlancoChange,
	onIvaChange,
	onSubmitScan,
}: Props = $props();
</script>

<Card class="p-4 bg-gray-50/70 border border-gray-200 space-y-3">
	<div class="text-xs font-bold text-gray-800">
		Parámetros Fiscales del Comprobante
	</div>

	<div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
		<div>
			<label for="blanco-pct" class="block font-medium text-gray-700 mb-1">
				% Blanco (Con Factura)
			</label>
			<Input
				id="blanco-pct"
				type="number"
				min="0"
				max="100"
				value={blancoPct}
				oninput={(e) => onBlancoChange(Number((e.target as HTMLInputElement).value))}
			/>
		</div>

		<div>
			<label for="negro-pct" class="block font-medium text-gray-700 mb-1">
				% Negro (Sin Factura)
			</label>
			<Input
				id="negro-pct"
				type="number"
				min="0"
				max="100"
				disabled
				value={negroPct}
				class="bg-gray-100 text-gray-500"
			/>
		</div>

		<div>
			<label for="iva-pct" class="block font-medium text-gray-700 mb-1">
				% Alícuota IVA
			</label>
			<Input
				id="iva-pct"
				type="number"
				min="0"
				max="30"
				value={ivaPct}
				oninput={(e) => onIvaChange(Number((e.target as HTMLInputElement).value))}
			/>
		</div>
	</div>

	{#if !config.hasKey}
		<div class="p-2.5 rounded-lg bg-amber-50 border border-amber-200 flex items-center justify-between text-amber-900 text-2xs">
			<div class="flex items-center gap-2">
				<AlertTriangle class="w-4 h-4 text-amber-600 shrink-0" />
				<span>No tenés configurada tu clave de OpenRouter para procesar fotos reales.</span>
			</div>
			<button
				type="button"
				onclick={() => config.open()}
				class="font-bold underline text-amber-800 hover:text-amber-950 ml-2 whitespace-nowrap"
			>
				Configurar clave
			</button>
		</div>
	{/if}

	{#if errorMessage}
		<div class="p-2 rounded bg-rose-50 border border-rose-200 text-rose-800 text-2xs font-medium">
			{errorMessage}
		</div>
	{/if}

	<div class="pt-2 flex justify-end gap-2">
		<Button
			size="sm"
			onclick={onSubmitScan}
			disabled={isScanning || !hasImages}
			class="bg-emerald-600 hover:bg-emerald-700 text-white gap-2 px-4 shadow-xs"
		>
			<Sparkles class="w-4 h-4 {isScanning ? 'animate-spin' : ''}" />
			<span>{isScanning ? 'Extrayendo con IA...' : 'Escanear y Auditar'}</span>
		</Button>
	</div>
</Card>
