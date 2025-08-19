'use client';

import React from 'react';
import { reportError } from '../lib/error-reporting';

/**
 * ErrorBoundary
 *
 * Usage:
 *
 * Wrap crash‑prone sections so a failure does not take down the whole page.
 *
 * Example:
 *
 *  <ErrorBoundary title="Dashboard section error">
 *    <DashboardWidgets />
 *  </ErrorBoundary>
 *
 * Optional:
 *  - Provide a custom fallback element via `fallback`
 *  - Provide `onReset` to run side effects when user clicks "Try Again"
 */
type ErrorBoundaryProps = {
	children: React.ReactNode;
	title?: string;
	fallback?: React.ReactNode;
	onReset?: () => void;
};

type ErrorBoundaryState = {
	hasError: boolean;
	error: Error | null;
	resetKey: number;
};

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
	constructor(props: ErrorBoundaryProps) {
		super(props);
		this.state = { hasError: false, error: null, resetKey: 0 };
	}

	static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
		return { hasError: true, error };
	}

	componentDidCatch(error: Error, info: React.ErrorInfo) {
		// Centralized reporting (console for now)
		reportError(error, { componentStack: info.componentStack });
	}

	private handleReset = () => {
		this.setState(prev => ({ hasError: false, error: null, resetKey: prev.resetKey + 1 }));
		if (this.props.onReset) this.props.onReset();
	};

	render() {
		if (this.state.hasError) {
			if (this.props.fallback) return <>{this.props.fallback}</>;
			return (
				<div className="w-full h-full p-6 flex items-center justify-center">
					<div className="max-w-md w-full bg-white rounded-xl shadow border border-gray-200 p-6 text-center">
						<h2 className="text-lg font-semibold text-gray-900 mb-2">{this.props.title || 'Something went wrong'}</h2>
						<p className="text-sm text-gray-700 mb-4">{this.state.error?.message || 'An unexpected error occurred.'}</p>
						<button
							className="bg-blue-600 text-white px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							onClick={this.handleReset}
						>
							Try Again
						</button>
					</div>
				</div>
			);
		}

		// Remount children on reset by changing key
		return <div key={this.state.resetKey}>{this.props.children}</div>;
	}
}

export default ErrorBoundary;


