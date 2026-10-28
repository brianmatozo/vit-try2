import { updateConfigApiV1RemitosConfigPost } from '@vitalcer/api';
import { browser } from '$app/environment';

export const OPENROUTER_MODEL_PRESETS = [
	{
		id: 'google/gemini-2.0-flash-001',
		name: 'Gemini 2.0 Flash (Recomendado)',
		desc: 'Ultra rápido, económico y excelente OCR en español',
	},
	{
		id: 'anthropic/claude-3.5-sonnet',
		name: 'Claude 3.5 Sonnet',
		desc: 'Alta precisión para recibos deteriorados o matriz de puntos',
	},
	{
		id: 'google/gemini-1.5-flash',
		name: 'Gemini 1.5 Flash',
		desc: 'Rápido y liviano para remitos estándar',
	},
	{
		id: 'openai/gpt-4o-mini',
		name: 'GPT-4o Mini',
		desc: 'Modelo compacto multimodal de OpenAI',
	},
] as const;

export class RemitoConfigState {
	apiKey = $state('');
	selectedModel = $state('google/gemini-2.0-flash-001');
	customModel = $state('');
	isCustom = $state(false);
	isOpen = $state(false);
	isSaving = $state(false);
	statusMessage = $state<string | null>(null);

	hasKey = $derived(this.apiKey.trim().length > 0);
	effectiveModel = $derived(
		this.isCustom && this.customModel.trim()
			? this.customModel.trim()
			: this.selectedModel,
	);

	constructor() {
		if (browser) {
			const savedKey = localStorage.getItem('vitalcer_openrouter_api_key');
			if (savedKey) this.apiKey = savedKey;

			const savedModel = localStorage.getItem('vitalcer_openrouter_model');
			if (savedModel) {
				const isPreset = OPENROUTER_MODEL_PRESETS.some(
					(p) => p.id === savedModel,
				);
				if (isPreset) {
					this.selectedModel = savedModel;
					this.isCustom = false;
				} else {
					this.customModel = savedModel;
					this.isCustom = true;
				}
			}
		}
	}

	open(): void {
		this.statusMessage = null;
		this.isOpen = true;
	}

	close(): void {
		this.isOpen = false;
	}

	selectPreset(modelId: string): void {
		this.selectedModel = modelId;
		this.isCustom = false;
	}

	async save(): Promise<void> {
		this.isSaving = true;
		this.statusMessage = null;

		const keyToSave = this.apiKey.trim();
		const modelToSave = this.effectiveModel;

		if (browser) {
			localStorage.setItem('vitalcer_openrouter_api_key', keyToSave);
			localStorage.setItem('vitalcer_openrouter_model', modelToSave);
		}

		try {
			await updateConfigApiV1RemitosConfigPost({
				body: {
					api_key: keyToSave || undefined,
					primary_model: modelToSave,
				},
			});
			this.statusMessage = 'Configuración guardada correctamente';
			setTimeout(() => {
				this.isOpen = false;
				this.statusMessage = null;
			}, 800);
		} catch {
			this.statusMessage = 'Guardado localmente en este navegador';
			setTimeout(() => {
				this.isOpen = false;
				this.statusMessage = null;
			}, 1000);
		} finally {
			this.isSaving = false;
		}
	}
}
