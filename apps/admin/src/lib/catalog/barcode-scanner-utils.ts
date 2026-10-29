export const BARCODE_FORMATS = [
	'ean_13',
	'ean_8',
	'code_128',
	'code_39',
	'upc_a',
	'upc_e',
	'qr_code',
];

export function mapCameraError(err: unknown): string {
	if (typeof window !== 'undefined' && !window.isSecureContext) {
		return 'La cámara requiere conexión HTTPS segura o localhost.';
	}
	const error = err as Error;
	if (
		error.name === 'NotAllowedError' ||
		error.name === 'PermissionDeniedError'
	) {
		return 'Permiso denegado para acceder a la cámara. Habilitá los permisos en el navegador.';
	}
	if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
		return 'No se detectó ninguna cámara disponible en este dispositivo.';
	}
	if (error.name === 'AbortError') {
		return 'La conexión con la cámara fue interrumpida. Reintentar.';
	}
	return `Error al iniciar cámara: ${error.message || 'Error desconocido'}`;
}

export function playScanChime(): void {
	if (typeof window === 'undefined') return;
	try {
		const AudioCtx =
			window.AudioContext ||
			(window as unknown as { webkitAudioContext: typeof AudioContext })
				.webkitAudioContext;
		if (!AudioCtx) return;
		const ctx = new AudioCtx();
		const now = ctx.currentTime;
		const osc = ctx.createOscillator();
		const gain = ctx.createGain();

		osc.type = 'sine';
		osc.frequency.setValueAtTime(1200, now);
		osc.frequency.exponentialRampToValueAtTime(1600, now + 0.07);

		gain.gain.setValueAtTime(0.2, now);
		gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);

		osc.connect(gain);
		gain.connect(ctx.destination);

		osc.start(now);
		osc.stop(now + 0.08);

		if ('vibrate' in navigator) {
			try {
				navigator.vibrate(40);
			} catch {}
		}
	} catch {}
}
