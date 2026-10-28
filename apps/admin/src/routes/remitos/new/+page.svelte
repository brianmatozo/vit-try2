<script lang="ts">
import { scanImagesApiV1RemitosScanImagesPost } from '@vitalcer/api';
import { Button } from '@vitalcer/ui';
import { ArrowLeft, Sparkles } from 'lucide-svelte';
import { goto } from '$app/navigation';
import RemitoConfigDialog from '$lib/remitos/components/RemitoConfigDialog.svelte';
import RemitoUploadDropzone from '$lib/remitos/components/RemitoUploadDropzone.svelte';
import { RemitoConfigState } from '$lib/remitos/remito-config-state.svelte';

const config = new RemitoConfigState();
let isScanning = $state(false);
let scanError = $state<string | null>(null);

async function handleScan(
	images: string[],
	blancoPct: number,
	negroPct: number,
	ivaPct: number,
	mock: boolean,
): Promise<void> {
	isScanning = true;
	scanError = null;

	try {
		const res = await scanImagesApiV1RemitosScanImagesPost({
			body: {
				images,
				model: config.effectiveModel,
				api_key: config.apiKey || undefined,
				blanco_pct: blancoPct,
				negro_pct: negroPct,
				iva_pct: ivaPct,
				mock,
			},
		});

		if (res.data?.id) {
			await goto(`/remitos/${res.data.id}`);
		} else {
			scanError = 'No se pudo obtener el identificador del remito generado.';
		}
	} catch (err: unknown) {
		scanError =
			err instanceof Error
				? err.message
				: 'Error al procesar el remito con IA. Verificá la clave de OpenRouter y la calidad de la foto.';
	} finally {
		isScanning = false;
	}
}
</script>

<svelte:head>
	<title>Nuevo Remito | Vitalcer Admin</title>
</svelte:head>

<div class="max-w-3xl mx-auto space-y-4">
	<!-- Top Navigation -->
	<div class="flex items-center justify-between pb-2 border-b border-gray-200">
		<div class="flex items-center gap-2">
			<a href="/remitos">
				<Button variant="outline" size="sm" class="h-8 w-8 p-0">
					<ArrowLeft class="w-4 h-4" />
				</Button>
			</a>
			<div>
				<h1 class="text-lg font-bold text-gray-900 flex items-center gap-1.5">
					Escanear Nuevo Remito
					<Sparkles class="w-4 h-4 text-emerald-600" />
				</h1>
				<p class="text-2xs text-gray-500">
					Subí las fotos del comprobante para extracción y matching automático
				</p>
			</div>
		</div>

		<Button
			variant="outline"
			size="sm"
			onclick={() => config.open()}
			class="text-xs"
		>
			Ajustes IA
		</Button>
	</div>

	{#if scanError}
		<div class="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs">
			<span class="font-bold">Error en extracción:</span> {scanError}
		</div>
	{/if}

	<!-- Upload & Scan Component -->
	<RemitoUploadDropzone
		{config}
		{isScanning}
		onScan={handleScan}
	/>

	<!-- Config Dialog -->
	<RemitoConfigDialog {config} />
</div>
