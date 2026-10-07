<script lang="ts">
import { BrowserMultiFormatReader } from '@zxing/browser';
import {
	AlertCircle,
	Camera,
	CameraOff,
	Flashlight,
	FlashlightOff,
	RefreshCw,
} from 'lucide-svelte';
import { onDestroy, onMount, untrack } from 'svelte';

interface Props {
	onscan: (barcode: string) => void;
	active?: boolean;
}

let { onscan, active = true }: Props = $props();

let videoElement = $state<HTMLVideoElement | null>(null);
let mediaStream = $state<MediaStream | null>(null);
let hasTorch = $state(false);
let isTorchOn = $state(false);
let cameraError = $state<string | null>(null);
let isScanning = $state(false);
let scanSuccessFlash = $state(false);
let lastScannedCode = $state<string | null>(null);
let lastScannedTime = $state<number>(0);
let facingMode = $state<'environment' | 'user'>('environment');

interface BarcodeDetectorResult {
	rawValue: string;
}

interface BarcodeDetectorInstance {
	detect: (image: ImageBitmapSource) => Promise<BarcodeDetectorResult[]>;
}

interface BarcodeDetectorConstructor {
	new (options?: { formats: string[] }): BarcodeDetectorInstance;
}

let zxingReader: BrowserMultiFormatReader | null = null;
let animationFrameId: number | null = null;
let nativeDetector: BarcodeDetectorInstance | null = null;
let startRequestId = 0;
let zxingControls: { stop: () => void } | null = null;

// Barcode detection formats
const BARCODE_FORMATS = [
	'ean_13',
	'ean_8',
	'code_128',
	'code_39',
	'upc_a',
	'upc_e',
	'qr_code',
];

function handleDetected(code: string) {
	const trimmed = code.trim();
	if (!trimmed) return;

	const now = Date.now();
	// Throttle: 1.5s for same code, 600ms for different code
	if (trimmed === lastScannedCode && now - lastScannedTime < 1500) {
		return;
	}
	if (now - lastScannedTime < 600) {
		return;
	}

	lastScannedCode = trimmed;
	lastScannedTime = now;

	// Visual flash
	scanSuccessFlash = true;
	setTimeout(() => {
		scanSuccessFlash = false;
	}, 400);

	onscan(trimmed);
}

async function startCamera() {
	const currentRequestId = ++startRequestId;
	stopCamera();
	cameraError = null;

	if (!videoElement) return;

	try {
		const constraints: MediaStreamConstraints = {
			video: {
				facingMode: { ideal: facingMode },
				width: { ideal: 1280 },
				height: { ideal: 720 },
			},
			audio: false,
		};

		if (!navigator?.mediaDevices?.getUserMedia) {
			if (typeof window !== 'undefined' && !window.isSecureContext) {
				cameraError =
					'La cámara requiere conexión HTTPS segura. Por favor accedé mediante https://...';
			} else {
				cameraError =
					'Tu navegador no soporta acceso a la cámara o no tiene permisos habilitados.';
			}
			isScanning = false;
			return;
		}

		const stream = await navigator.mediaDevices.getUserMedia(constraints);

		// If a new request occurred while waiting for getUserMedia, stop this stream
		if (currentRequestId !== startRequestId) {
			stream.getTracks().forEach((track) => {
				track.stop();
			});
			return;
		}

		mediaStream = stream;

		if (videoElement) {
			videoElement.srcObject = stream;
			try {
				await videoElement.play();
			} catch (playErr) {
				// AbortError is normal when play() is superseded by rapid changes or user agent pause
				if ((playErr as Error)?.name !== 'AbortError') {
					throw playErr;
				}
			}
		}

		if (currentRequestId !== startRequestId) return;

		// Check torch capability
		const track = stream.getVideoTracks()[0];
		if (track && typeof track.getCapabilities === 'function') {
			const caps = track.getCapabilities() as MediaTrackCapabilities & {
				torch?: boolean;
			};
			hasTorch = Boolean(caps.torch);
		} else {
			hasTorch = false;
		}

		isScanning = true;
		startDetectionLoop();
	} catch (err: unknown) {
		if (currentRequestId !== startRequestId) return;
		console.error('Camera access error:', err);
		const error = err as Error;
		if (
			error.name === 'NotAllowedError' ||
			error.name === 'PermissionDeniedError'
		) {
			cameraError =
				'Permiso denegado para acceder a la cámara. Por favor autorizá el uso de la cámara.';
		} else if (
			error.name === 'NotFoundError' ||
			error.name === 'DevicesNotFoundError'
		) {
			cameraError =
				'No se encontró ninguna cámara disponible en el dispositivo.';
		} else if (error.name === 'AbortError') {
			console.warn('Camera stream aborted by browser:', error);
			cameraError =
				'La conexión con la cámara fue interrumpida. Tocá "Reintentar Cámara".';
		} else {
			cameraError = `Error al iniciar la cámara: ${error.message || 'Error desconocido'}`;
		}
		isScanning = false;
	}
}

function stopCamera() {
	isScanning = false;
	if (animationFrameId !== null) {
		cancelAnimationFrame(animationFrameId);
		animationFrameId = null;
	}

	if (zxingControls) {
		try {
			zxingControls.stop();
		} catch {}
		zxingControls = null;
	}
	zxingReader = null;

	if (mediaStream) {
		mediaStream.getTracks().forEach((track) => {
			try {
				track.stop();
			} catch {}
		});
		mediaStream = null;
	}

	if (videoElement) {
		videoElement.srcObject = null;
	}
	hasTorch = false;
	isTorchOn = false;
}

async function toggleTorch() {
	if (!mediaStream || !hasTorch) return;
	const track = mediaStream.getVideoTracks()[0];
	if (!track) return;

	try {
		isTorchOn = !isTorchOn;
		await track.applyConstraints({
			advanced: [{ torch: isTorchOn } as MediaTrackConstraintSet],
		});
	} catch (err) {
		console.warn('Failed to toggle torch:', err);
		isTorchOn = false;
	}
}

function switchCamera() {
	facingMode = facingMode === 'environment' ? 'user' : 'environment';
	startCamera();
}

function startDetectionLoop() {
	if (typeof window === 'undefined') return;

	// 1. Check for native BarcodeDetector API (fastest, native GPU accelerated)
	if ('BarcodeDetector' in window) {
		try {
			const BarcodeDetectorClass = (
				window as unknown as { BarcodeDetector: BarcodeDetectorConstructor }
			).BarcodeDetector;
			const detector = new BarcodeDetectorClass({
				formats: BARCODE_FORMATS,
			});
			nativeDetector = detector;

			const detectFrame = async () => {
				if (!isScanning || !videoElement || videoElement.readyState < 2) {
					animationFrameId = requestAnimationFrame(detectFrame);
					return;
				}

				try {
					const barcodes = await detector.detect(videoElement);
					if (barcodes && barcodes.length > 0) {
						for (const barcode of barcodes) {
							if (barcode.rawValue) {
								handleDetected(barcode.rawValue);
								break;
							}
						}
					}
				} catch {}

				if (isScanning) {
					animationFrameId = requestAnimationFrame(detectFrame);
				}
			};

			animationFrameId = requestAnimationFrame(detectFrame);
			return;
		} catch (e) {
			console.warn(
				'BarcodeDetector failed to initialize, falling back to ZXing',
				e,
			);
		}
	}

	// 2. Fallback to @zxing/browser
	try {
		if (!videoElement) return;
		zxingReader = new BrowserMultiFormatReader();
		zxingReader
			.decodeFromVideoElement(videoElement, (result) => {
				if (result) {
					handleDetected(result.getText());
				}
			})
			.then((controls) => {
				zxingControls = controls;
			})
			.catch((err) => {
				console.warn('ZXing decodeFromVideoElement failed:', err);
			});
	} catch (err) {
		console.error('ZXing initialization failed:', err);
	}
}

$effect(() => {
	const shouldBeActive = active;
	untrack(() => {
		if (shouldBeActive) {
			startCamera();
		} else {
			stopCamera();
		}
	});

	return () => {
		untrack(() => {
			stopCamera();
		});
	};
});

onDestroy(() => {
	stopCamera();
});
</script>

<div class="relative w-full overflow-hidden rounded-2xl bg-black shadow-lg border border-neutral-800">
	<!-- Video Element -->
	<video
		bind:this={videoElement}
		playsinline
		muted
		autoplay
		class="w-full h-48 sm:h-56 object-cover"
	></video>

	<!-- Reticle Overlay -->
	{#if isScanning && !cameraError}
		<div class="absolute inset-0 pointer-events-none flex items-center justify-center p-4">
			<!-- Visual flash on successful scan -->
			{#if scanSuccessFlash}
				<div class="absolute inset-0 bg-emerald-500/30 transition-opacity duration-300"></div>
			{/if}

			<!-- Bounding box with corner accents -->
			<div class="relative w-4/5 max-w-[280px] h-28 border-2 border-dashed border-emerald-400/70 rounded-xl flex items-center justify-center">
				<!-- Corner brackets -->
				<div class="absolute -top-1 -left-1 w-4 h-4 border-t-2 border-l-2 border-emerald-400"></div>
				<div class="absolute -top-1 -right-1 w-4 h-4 border-t-2 border-r-2 border-emerald-400"></div>
				<div class="absolute -bottom-1 -left-1 w-4 h-4 border-b-2 border-l-2 border-emerald-400"></div>
				<div class="absolute -bottom-1 -right-1 w-4 h-4 border-b-2 border-r-2 border-emerald-400"></div>

				<!-- Laser animation line -->
				<div class="w-full h-0.5 bg-gradient-to-r from-transparent via-emerald-400 to-transparent shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse"></div>
			</div>
		</div>

		<!-- Scanner controls overlay -->
		<div class="absolute bottom-2 inset-x-2 flex items-center justify-between pointer-events-auto">
			<!-- Status Pill -->
			<div class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md text-[11px] font-medium text-emerald-400 border border-emerald-500/20">
				<span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
				<span>Apuntar al código</span>
			</div>

			<!-- Quick Action Buttons -->
			<div class="flex items-center gap-2">
				{#if hasTorch}
					<button
						type="button"
						onclick={toggleTorch}
						class="p-2 rounded-full bg-black/60 backdrop-blur-md text-white hover:bg-neutral-800 transition active:scale-95 border border-white/10"
						aria-label={isTorchOn ? 'Apagar linterna' : 'Encender linterna'}
					>
						{#if isTorchOn}
							<Flashlight class="w-4 h-4 text-amber-400 fill-amber-400" />
						{:else}
							<FlashlightOff class="w-4 h-4 text-neutral-400" />
						{/if}
					</button>
				{/if}

				<button
					type="button"
					onclick={switchCamera}
					class="p-2 rounded-full bg-black/60 backdrop-blur-md text-white hover:bg-neutral-800 transition active:scale-95 border border-white/10"
					aria-label="Cambiar cámara"
				>
					<RefreshCw class="w-4 h-4 text-neutral-300" />
				</button>
			</div>
		</div>
	{/if}

	<!-- Error State -->
	{#if cameraError}
		<div class="absolute inset-0 bg-neutral-900/95 flex flex-col items-center justify-center p-6 text-center text-white">
			<AlertCircle class="w-10 h-10 text-rose-400 mb-2" />
			<p class="text-sm font-medium text-neutral-200 mb-3">{cameraError}</p>
			<button
				type="button"
				onclick={startCamera}
				class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white text-xs font-semibold rounded-xl shadow-md transition"
			>
				Reintentar Cámara
			</button>
		</div>
	{/if}
</div>
