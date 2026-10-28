import { beforeEach, describe, expect, it, vi } from 'vitest';
import { RemitoConfigState } from './remito-config-state.svelte';

vi.mock('$app/environment', () => ({
	browser: false,
}));

vi.mock('@vitalcer/api', () => ({
	updateConfigApiV1RemitosConfigPost: vi.fn().mockResolvedValue({
		data: {
			has_api_key: true,
			primary_model: 'google/gemini-2.0-flash-001',
			fallback_model: 'anthropic/claude-3.5-sonnet',
		},
	}),
}));

describe('RemitoConfigState', () => {
	let state: RemitoConfigState;

	beforeEach(() => {
		state = new RemitoConfigState();
	});

	it('initializes with default preset model and empty key', () => {
		expect(state.apiKey).toBe('');
		expect(state.hasKey).toBe(false);
		expect(state.selectedModel).toBe('google/gemini-2.0-flash-001');
		expect(state.effectiveModel).toBe('google/gemini-2.0-flash-001');
		expect(state.isOpen).toBe(false);
	});

	it('selects another preset model', () => {
		state.selectPreset('anthropic/claude-3.5-sonnet');
		expect(state.selectedModel).toBe('anthropic/claude-3.5-sonnet');
		expect(state.effectiveModel).toBe('anthropic/claude-3.5-sonnet');
		expect(state.isCustom).toBe(false);
	});

	it('supports custom model names', () => {
		state.isCustom = true;
		state.customModel = 'deepseek/deepseek-chat';
		expect(state.effectiveModel).toBe('deepseek/deepseek-chat');
	});

	it('toggles dialog open and close', () => {
		state.open();
		expect(state.isOpen).toBe(true);
		state.close();
		expect(state.isOpen).toBe(false);
	});

	it('saves configuration and marks hasKey', async () => {
		state.apiKey = 'sk-or-v1-abcdef123456';
		expect(state.hasKey).toBe(true);
		await state.save();
		expect(state.isSaving).toBe(false);
	});
});
