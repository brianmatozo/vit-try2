import { describe, expect, it } from 'vitest';
import {
	formatClosureDateTime,
	formatCurrencyARS,
	getClosureStatusBadge,
	getDiscrepancyBadgeInfo,
} from './closure-filter.js';

describe('closure-filter', () => {
	describe('getDiscrepancyBadgeInfo', () => {
		it('returns Sin Arqueo when actual cash is null or undefined', () => {
			const info = getDiscrepancyBadgeInfo(50000, null);
			expect(info.label).toBe('Sin Arqueo');
			expect(info.variant).toBe('default');
			expect(info.amount).toBe(0);

			const info2 = getDiscrepancyBadgeInfo(50000, undefined);
			expect(info2.label).toBe('Sin Arqueo');
		});

		it('returns Exacto for matching expected and actual cash', () => {
			const info = getDiscrepancyBadgeInfo(50000, 50000);
			expect(info.label).toBe('Exacto ($0)');
			expect(info.variant).toBe('success');
			expect(info.status).toBe('exact');
			expect(info.amount).toBe(0);
		});

		it('returns Sobrante for surplus cash', () => {
			const info = getDiscrepancyBadgeInfo(50000, 52000);
			expect(info.label).toContain('Sobrante');
			expect(info.variant).toBe('warning');
			expect(info.status).toBe('surplus');
			expect(info.amount).toBe(2000);
		});

		it('returns Faltante for missing cash', () => {
			const info = getDiscrepancyBadgeInfo(50000, 48500);
			expect(info.label).toContain('Faltante');
			expect(info.variant).toBe('destructive');
			expect(info.status).toBe('shortage');
			expect(info.amount).toBe(-1500);
		});
	});

	describe('formatCurrencyARS', () => {
		it('formats integer ARS amounts without decimals', () => {
			expect(formatCurrencyARS(15000)).toMatch(/\$15/);
			expect(formatCurrencyARS(0)).toBe('$0');
			expect(formatCurrencyARS(null)).toBe('$0');
		});
	});

	describe('formatClosureDateTime', () => {
		it('formats ISO dates correctly', () => {
			const formatted = formatClosureDateTime('2026-10-30T14:30:00Z');
			expect(formatted).not.toBe('—');
			expect(typeof formatted).toBe('string');
		});

		it('returns dash for null or undefined dates', () => {
			expect(formatClosureDateTime(null)).toBe('—');
			expect(formatClosureDateTime(undefined)).toBe('—');
		});
	});

	describe('getClosureStatusBadge', () => {
		it('handles open status', () => {
			const badge = getClosureStatusBadge('open');
			expect(badge.label).toBe('Abierta');
			expect(badge.variant).toBe('success');
		});

		it('handles auto-closed status', () => {
			const badge = getClosureStatusBadge('closed', true);
			expect(badge.label).toContain('Auto-Cerrada');
			expect(badge.variant).toBe('warning');
		});

		it('handles manual closed status', () => {
			const badge = getClosureStatusBadge('closed', false);
			expect(badge.label).toBe('Cerrada');
			expect(badge.variant).toBe('default');
		});
	});
});
