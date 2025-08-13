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

// Provide minimal Web Audio API polyfill for tests that expect support
if (typeof (global as any).window === 'undefined') {
  (global as any).window = {} as any;
}

(global as any).window.AudioContext = (global as any).window.AudioContext || (function() {
  return function MockAudioContext(this: any) {
    this.createOscillator = jest.fn(() => ({
      frequency: { setValueAtTime: jest.fn(), exponentialRampToValueAtTime: jest.fn(), linearRampToValueAtTime: jest.fn() },
      start: jest.fn(),
      stop: jest.fn(),
      connect: jest.fn(),
    }));
    this.createGain = jest.fn(() => ({
      gain: { setValueAtTime: jest.fn(), linearRampToValueAtTime: jest.fn(), exponentialRampToValueAtTime: jest.fn() },
      connect: jest.fn(),
    }));
    this.currentTime = 0;
    this.state = 'running';
    this.resume = jest.fn();
    this.destination = {};
  } as any;
})();

// Ensure document.visibilityState exists and is visible by default
Object.defineProperty(document, 'visibilityState', {
  value: 'visible',
  configurable: true,
});

// In case any test imports canPlayAudio before it's mocked, ensure Audio is defined
if (!(global as any).Audio) {
  (global as any).Audio = function() { return { play: jest.fn(), volume: 0, src: '' }; } as any;
}



