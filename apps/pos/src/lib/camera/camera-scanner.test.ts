import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CameraScannerController } from './camera-scanner.svelte';

vi.mock('$lib/audio/sound', () => ({
	playBeep: vi.fn().mockReturnValue(Promise.resolve()),
	playError: vi.fn().mockReturnValue(Promise.resolve()),
}));

describe('CameraScannerController', () => {
	const createMockVideoElement = () =>
		({
			play: vi.fn().mockResolvedValue(undefined),
			srcObject: null,
			readyState: 2,
		}) as unknown as HTMLVideoElement;

	beforeEach(() => {
		vi.useFakeTimers();
	});

	afterEach(() => {
		vi.useRealTimers();
		vi.clearAllMocks();
	});

	it('initializes with default idle state', () => {
		const scanner = new CameraScannerController();
		expect(scanner.isScanning).toBe(false);
		expect(scanner.hasTorch).toBe(false);
		expect(scanner.isTorchOn).toBe(false);
		expect(scanner.cameraError).toBeNull();
		expect(scanner.facingMode).toBe('environment');
		expect(scanner.lastScannedCode).toBeNull();
	});

	describe('handleDetected and throttling', () => {
		it('processes valid barcode and triggers onscan callback', () => {
			const onscan = vi.fn();
			const scanner = new CameraScannerController({ onscan });

			const accepted = scanner.handleDetected('7791234567890');
			expect(accepted).toBe(true);
			expect(onscan).toHaveBeenCalledWith('7791234567890');
			expect(scanner.lastScannedCode).toBe('7791234567890');
			expect(scanner.scanSuccessFlash).toBe(true);

			vi.advanceTimersByTime(400);
			expect(scanner.scanSuccessFlash).toBe(false);
		});

		it('ignores empty or whitespace codes', () => {
			const onscan = vi.fn();
			const scanner = new CameraScannerController({ onscan });

			expect(scanner.handleDetected('')).toBe(false);
			expect(scanner.handleDetected('   ')).toBe(false);
			expect(onscan).not.toHaveBeenCalled();
		});

		it('throttles identical barcode scanned within 1500ms', () => {
			const onscan = vi.fn();
			const scanner = new CameraScannerController({ onscan });

			scanner.handleDetected('7791234567890');
			expect(onscan).toHaveBeenCalledTimes(1);

			// Immediate repeat scan
			const repeatScan = scanner.handleDetected('7791234567890');
			expect(repeatScan).toBe(false);
			expect(onscan).toHaveBeenCalledTimes(1);

			// After 1000ms (still within 1500ms window)
			vi.advanceTimersByTime(1000);
			expect(scanner.handleDetected('7791234567890')).toBe(false);
			expect(onscan).toHaveBeenCalledTimes(1);

			// After 1600ms (window expired)
			vi.advanceTimersByTime(600);
			expect(scanner.handleDetected('7791234567890')).toBe(true);
			expect(onscan).toHaveBeenCalledTimes(2);
		});

		it('throttles different barcode scanned within 600ms', () => {
			const onscan = vi.fn();
			const scanner = new CameraScannerController({ onscan });

			scanner.handleDetected('CODE-A');
			expect(onscan).toHaveBeenCalledTimes(1);

			// Scanned after 200ms
			vi.advanceTimersByTime(200);
			expect(scanner.handleDetected('CODE-B')).toBe(false);
			expect(onscan).toHaveBeenCalledTimes(1);

			// Scanned after 650ms total
			vi.advanceTimersByTime(450);
			expect(scanner.handleDetected('CODE-B')).toBe(true);
			expect(onscan).toHaveBeenCalledTimes(2);
		});
	});

	describe('state transitions', () => {
		it('switches facing mode between environment and user', () => {
			const scanner = new CameraScannerController();
			const startSpy = vi.spyOn(scanner, 'startCamera').mockResolvedValue();

			expect(scanner.facingMode).toBe('environment');
			scanner.switchCamera();
			expect(scanner.facingMode).toBe('user');
			expect(startSpy).toHaveBeenCalledTimes(1);

			scanner.switchCamera();
			expect(scanner.facingMode).toBe('environment');
			expect(startSpy).toHaveBeenCalledTimes(2);
		});

		it('stops camera and resets hardware track flags', () => {
			const scanner = new CameraScannerController();
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
			const scanner = new CameraScannerController();
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
	});

	describe('error handling and decoder fallback', () => {
		it('sets permission error on NotAllowedError', async () => {
			const scanner = new CameraScannerController();
			scanner.videoElement = createMockVideoElement();

			const notAllowed = new Error('Permission denied');
			notAllowed.name = 'NotAllowedError';

			const getUserMedia = vi.fn().mockRejectedValue(notAllowed);
			vi.stubGlobal('navigator', {
				mediaDevices: { getUserMedia },
			});

			await scanner.startCamera();

			expect(scanner.cameraError).toContain('Permiso denegado');
			expect(scanner.isScanning).toBe(false);
		});

		it('falls back to ZXing when BarcodeDetector is not present', () => {
			const scanner = new CameraScannerController();
			scanner.videoElement = createMockVideoElement();
			scanner.isScanning = true;

			vi.stubGlobal('window', {});

			scanner.startDetectionLoop();

			// ZXing reader was instantiated
			expect(
				(scanner as unknown as { zxingReader: unknown }).zxingReader,
			).not.toBeNull();
		});
	});
});
