<script lang="ts">
import { Button, Card } from '@vitalcer/ui';
import { Camera, FileText, Trash2, UploadCloud } from 'lucide-svelte';
import type { RemitoConfigState } from '../remito-config-state.svelte';
import RemitoFiscalInputs from './RemitoFiscalInputs.svelte';

type ScanHandler = (
	images: string[],
	blanco: number,
	negro: number,
	iva: number,
	mock: boolean,
) => Promise<void>;

interface Props {
	config: RemitoConfigState;
	isScanning: boolean;
	onScan: ScanHandler;
}

let { config, isScanning, onScan }: Props = $props();

let selectedImages = $state<string[]>([]);
let blancoPct = $state(60);
let negroPct = $state(40);
let ivaPct = $state(21);
let errorMessage = $state<string | null>(null);

function handleFileChange(e: Event): void {
	const input = e.target as HTMLInputElement;
	if (!input.files || input.files.length === 0) return;

	errorMessage = null;
	const files = Array.from(input.files).slice(0, 4);

	for (const file of files) {
		const reader = new FileReader();
		reader.onload = (event) => {
			const result = event.target?.result as string;
			if (result && selectedImages.length < 4) {
				selectedImages = [...selectedImages, result];
			}
		};
		reader.readAsDataURL(file);
	}
}

function removeImage(index: number): void {
	selectedImages = selectedImages.filter((_, i) => i !== index);
}
function handleBlancoChange(val: number): void {
	blancoPct = Math.max(0, Math.min(100, val));
	negroPct = 100 - blancoPct;
}
function handleIvaChange(val: number): void {
	ivaPct = Math.max(0, Math.min(30, val));
}

async function triggerScan(mock = false): Promise<void> {
	if (!mock && selectedImages.length === 0) {
		errorMessage = 'Seleccioná al menos una foto del remito.';
		return;
	}
	if (!mock && !config.hasKey) {
		config.open();
		return;
	}
	errorMessage = null;
	await onScan(selectedImages, blancoPct, negroPct, ivaPct, mock);
}
</script>

<div class="space-y-4">
	<!-- Upload Area Card -->
	<Card class="p-6 text-center border-2 border-dashed border-gray-300 hover:border-emerald-500 transition-colors">
		<input
			type="file"
			id="remito-file-input"
			accept="image/jpeg,image/png,image/webp"
			multiple
			onchange={handleFileChange}
			class="hidden"
		/>

		<div class="flex flex-col items-center justify-center space-y-3">
			<div class="w-12 h-12 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600">
				<UploadCloud class="w-6 h-6" />
			</div>
			<div>
				<div class="text-sm font-semibold text-gray-800">Subí las fotos del remito o recibo en papel</div>
				<p class="text-2xs text-gray-500 mt-0.5">Formatos JPEG, PNG o WebP. Podés adjuntar hasta 4 páginas de un mismo comprobante.</p>
			</div>

			<div class="flex flex-wrap items-center justify-center gap-2 pt-1">
				<label for="remito-file-input">
					<Button size="sm" type="button" class="cursor-pointer gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white">
						<Camera class="w-4 h-4" />
						<span>Tomar Foto / Elegir Archivos</span>
					</Button>
				</label>
				<Button type="button" variant="outline" size="sm" onclick={() => triggerScan(true)} disabled={isScanning} class="border-dashed gap-1 text-gray-600 hover:text-emerald-700">
					<FileText class="w-4 h-4" />
					<span>Cargar Remito de Prueba (Mock)</span>
				</Button>
			</div>
		</div>
	</Card>

	<!-- Image Thumbnails Grid -->
	{#if selectedImages.length > 0}
		<div>
			<div class="text-xs font-semibold text-gray-700 mb-2 flex items-center justify-between">
				<span>Páginas seleccionadas ({selectedImages.length} de 4):</span>
				<button type="button" onclick={() => (selectedImages = [])} class="text-2xs text-rose-600 hover:underline">Quitar todas</button>
			</div>

			<div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
				{#each selectedImages as img, idx (idx)}
					<div class="relative group rounded-lg overflow-hidden border border-gray-200 bg-gray-100 aspect-3/4 flex items-center justify-center">
						<img src={img} alt="Página {idx + 1}" class="w-full h-full object-cover" />
						<div class="absolute bottom-1 left-1.5 px-1.5 py-0.5 rounded bg-black/70 text-white text-3xs font-semibold">Pág. {idx + 1}</div>
						<button
							type="button"
							onclick={() => removeImage(idx)}
							class="absolute top-1.5 right-1.5 w-6 h-6 rounded-full bg-rose-600 text-white flex items-center justify-center opacity-80 hover:opacity-100 transition-opacity shadow-sm"
							title="Eliminar página"
						>
							<Trash2 class="w-3.5 h-3.5" />
						</button>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Fiscal Parameters & Trigger -->
	<RemitoFiscalInputs
		{config}
		{blancoPct}
		{negroPct}
		{ivaPct}
		{isScanning}
		hasImages={selectedImages.length > 0}
		{errorMessage}
		onBlancoChange={handleBlancoChange}
		onIvaChange={handleIvaChange}
		onSubmitScan={() => triggerScan(false)}
	/>
</div>
