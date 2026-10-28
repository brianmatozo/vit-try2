<script lang="ts">
import { Button, Dialog, Input } from '@vitalcer/ui';
import { CheckCircle2, Eye, EyeOff, Sparkles } from 'lucide-svelte';
import {
	OPENROUTER_MODEL_PRESETS,
	type RemitoConfigState,
} from '../remito-config-state.svelte';

interface Props {
	config: RemitoConfigState;
}

let { config }: Props = $props();
let showKey = $state(false);
</script>

<Dialog
	bind:open={config.isOpen}
	title="Configuración de IA para Remitos"
	description="Configurá tu clave de OpenRouter y el modelo de visión preferido sin tocar archivos .env."
	position="center"
>
	<div class="space-y-4 text-xs">
		<!-- API Key Section -->
		<div>
			<div class="flex items-center justify-between mb-1">
				<label for="or-key" class="font-semibold text-gray-700">
					Clave de API OpenRouter (sk-or-v1-...)
				</label>
				{#if config.hasKey}
					<span class="inline-flex items-center gap-1 text-emerald-600 font-medium text-2xs">
						<CheckCircle2 class="w-3.5 h-3.5" /> Configurada
					</span>
				{:else}
					<span class="text-amber-600 font-medium text-2xs">Requerida para escanear</span>
				{/if}
			</div>

			<div class="relative">
				<Input
					id="or-key"
					type={showKey ? 'text' : 'password'}
					placeholder="sk-or-v1-xxxxxxxxxxxxxxxxxxxx"
					bind:value={config.apiKey}
					class="pr-9 font-mono text-xs"
				/>
				<button
					type="button"
					onclick={() => (showKey = !showKey)}
					class="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-1"
					title={showKey ? 'Ocultar clave' : 'Mostrar clave'}
				>
					{#if showKey}
						<EyeOff class="w-4 h-4" />
					{:else}
						<Eye class="w-4 h-4" />
					{/if}
				</button>
			</div>
			<p class="text-2xs text-gray-400 mt-1">
				Podés obtener una clave en <a href="https://openrouter.ai/keys" target="_blank" rel="noreferrer" class="underline text-emerald-600">openrouter.ai/keys</a>.
			</p>
		</div>

		<!-- Model Selection Section -->
		<div>
			<div class="block font-semibold text-gray-700 mb-1.5">
				Modelo de Visión Artificial
			</div>
			<div class="space-y-1.5">
				{#each OPENROUTER_MODEL_PRESETS as preset (preset.id)}
					{@const isSelected = !config.isCustom && config.selectedModel === preset.id}
					<button
						type="button"
						onclick={() => config.selectPreset(preset.id)}
						class="w-full text-left p-2.5 rounded-lg border transition-all {isSelected ? 'border-emerald-500 bg-emerald-50/50 text-emerald-950 font-medium ring-1 ring-emerald-500/30' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-700'}"
					>
						<div class="flex items-center justify-between">
							<span class="font-semibold text-xs flex items-center gap-1.5">
								{#if preset.id.includes('gemini-2.0')}
									<Sparkles class="w-3.5 h-3.5 text-amber-500" />
								{/if}
								{preset.name}
							</span>
							<span class="text-2xs font-mono text-gray-400">{preset.id}</span>
						</div>
						<div class="text-2xs text-gray-500 mt-0.5">{preset.desc}</div>
					</button>
				{/each}

				<!-- Custom Model Option -->
				<div class="pt-1">
					<label class="flex items-center gap-2 cursor-pointer font-medium text-gray-700 mb-1">
						<input
							type="radio"
							name="modelChoice"
							checked={config.isCustom}
							onchange={() => (config.isCustom = true)}
							class="text-emerald-600 focus:ring-emerald-500"
						/>
						<span>Especificar otro modelo personalizado de OpenRouter</span>
					</label>
					{#if config.isCustom}
						<Input
							placeholder="Ej: deepseek/deepseek-chat o google/gemini-2.5-pro"
							bind:value={config.customModel}
							class="mt-1 font-mono text-xs"
						/>
					{/if}
				</div>
			</div>
		</div>

		{#if config.statusMessage}
			<div class="p-2 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-2xs font-medium text-center">
				{config.statusMessage}
			</div>
		{/if}
	</div>

	{#snippet footer()}
		<Button variant="outline" size="sm" onclick={() => config.close()}>
			Cancelar
		</Button>
		<Button
			size="sm"
			disabled={config.isSaving}
			onclick={() => config.save()}
			class="bg-emerald-600 hover:bg-emerald-700 text-white"
		>
			{config.isSaving ? 'Guardando...' : 'Guardar Ajustes'}
		</Button>
	{/snippet}
</Dialog>
