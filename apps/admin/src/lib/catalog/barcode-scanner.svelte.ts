import {
	BARCODE_FORMATS,
	mapCameraError,
	playScanChime,
} from './barcode-scanner-utils';

export {
	BARCODE_FORMATS,
	mapCameraError,
	playScanChime,
} from './barcode-scanner-utils';

export interface BarcodeScannerOptions {
	onscan?: (barcode: string) => void;
	singleShot?: boolean;
}

export class BarcodeScannerController {
	videoElement = $state<HTMLVideoElement | null>(null);
	mediaStream = $state<MediaStream | null>(null);
	hasTorch = $state(false);
	isTorchOn = $state(false);
	cameraError = $state<string | null>(null);
	isScanning = $state(false);
	scanSuccessFlash = $state(false);
	facingMode = $state<'environment' | 'user'>('environment');

	onscan: (barcode: string) => void;
	singleShot: boolean;

	private startRequestId = 0;
	private animationFrameId: number | null = null;
	private zxingControls: { stop: () => void } | null = null;

	constructor(options?: BarcodeScannerOptions) {
		this.onscan = options?.onscan ?? (() => {});
		this.singleShot = options?.singleShot ?? true;
	}

	handleDetected(code: string): boolean {
		const trimmed = code.trim();
		if (!trimmed) return false;

		this.scanSuccessFlash = true;
		playScanChime();
		this.onscan(trimmed);

		if (this.singleShot) {
			this.stopCamera();
		}
		return true;
	}

	async startCamera(): Promise<void> {
		const currentRequestId = ++this.startRequestId;
		this.stopCamera();
		this.cameraError = null;
		if (!this.videoElement) return;

		try {
			if (!navigator?.mediaDevices?.getUserMedia) {
				this.cameraError = mapCameraError(
					new Error('MediaDevices not supported'),
				);
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
			this.videoElement.srcObject = stream;
			try {
				await this.videoElement.play();
			} catch (playErr) {
				if ((playErr as Error)?.name !== 'AbortError') throw playErr;
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
		} catch {
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

		// 1. Native BarcodeDetector (Zero overhead, hardware accelerated)
		if ('BarcodeDetector' in window) {
			try {
				const BarcodeDetectorClass = (
					window as unknown as {
						BarcodeDetector: new (opts: {
							formats: string[];
						}) => {
							detect: (
								source: ImageBitmapSource,
							) => Promise<Array<{ rawValue: string }>>;
						};
					}
				).BarcodeDetector;

				const detector = new BarcodeDetectorClass({ formats: BARCODE_FORMATS });

				const detectFrame = async () => {
					if (
						!this.isScanning ||
						!this.videoElement ||
						this.videoElement.readyState < 2
					) {
						if (this.isScanning) {
							this.animationFrameId = requestAnimationFrame(detectFrame);
						}
						return;
					}
					try {
						const barcodes = await detector.detect(this.videoElement);
						if (barcodes?.[0]?.rawValue) {
							this.handleDetected(barcodes[0].rawValue);
							return;
						}
					} catch {}

					if (this.isScanning) {
						this.animationFrameId = requestAnimationFrame(detectFrame);
					}
				};

				this.animationFrameId = requestAnimationFrame(detectFrame);
				return;
			} catch {}
		}

		// 2. On-demand dynamic import of ZXing fallback (only loaded when needed)
		import('@zxing/browser')
			.then(({ BrowserMultiFormatReader }) => {
				if (!this.isScanning || !this.videoElement) return;
				const reader = new BrowserMultiFormatReader();
				reader
					.decodeFromVideoElement(this.videoElement, (result) => {
						if (result?.getText()) {
							this.handleDetected(result.getText());
						}
					})
					.then((controls) => {
						this.zxingControls = controls;
					})
					.catch(() => {});
			})
			.catch(() => {});
	}

	destroy(): void {
		this.stopCamera();
	}
}
