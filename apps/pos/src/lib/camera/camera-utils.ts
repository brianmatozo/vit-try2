export interface BarcodeDetectorResult {
	rawValue: string;
}

export interface BarcodeDetectorInstance {
	detect: (image: ImageBitmapSource) => Promise<BarcodeDetectorResult[]>;
}

export interface BarcodeDetectorConstructor {
	new (options?: { formats: string[] }): BarcodeDetectorInstance;
}

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
	const error = err as Error;
	if (
		error.name === 'NotAllowedError' ||
		error.name === 'PermissionDeniedError'
	) {
		return 'Permiso denegado para acceder a la cámara. Por favor autorizá el uso de la cámara.';
	}
	if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
		return 'No se encontró ninguna cámara disponible en el dispositivo.';
	}
	if (error.name === 'AbortError') {
		return 'La conexión con la cámara fue interrumpida. Tocá "Reintentar Cámara".';
	}
	return `Error al iniciar la cámara: ${error.message || 'Error desconocido'}`;
}
