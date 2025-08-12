import '@testing-library/jest-dom';
import React from 'react';
import { render } from '@testing-library/react';
import { ToastProvider } from './src/components/ui/toast';

// Helper for tests to import when needed; avoids global override pitfalls
export function renderWithProviders(ui: React.ReactElement, options?: any) {
  return render(React.createElement(ToastProvider, null, ui), options);
}

// Ensure global.fetch exists for tests that spy on it
if (!(global as any).fetch) {
  (global as any).fetch = jest.fn();
}

// Polyfill ResizeObserver for libraries like Recharts in jsdom
if (typeof (global as any).ResizeObserver === 'undefined') {
  (global as any).ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as any;
}



