import { describe, expect, it, vi } from 'vitest';
import { HardwareScannerListener } from './hardware-scanner';

function createKeyboardEvent(
	key: string,
	target: Partial<HTMLElement> = {},
): KeyboardEvent {
	return {
		key,
		target: target as EventTarget,
		preventDefault: vi.fn(),
	} as unknown as KeyboardEvent;
}

describe('HardwareScannerListener', () => {
	it('accumulates rapid keystrokes and fires onScan on Enter', () => {
		const onScan = vi.fn();
		const listener = new HardwareScannerListener(onScan);

		for (const ch of '7791234567890') {
			listener.handleKeydown(createKeyboardEvent(ch));
		}

		const enterEvent = createKeyboardEvent('Enter');
		const handled = listener.handleKeydown(enterEvent);

		expect(handled).toBe(true);
		expect(enterEvent.preventDefault).toHaveBeenCalled();
		expect(onScan).toHaveBeenCalledWith('7791234567890');
		expect(listener.getBuffer()).toBe('');
	});

	it('resets buffer when keystrokes are slower than maxInterKeyDelayMs', () => {
		vi.useFakeTimers();
		try {
			const onScan = vi.fn();
			const listener = new HardwareScannerListener(onScan, {
				maxInterKeyDelayMs: 50,
			});

			listener.handleKeydown(createKeyboardEvent('A'));
			listener.handleKeydown(createKeyboardEvent('B'));
			expect(listener.getBuffer()).toBe('AB');

			// Advance time beyond maxInterKeyDelayMs
			vi.advanceTimersByTime(100);

			listener.handleKeydown(createKeyboardEvent('1'));
			expect(listener.getBuffer()).toBe('1');
		} finally {
			vi.useRealTimers();
		}
	});

	it('ignores Enter when buffer is shorter than minBarcodeLength', () => {
		const onScan = vi.fn();
		const listener = new HardwareScannerListener(onScan, {
			minBarcodeLength: 3,
		});

		listener.handleKeydown(createKeyboardEvent('1'));
		listener.handleKeydown(createKeyboardEvent('2'));

		const enterEvent = createKeyboardEvent('Enter');
		const handled = listener.handleKeydown(enterEvent);

		expect(handled).toBe(false);
		expect(onScan).not.toHaveBeenCalled();
		expect(listener.getBuffer()).toBe('');
	});

	it('ignores keystrokes when typing into an INPUT or TEXTAREA element', () => {
		const onScan = vi.fn();
		const listener = new HardwareScannerListener(onScan);

		const inputTarget = { tagName: 'INPUT' } as HTMLElement;
		listener.handleKeydown(createKeyboardEvent('1', inputTarget));
		listener.handleKeydown(createKeyboardEvent('2', inputTarget));
		listener.handleKeydown(createKeyboardEvent('Enter', inputTarget));

		expect(listener.getBuffer()).toBe('');
		expect(onScan).not.toHaveBeenCalled();

		const textareaTarget = { tagName: 'TEXTAREA' } as HTMLElement;
		listener.handleKeydown(createKeyboardEvent('X', textareaTarget));
		expect(listener.getBuffer()).toBe('');
	});

	it('ignores non-character multi-letter keys like Shift or Tab', () => {
		const onScan = vi.fn();
		const listener = new HardwareScannerListener(onScan);

		listener.handleKeydown(createKeyboardEvent('Shift'));
		listener.handleKeydown(createKeyboardEvent('Escape'));
		listener.handleKeydown(createKeyboardEvent('ArrowDown'));

		expect(listener.getBuffer()).toBe('');
	});

	it('resets buffer correctly with reset()', () => {
		const onScan = vi.fn();
		const listener = new HardwareScannerListener(onScan);

		listener.handleKeydown(createKeyboardEvent('A'));
		listener.handleKeydown(createKeyboardEvent('B'));
		expect(listener.getBuffer()).toBe('AB');

		listener.reset();
		expect(listener.getBuffer()).toBe('');
	});
});
