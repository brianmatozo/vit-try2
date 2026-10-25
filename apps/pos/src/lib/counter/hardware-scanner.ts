export interface HardwareScannerOptions {
	maxInterKeyDelayMs?: number;
	minBarcodeLength?: number;
}

export class HardwareScannerListener {
	private buffer = '';
	private lastKeyTime = 0;
	readonly maxInterKeyDelayMs: number;
	readonly minBarcodeLength: number;

	constructor(
		private onScan: (scannedCode: string) => void,
		options: HardwareScannerOptions = {},
	) {
		this.maxInterKeyDelayMs = options.maxInterKeyDelayMs ?? 200;
		this.minBarcodeLength = options.minBarcodeLength ?? 3;
	}

	handleKeydown(e: KeyboardEvent): boolean {
		// If cashier is typing in an input, textarea, or contenteditable element, ignore
		const target = e.target as HTMLElement | null;
		if (
			target &&
			(target.tagName === 'INPUT' ||
				target.tagName === 'TEXTAREA' ||
				target.isContentEditable)
		) {
			return false;
		}

		const now = Date.now();
		// Scanners fire keystrokes in rapid succession (< 50ms per key)
		if (now - this.lastKeyTime > this.maxInterKeyDelayMs) {
			this.buffer = '';
		}
		this.lastKeyTime = now;

		if (e.key === 'Enter') {
			const scannedCode = this.buffer.trim();
			if (scannedCode.length >= this.minBarcodeLength) {
				e.preventDefault();
				this.buffer = '';
				this.onScan(scannedCode);
				return true;
			}
			this.buffer = '';
		} else if (e.key.length === 1) {
			this.buffer += e.key;
		}

		return false;
	}

	getBuffer(): string {
		return this.buffer;
	}

	reset(): void {
		this.buffer = '';
		this.lastKeyTime = 0;
	}
}
