export function reportError(error: unknown, info?: any) {
	// Minimal centralized error reporting for now
	// Future: send to backend logging endpoint
	try {
		// eslint-disable-next-line no-console
		console.warn('[ErrorBoundary]', error, info);
	} catch {
		/* noop */
	}
}


