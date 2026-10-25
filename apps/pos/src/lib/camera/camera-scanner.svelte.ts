import { BrowserMultiFormatReader } from '@zxing/browser';
import { playBeep, playError } from '$lib/audio/sound';
import {
	BARCODE_FORMATS,
	type BarcodeDetectorConstructor,
	mapCameraError,
} from './camera-utils';

export {
	BARCODE_FORMATS,
	type BarcodeDetectorConstructor,
	type BarcodeDetectorInstance,
	type BarcodeDetectorResult,
	mapCameraError,
} from './camera-utils';

export class CameraScannerController {
	videoElement = $state<HTMLVideoElement | null>(null);
	mediaStream = $state<MediaStream | null>(null);
	hasTorch = $state(false);
	isTorchOn = $state(false);
	cameraError = $state<string | null>(null);
	isScanning = $state(false);
	scanSuccessFlash = $state(false);
	lastScannedCode = $state<string | null>(null);
	lastScannedTime = $state(0);
	facingMode = $state<'environment' | 'user'>('environment');

	onscan: (barcode: string) => void;

	private startRequestId = 0;
	private animationFrameId: number | null = null;
	private zxingReader: BrowserMultiFormatReader | null = null;
	private zxingControls: { stop: () => void } | null = null;
	private flashTimeoutId: ReturnType<typeof setTimeout> | null = null;

	constructor(options?: { onscan?: (barcode: string) => void }) {
		this.onscan = options?.onscan ?? (() => {});
	}

	handleDetected(code: string): boolean {
		const trimmed = code.trim();
		if (!trimmed) return false;

		const now = Date.now();
		if (trimmed === this.lastScannedCode && now - this.lastScannedTime < 1500)
			return false;
		if (now - this.lastScannedTime < 600) return false;

		this.lastScannedCode = trimmed;
		this.lastScannedTime = now;

		this.scanSuccessFlash = true;
		if (this.flashTimeoutId) clearTimeout(this.flashTimeoutId);
		this.flashTimeoutId = setTimeout(() => {
			this.scanSuccessFlash = false;
			this.flashTimeoutId = null;
		}, 400);

		try {
			playBeep()?.catch?.(() => {});
		} catch {}
		this.onscan(trimmed);
		return true;
	}

	async startCamera(): Promise<void> {
		const currentRequestId = ++this.startRequestId;
		this.stopCamera();
		this.cameraError = null;
		if (!this.videoElement) return;

		try {
			if (!navigator?.mediaDevices?.getUserMedia) {
				const isSec = typeof window !== 'undefined' && !window.isSecureContext;
				this.cameraError = isSec
					? 'La cámara requiere conexión HTTPS segura. Por favor accedé mediante https://...'
					: 'Tu navegador no soporta acceso a la cámara o no tiene permisos habilitados.';
				try {
					playError()?.catch?.(() => {});
				} catch {}
				return;
			}

			const stream = await navigator.mediaDevices.getUserMedia({
				video: {
					facingMode: { ideal: this.facingMode },
					width: { ideal: 1280 },
					height: { ideal: 720 },
				},
				audio: false,
			});

			if (currentRequestId !== this.startRequestId) {
				stream.getTracks().forEach((track) => {
					track.stop();
				});
				return;
			}

			this.mediaStream = stream;
			if (this.videoElement) {
				this.videoElement.srcObject = stream;
				try {
					await this.videoElement.play();
				} catch (playErr) {
					if ((playErr as Error)?.name !== 'AbortError') throw playErr;
				}
			}

			if (currentRequestId !== this.startRequestId) return;

			const track = stream.getVideoTracks()[0];
			const caps =
				track && typeof track.getCapabilities === 'function'
					? (track.getCapabilities() as MediaTrackCapabilities & {
							torch?: boolean;
						})
					: null;
			this.hasTorch = Boolean(caps?.torch);

			this.isScanning = true;
			this.startDetectionLoop();
		} catch (err: unknown) {
			if (currentRequestId !== this.startRequestId) return;
			console.error('Camera access error:', err);
			try {
				playError()?.catch?.(() => {});
			} catch {}
			this.cameraError = mapCameraError(err);
			this.isScanning = false;
		}
	}

	stopCamera(): void {
		this.isScanning = false;
		if (this.animationFrameId !== null) {
			cancelAnimationFrame(this.animationFrameId);
			this.animationFrameId = null;
		}
		if (this.zxingControls) {
			try {
				this.zxingControls.stop();
			} catch {}
			this.zxingControls = null;
		}
		this.zxingReader = null;
		if (this.mediaStream) {
			this.mediaStream.getTracks().forEach((track) => {
				try {
					track.stop();
				} catch {}
			});
			this.mediaStream = null;
		}
		if (this.videoElement) {
			this.videoElement.srcObject = null;
		}
		this.hasTorch = false;
		this.isTorchOn = false;
	}

	async toggleTorch(): Promise<void> {
		if (!this.mediaStream || !this.hasTorch) return;
		const track = this.mediaStream.getVideoTracks()[0];
		if (!track) return;
		try {
			this.isTorchOn = !this.isTorchOn;
			await track.applyConstraints({
				advanced: [{ torch: this.isTorchOn } as MediaTrackConstraintSet],
			});
		} catch (err) {
			console.warn('Failed to toggle torch:', err);
			this.isTorchOn = false;
		}
	}

	switchCamera(): void {
		this.facingMode =
			this.facingMode === 'environment' ? 'user' : 'environment';
		this.startCamera();
	}

	startDetectionLoop(): void {
		if (typeof window === 'undefined') return;

		if ('BarcodeDetector' in window) {
			try {
				const BarcodeDetectorClass = (
					window as unknown as {
						BarcodeDetector: BarcodeDetectorConstructor;
					}
				).BarcodeDetector;
				const detector = new BarcodeDetectorClass({
					formats: BARCODE_FORMATS,
				});

				const detectFrame = async () => {
					if (
						!this.isScanning ||
						!this.videoElement ||
						this.videoElement.readyState < 2
					) {
						if (this.isScanning)
							this.animationFrameId = requestAnimationFrame(detectFrame);
						return;
					}
					try {
						const barcodes = await detector.detect(this.videoElement);
						if (barcodes?.[0]?.rawValue) {
							this.handleDetected(barcodes[0].rawValue);
						}
					} catch {}

					if (this.isScanning)
						this.animationFrameId = requestAnimationFrame(detectFrame);
				};

				this.animationFrameId = requestAnimationFrame(detectFrame);
				return;
			} catch (e) {
				console.warn('BarcodeDetector fallback to ZXing', e);
			}
		}

		try {
			if (!this.videoElement) return;
			this.zxingReader = new BrowserMultiFormatReader();
			this.zxingReader
				.decodeFromVideoElement(this.videoElement, (result) => {
					if (result) this.handleDetected(result.getText());
				})
				.then((controls) => {
					this.zxingControls = controls;
				})
				.catch((err) => console.warn('ZXing failed:', err));
		} catch (err) {
			console.error('ZXing init failed:', err);
		}
	}

	destroy(): void {
		this.stopCamera();
		if (this.flashTimeoutId) {
			clearTimeout(this.flashTimeoutId);
			this.flashTimeoutId = null;
		}
	}
}
