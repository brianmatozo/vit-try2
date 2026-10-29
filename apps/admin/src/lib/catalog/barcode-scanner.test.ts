import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { BarcodeScannerController } from './barcode-scanner.svelte';
import { mapCameraError } from './barcode-scanner-utils';

vi.mock('./barcode-scanner-utils', async (importOriginal) => {
	const actual = (await importOriginal()) as Record<string, unknown>;
	return {
		...actual,
		playScanChime: vi.fn(),
	};
});

describe('BarcodeScannerController', () => {
	beforeEach(() => {
		vi.useFakeTimers();
	});

	afterEach(() => {
		vi.useRealTimers();
		vi.clearAllMocks();
	});

	it('initializes with default single-shot state', () => {
		const scanner = new BarcodeScannerController();
		expect(scanner.isScanning).toBe(false);
		expect(scanner.hasTorch).toBe(false);
		expect(scanner.isTorchOn).toBe(false);
		expect(scanner.cameraError).toBeNull();
		expect(scanner.facingMode).toBe('environment');
		expect(scanner.singleShot).toBe(true);
	});

	describe('handleDetected and single-shot behavior', () => {
		it('processes valid barcode, triggers onscan callback, and stops camera in single-shot mode', () => {
			const onscan = vi.fn();
			const scanner = new BarcodeScannerController({
				onscan,
				singleShot: true,
			});
			const stopSpy = vi.spyOn(scanner, 'stopCamera');

			const accepted = scanner.handleDetected('7791234567890');
			expect(accepted).toBe(true);
			expect(onscan).toHaveBeenCalledWith('7791234567890');
			expect(scanner.scanSuccessFlash).toBe(true);
			expect(stopSpy).toHaveBeenCalledTimes(1);
		});

		it('ignores empty or whitespace barcode', () => {
			const onscan = vi.fn();
			const scanner = new BarcodeScannerController({ onscan });
			const stopSpy = vi.spyOn(scanner, 'stopCamera');

			expect(scanner.handleDetected('')).toBe(false);
			expect(scanner.handleDetected('   ')).toBe(false);
			expect(onscan).not.toHaveBeenCalled();
			expect(stopSpy).not.toHaveBeenCalled();
		});

		it('does not stop camera when singleShot is false', () => {
			const onscan = vi.fn();
			const scanner = new BarcodeScannerController({
				onscan,
				singleShot: false,
			});
			const stopSpy = vi.spyOn(scanner, 'stopCamera');

			const accepted = scanner.handleDetected('7791234567890');
			expect(accepted).toBe(true);
			expect(onscan).toHaveBeenCalledWith('7791234567890');
			expect(stopSpy).not.toHaveBeenCalled();
		});
	});

	describe('state transitions and hardware control', () => {
		it('switches facing mode between environment and user', () => {
			const scanner = new BarcodeScannerController();
			const startSpy = vi.spyOn(scanner, 'startCamera').mockResolvedValue();

			expect(scanner.facingMode).toBe('environment');
			scanner.switchCamera();
			expect(scanner.facingMode).toBe('user');
			expect(startSpy).toHaveBeenCalledTimes(1);

			scanner.switchCamera();
			expect(scanner.facingMode).toBe('environment');
			expect(startSpy).toHaveBeenCalledTimes(2);
		});

		it('stops camera and cleans up stream tracks', () => {
			const scanner = new BarcodeScannerController();
			const stopTrack = vi.fn();
			const mockStream = {
				getTracks: () => [{ stop: stopTrack } as unknown as MediaStreamTrack],
			} as unknown as MediaStream;

			scanner.mediaStream = mockStream;
			scanner.isScanning = true;
			scanner.hasTorch = true;
			scanner.isTorchOn = true;

			scanner.stopCamera();

			expect(stopTrack).toHaveBeenCalled();
			expect(scanner.mediaStream).toBeNull();
			expect(scanner.isScanning).toBe(false);
			expect(scanner.hasTorch).toBe(false);
			expect(scanner.isTorchOn).toBe(false);
		});

		it('toggles torch on supported tracks', async () => {
			const scanner = new BarcodeScannerController();
			const applyConstraints = vi.fn().mockResolvedValue(undefined);
			const mockTrack = {
				applyConstraints,
			} as unknown as MediaTrackCapabilities;

			scanner.hasTorch = true;
			scanner.mediaStream = {
				getVideoTracks: () => [mockTrack],
			} as unknown as MediaStream;

			await scanner.toggleTorch();
			expect(scanner.isTorchOn).toBe(true);
			expect(applyConstraints).toHaveBeenCalledWith({
				advanced: [{ torch: true }],
			});

			await scanner.toggleTorch();
			expect(scanner.isTorchOn).toBe(false);
			expect(applyConstraints).toHaveBeenCalledWith({
				advanced: [{ torch: false }],
			});
		});

		it('destroy invokes stopCamera', () => {
			const scanner = new BarcodeScannerController();
			const stopSpy = vi.spyOn(scanner, 'stopCamera');
			scanner.destroy();
			expect(stopSpy).toHaveBeenCalledTimes(1);
		});
	});

	describe('mapCameraError', () => {
		it('maps NotAllowedError to user-friendly Spanish message', () => {
			const err = new Error('Permission denied');
			err.name = 'NotAllowedError';
			expect(mapCameraError(err)).toContain('Permiso denegado');
		});

		it('maps NotFoundError to device not found message', () => {
			const err = new Error('Devices not found');
			err.name = 'NotFoundError';
			expect(mapCameraError(err)).toContain('No se detectó ninguna cámara');
		});

		it('handles generic unknown errors', () => {
			const err = new Error('Hardware boom');
			expect(mapCameraError(err)).toContain('Hardware boom');
		});
	});
});
