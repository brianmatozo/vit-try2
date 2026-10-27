/**
 * Structured API error result.
 */
export interface ApiErrorResult {
	message: string;
	code?: string;
	raw?: unknown;
}

/**
 * Extracts a user-facing error message and optional machine-readable error code
 * from any API error response, network error, or unexpected exception.
 *
 * Handles:
 * 1. Vitalcer backend domain exceptions: `{ detail: string, code?: string }`
 * 2. FastAPI 422 Unprocessable Entity: `{ detail: Array<{ msg: string, loc?: (string | number)[] }> }`
 * 3. Standard JS Error instances: `new Error("...")`
 * 4. Unknown string / object payloads with fallback
 */
export function extractApiError(
	error: unknown,
	fallback = 'Error inesperado del servidor',
): ApiErrorResult {
	if (!error) {
		return { message: fallback };
	}

	if (typeof error === 'string') {
		return { message: error, raw: error };
	}

	if (typeof error === 'object' && error !== null) {
		const errObj = error as Record<string, unknown>;
		const code = typeof errObj.code === 'string' ? errObj.code : undefined;

		// Case 1: detail is a string (standard FastAPI HTTPException or VitalcerException)
		if (typeof errObj.detail === 'string') {
			return {
				message: errObj.detail,
				code,
				raw: error,
			};
		}

		// Case 2: detail is an array (FastAPI 422 validation error)
		if (Array.isArray(errObj.detail)) {
			const messages = errObj.detail
				.map((item) => {
					if (typeof item === 'string') return item;
					if (item && typeof item === 'object') {
						const valItem = item as { msg?: unknown; loc?: unknown };
						if (typeof valItem.msg === 'string') {
							if (Array.isArray(valItem.loc) && valItem.loc.length > 0) {
								// Strip root 'body' prefix if present for cleaner user messages
								const locParts = valItem.loc
									.filter((loc) => loc !== 'body')
									.join('.');
								return locParts ? `${locParts}: ${valItem.msg}` : valItem.msg;
							}
							return valItem.msg;
						}
					}
					return null;
				})
				.filter((msg): msg is string => Boolean(msg));

			if (messages.length > 0) {
				return {
					message: messages.join('; '),
					code: code ?? 'VALIDATION_ERROR',
					raw: error,
				};
			}
		}

		// Case 3: Standard JS Error with message property
		if (typeof errObj.message === 'string' && errObj.message.trim()) {
			return {
				message: errObj.message,
				code,
				raw: error,
			};
		}
	}

	return { message: fallback, raw: error };
}

/**
 * Convenience helper returning solely the human-readable error string.
 */
export function getApiErrorMessage(error: unknown, fallback?: string): string {
	return extractApiError(error, fallback).message;
}
