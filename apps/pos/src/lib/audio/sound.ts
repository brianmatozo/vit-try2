/**
 * Audio feedback module for Vitalcer POS.
 *
 * Supports user-provided audio files in /sounds/ (e.g. beep.mp3, error.mp3, success.mp3)
 * with graceful Web Audio API synthesis fallback and mobile vibration/haptics.
 */

let audioCtx: AudioContext | null = null;

function getAudioContext(): AudioContext | null {
	if (typeof window === 'undefined') return null;

	if (!audioCtx) {
		const AudioContextClass =
			window.AudioContext ||
			(window as unknown as { webkitAudioContext: typeof AudioContext })
				.webkitAudioContext;

		if (AudioContextClass) {
			audioCtx = new AudioContextClass();
		}
	}

	if (audioCtx && audioCtx.state === 'suspended') {
		audioCtx.resume().catch(() => {
			// Autoplay might prevent resume until direct user interaction
		});
	}

	return audioCtx;
}

/**
 * Triggers vibration haptic on supported mobile devices.
 */
function vibrate(pattern: number | number[]) {
	if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
		try {
			navigator.vibrate(pattern);
		} catch {
			// Ignore unsupported or blocked vibration
		}
	}
}

/**
 * Plays an audio file from static /sounds/ path, or runs synthesized fallback.
 */
async function playFileOrSynthesize(urls: string[], synthesizer: () => void) {
	if (typeof window === 'undefined') return;

	for (const url of urls) {
		try {
			const audio = new Audio(url);
			audio.volume = 0.8;
			await audio.play();
			return;
		} catch {
			// File not found or blocked, try next or fallback
		}
	}

	// Run Web Audio API synthesizer fallback
	try {
		synthesizer();
	} catch {
		// Audio context not allowed or failed
	}
}

/**
 * Cashier barcode scan success tone.
 */
export async function playBeep() {
	vibrate(40);

	await playFileOrSynthesize(['/sounds/beep.mp3', '/sounds/scan.mp3'], () => {
		const ctx = getAudioContext();
		if (!ctx) return;

		const now = ctx.currentTime;
		const osc = ctx.createOscillator();
		const gain = ctx.createGain();

		osc.type = 'sine';
		osc.frequency.setValueAtTime(1100, now);
		osc.frequency.exponentialRampToValueAtTime(1400, now + 0.06);

		gain.gain.setValueAtTime(0.25, now);
		gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);

		osc.connect(gain);
		gain.connect(ctx.destination);

		osc.start(now);
		osc.stop(now + 0.08);
	});
}

/**
 * Error / buzzer tone (e.g. unknown barcode, out of stock, validation error).
 */
export async function playError() {
	vibrate([80, 50, 80]);

	await playFileOrSynthesize(
		['/sounds/error.mp3', '/sounds/buzzer.mp3'],
		() => {
			const ctx = getAudioContext();
			if (!ctx) return;

			const now = ctx.currentTime;
			const osc = ctx.createOscillator();
			const gain = ctx.createGain();

			osc.type = 'sawtooth';
			osc.frequency.setValueAtTime(180, now);

			gain.gain.setValueAtTime(0.3, now);
			gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);

			osc.connect(gain);
			gain.connect(ctx.destination);

			osc.start(now);
			osc.stop(now + 0.22);
		},
	);
}

/**
 * Checkout / sale confirmed celebration chime.
 */
export async function playSuccess() {
	vibrate([60, 40, 60, 40, 100]);

	await playFileOrSynthesize(
		['/sounds/success.mp3', '/sounds/checkout.mp3'],
		() => {
			const ctx = getAudioContext();
			if (!ctx) return;

			const now = ctx.currentTime;
			// 4-note ascending chime
			const notes = [523.25, 659.25, 783.99, 1046.5];
			const duration = 0.1;

			notes.forEach((freq, index) => {
				const noteStart = now + index * 0.08;
				const osc = ctx.createOscillator();
				const gain = ctx.createGain();

				osc.type = 'triangle';
				osc.frequency.setValueAtTime(freq, noteStart);

				gain.gain.setValueAtTime(0.3, noteStart);
				gain.gain.exponentialRampToValueAtTime(0.001, noteStart + duration);

				osc.connect(gain);
				gain.connect(ctx.destination);

				osc.start(noteStart);
				osc.stop(noteStart + duration);
			});
		},
	);
}
