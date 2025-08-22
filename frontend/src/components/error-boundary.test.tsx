import React from 'react';
import { render, screen } from '@testing-library/react';
import { ErrorBoundary } from './error-boundary';

function Boom() {
	throw new Error('boom');
	return null; // This line will never be reached
}

describe('ErrorBoundary', () => {
	let consoleErrorSpy: jest.SpyInstance;
	let consoleWarnSpy: jest.SpyInstance;

	beforeEach(() => {
		consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
		consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
	});

	afterEach(() => {
		consoleErrorSpy.mockRestore();
		consoleWarnSpy.mockRestore();
	});
	it('renders fallback when child throws', () => {
		render(
			<ErrorBoundary title="Section error">
				<Boom />
			</ErrorBoundary>
		);
		expect(screen.getByText(/Section error/i)).toBeInTheDocument();
		expect(screen.getByText(/boom/i)).toBeInTheDocument();
		expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
		// reporter called once with error + info
		expect(consoleWarnSpy).toHaveBeenCalledTimes(1);
	});

	it('renders custom fallback element when provided', () => {
		const custom = <div role="alert">Custom Fallback</div>;
		render(
			<ErrorBoundary fallback={custom}>
				<Boom />
			</ErrorBoundary>
		);
		expect(screen.getByRole('alert')).toHaveTextContent('Custom Fallback');
	});
});


